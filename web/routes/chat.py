"""Chat entre usuários e ONGs (página do usuário + API JSON usada também pela ONG)."""
from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for

from db import execute, query, tx
from security import require

bp = Blueprint("chat", __name__)

MAX_MSG = 2000


def _chat_row(chat_id):
    return query(
        """SELECT c.id, c.status, c.user_id, c.anuncio_id, a.ong_id, a.nome_animal,
                  u.nome AS user_nome, o.nome AS ong_nome
             FROM chat c
             JOIN anuncios a ON a.id = c.anuncio_id
             JOIN users u ON u.id = c.user_id
             JOIN ongs o ON o.id = a.ong_id
            WHERE c.id = %s""",
        (chat_id,), one=True,
    )


def _can_access(c):
    role, aid = g.actor["role"], g.actor["id"]
    if role == "admin":
        return True
    if role == "user":
        return str(c["user_id"]) == aid
    return str(c["ong_id"]) == aid


# ---------- 5. Chat do usuário ----------
@bp.route("/chat")
@require("user")
def pagina():
    return render_template("chat.html", selected=request.args.get("c", ""))


@bp.route("/anuncio/<uuid:anuncio_id>/conversar", methods=["POST"])
@require("user")
def conversar(anuncio_id):
    a = query(
        """SELECT an.id, an.status, o.status_verificacao
             FROM anuncios an JOIN ongs o ON o.id = an.ong_id WHERE an.id = %s""",
        (anuncio_id,), one=True,
    )
    if not a or a["status"] not in ("disponivel", "reservado") or a["status_verificacao"] != "verificada":
        abort(404)

    existente = query(
        "SELECT id FROM chat WHERE anuncio_id = %s AND user_id = %s ORDER BY data_criacao LIMIT 1",
        (anuncio_id, g.actor["id"]), one=True,
    )
    if existente:
        chat_id = existente["id"]
    else:
        chat_id = execute(
            "INSERT INTO chat (anuncio_id, user_id) VALUES (%s, %s) RETURNING id",
            (anuncio_id, g.actor["id"]),
        )["id"]
    return redirect(url_for("chat.pagina", c=chat_id))


# ---------- API ----------
@bp.route("/api/chats")
@require("user", "ong")
def api_chats():
    role = g.actor["role"]
    if role == "user":
        contraparte, filtro, lado_outro = "o.nome", "c.user_id = %s", "m.remetente_ong_id IS NOT NULL"
    else:
        contraparte, filtro, lado_outro = "u.nome", "a.ong_id = %s", "m.remetente_user_id IS NOT NULL"

    rows = query(
        f"""SELECT c.id, c.status, a.id AS anuncio_id, a.nome_animal,
                   {contraparte} AS contraparte,
                   COALESCE(c.data_ultima_mensagem, c.data_criacao) AS atividade,
                   (SELECT m.conteudo FROM mensagens m WHERE m.chat_id = c.id
                     ORDER BY m.data_envio DESC LIMIT 1) AS ultima,
                   (SELECT count(*) FROM mensagens m WHERE m.chat_id = c.id
                       AND m.lida_em IS NULL AND {lado_outro}) AS nao_lidas
              FROM chat c
              JOIN anuncios a ON a.id = c.anuncio_id
              JOIN users u ON u.id = c.user_id
              JOIN ongs o ON o.id = a.ong_id
             WHERE {filtro}
             ORDER BY atividade DESC""",
        (g.actor["id"],),
    )
    return jsonify(chats=rows)


@bp.route("/api/chats/<uuid:chat_id>/mensagens", methods=["GET", "POST"])
@require("user", "ong", "admin")
def api_mensagens(chat_id):
    c = _chat_row(chat_id)
    if not c or not _can_access(c):
        return jsonify(erro="Conversa não encontrada"), 404
    role = g.actor["role"]

    if request.method == "POST":
        if role == "admin":
            return jsonify(erro="Admins só visualizam conversas"), 403
        if c["status"] != "aberto":
            return jsonify(erro="Esta conversa não aceita novas mensagens"), 409
        conteudo = ((request.get_json(silent=True) or {}).get("conteudo") or "").strip()
        if not conteudo or len(conteudo) > MAX_MSG:
            return jsonify(erro=f"Mensagem vazia ou maior que {MAX_MSG} caracteres"), 400
        user_id = g.actor["id"] if role == "user" else None
        ong_id = g.actor["id"] if role == "ong" else None
        with tx() as cur:
            cur.execute(
                """INSERT INTO mensagens (chat_id, remetente_user_id, remetente_ong_id, conteudo)
                   VALUES (%s, %s, %s, %s)""",
                (chat_id, user_id, ong_id, conteudo),
            )
            cur.execute(
                "UPDATE chat SET data_ultima_mensagem = CURRENT_TIMESTAMP WHERE id = %s",
                (chat_id,),
            )
        return jsonify(ok=True), 201

    # GET: marca como lidas as mensagens do outro lado
    if role in ("user", "ong"):
        outro = "remetente_ong_id IS NOT NULL" if role == "user" else "remetente_user_id IS NOT NULL"
        execute(
            f"UPDATE mensagens SET lida_em = CURRENT_TIMESTAMP "
            f"WHERE chat_id = %s AND lida_em IS NULL AND {outro}",
            (chat_id,),
        )

    msgs = query(
        """SELECT id, conteudo, data_envio, lida_em, (remetente_user_id IS NOT NULL) AS de_user
             FROM mensagens WHERE chat_id = %s ORDER BY data_envio, id""",
        (chat_id,),
    )
    saida = [{
        "id": m["id"],
        "conteudo": m["conteudo"],
        "data_envio": m["data_envio"],
        "lida": m["lida_em"] is not None,
        "autor": c["user_nome"] if m["de_user"] else c["ong_nome"],
        "minha": (role == "user" and m["de_user"]) or (role == "ong" and not m["de_user"]),
    } for m in msgs]
    contraparte = c["ong_nome"] if role == "user" else c["user_nome"]
    return jsonify(
        chat={"id": c["id"], "status": c["status"], "nome_animal": c["nome_animal"],
              "anuncio_id": c["anuncio_id"], "contraparte": contraparte},
        mensagens=saida,
    )
