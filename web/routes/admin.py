"""7. Painel administrativo: moderação de usuários, ONGs, anúncios e chats."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from db import execute, query
from security import require, safe_next

bp = Blueprint("admin", __name__, url_prefix="/admin")

ABAS = ("usuarios", "ongs", "anuncios", "chats")


@bp.route("/")
@require("admin")
def painel():
    aba = request.args.get("aba", "usuarios")
    if aba not in ABAS:
        aba = "usuarios"
    q = request.args.get("q", "").strip()
    like = f"%{q}%"

    if aba == "usuarios":
        rows = query(
            """SELECT id, nome, email, telefone, status, data_cadastro FROM users
                WHERE nome ILIKE %s OR email ILIKE %s
                ORDER BY data_cadastro DESC LIMIT 200""", (like, like))
    elif aba == "ongs":
        rows = query(
            """SELECT id, nome, email, cnpj, cidade, estado, status_verificacao, data_cadastro
                 FROM ongs WHERE nome ILIKE %s OR email ILIKE %s OR cidade ILIKE %s
                ORDER BY (status_verificacao = 'pendente') DESC, data_cadastro DESC LIMIT 200""",
            (like, like, like))
    elif aba == "anuncios":
        rows = query(
            """SELECT an.id, an.nome_animal, an.especie, an.status, an.data_publicacao,
                      o.nome AS ong_nome
                 FROM anuncios an JOIN ongs o ON o.id = an.ong_id
                WHERE an.nome_animal ILIKE %s OR o.nome ILIKE %s
                ORDER BY an.data_publicacao DESC LIMIT 200""", (like, like))
    else:
        rows = query(
            """SELECT c.id, c.status, c.data_criacao, c.data_ultima_mensagem,
                      a.nome_animal, u.nome AS user_nome, o.nome AS ong_nome,
                      (SELECT count(*) FROM mensagens m WHERE m.chat_id = c.id) AS total
                 FROM chat c
                 JOIN anuncios a ON a.id = c.anuncio_id
                 JOIN users u ON u.id = c.user_id
                 JOIN ongs o ON o.id = a.ong_id
                WHERE a.nome_animal ILIKE %s OR u.nome ILIKE %s OR o.nome ILIKE %s
                ORDER BY COALESCE(c.data_ultima_mensagem, c.data_criacao) DESC LIMIT 200""",
            (like, like, like))

    pendentes = query("SELECT count(*) AS n FROM ongs WHERE status_verificacao = 'pendente'",
                      one=True)["n"]
    return render_template("admin.html", aba=aba, rows=rows, q=q, pendentes=pendentes)


@bp.route("/chats/<uuid:chat_id>")
@require("admin")
def chat_ver(chat_id):
    c = query(
        """SELECT c.id, c.status, c.data_criacao, a.id AS anuncio_id, a.nome_animal,
                  u.nome AS user_nome, u.email AS user_email, o.nome AS ong_nome
             FROM chat c
             JOIN anuncios a ON a.id = c.anuncio_id
             JOIN users u ON u.id = c.user_id
             JOIN ongs o ON o.id = a.ong_id
            WHERE c.id = %s""", (chat_id,), one=True)
    if not c:
        abort(404)
    msgs = query(
        """SELECT conteudo, data_envio, (remetente_user_id IS NOT NULL) AS de_user
             FROM mensagens WHERE chat_id = %s ORDER BY data_envio, id""", (chat_id,))
    return render_template("admin_chat.html", c=c, msgs=msgs)


# ---------- ações de moderação ----------
def _alterar(tabela, coluna, item_id, permitidos):
    valor = request.form.get("valor")
    if valor not in permitidos:
        abort(400)
    execute(f"UPDATE {tabela} SET {coluna} = %s WHERE id = %s", (valor, item_id))
    flash("Alteração salva.", "ok")


def _voltar(aba):
    return redirect(safe_next(request.form.get("voltar")) or url_for("admin.painel", aba=aba))


@bp.route("/usuarios/<uuid:item_id>/status", methods=["POST"])
@require("admin")
def usuario_status(item_id):
    _alterar("users", "status", item_id, ("ativo", "suspenso"))
    return _voltar("usuarios")


@bp.route("/ongs/<uuid:item_id>/verificacao", methods=["POST"])
@require("admin")
def ong_verificacao(item_id):
    _alterar("ongs", "status_verificacao", item_id, ("pendente", "verificada", "rejeitada"))
    return _voltar("ongs")


@bp.route("/anuncios/<uuid:item_id>/status", methods=["POST"])
@require("admin")
def anuncio_status(item_id):
    _alterar("anuncios", "status", item_id, ("disponivel", "reservado", "adotado", "inativo"))
    return _voltar("anuncios")


@bp.route("/chats/<uuid:item_id>/status", methods=["POST"])
@require("admin")
def chat_status(item_id):
    _alterar("chat", "status", item_id, ("aberto", "encerrado", "bloqueado"))
    return _voltar("chats")
