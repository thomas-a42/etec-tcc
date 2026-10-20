"""Páginas públicas: home, busca, detalhe do anúncio e a API do feed."""
from flask import Blueprint, abort, g, jsonify, render_template, request

import config
from db import query

bp = Blueprint("public", __name__)

STATUS_PUBLICOS = ("disponivel", "reservado")


def _int(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


# ---------- 3. Home ----------
@bp.route("/")
def home():
    return render_template("home.html")


# ---------- 4. Busca ----------
@bp.route("/busca")
def busca():
    especies = [r["especie"] for r in query(
        "SELECT DISTINCT especie FROM anuncios WHERE status = ANY(%s) ORDER BY 1",
        (list(STATUS_PUBLICOS),))]
    racas = [r["raca"] for r in query(
        "SELECT DISTINCT raca FROM anuncios WHERE raca IS NOT NULL AND status = ANY(%s) ORDER BY 1",
        (list(STATUS_PUBLICOS),))]
    return render_template("busca.html", especies=especies, racas=racas)


# ---------- Feed (home + busca usam este endpoint) ----------
@bp.route("/api/anuncios")
def api_anuncios():
    a = request.args
    where = ["o.status_verificacao = 'verificada'"]
    params = []

    status = a.get("status", "disponivel")
    if status not in STATUS_PUBLICOS:
        status = "disponivel"
    where.append("an.status = %s")
    params.append(status)

    def like(coluna, chave):
        valor = a.get(chave, "").strip()
        if valor:
            where.append(f"{coluna} ILIKE %s")
            params.append(f"%{valor}%")

    like("an.nome_animal", "q")
    like("an.raca", "raca")
    like("o.cidade", "cidade")

    especie = a.get("especie", "").strip()
    if especie:
        where.append("lower(an.especie) = lower(%s)")
        params.append(especie)
    if a.get("sexo") in ("macho", "femea", "desconhecido"):
        where.append("an.sexo = %s")
        params.append(a["sexo"])
    if a.get("porte") in ("pequeno", "medio", "grande"):
        where.append("an.porte = %s")
        params.append(a["porte"])
    if len(a.get("estado", "")) == 2:
        where.append("o.estado = %s")
        params.append(a["estado"].upper())
    if _int(a.get("idade_min")) is not None:
        where.append("an.idade >= %s")
        params.append(_int(a["idade_min"]))
    if _int(a.get("idade_max")) is not None:
        where.append("an.idade <= %s")
        params.append(_int(a["idade_max"]))
    if a.get("vacinado"):
        where.append("an.vacinado")
    if a.get("castrado"):
        where.append("an.castrado")

    offset = max(0, _int(a.get("offset")) or 0)
    limit = config.PAGE_SIZE

    rows = query(
        f"""SELECT an.id, an.nome_animal, an.especie, an.raca, an.sexo, an.idade,
                   an.porte, an.vacinado, an.castrado, an.status, an.data_publicacao,
                   o.nome AS ong_nome, o.cidade, o.estado,
                   (SELECT i.url FROM imagens_anuncios i WHERE i.anuncio_id = an.id
                     ORDER BY i.principal DESC, i.ordem, i.data_upload LIMIT 1) AS imagem
              FROM anuncios an
              JOIN ongs o ON o.id = an.ong_id
             WHERE {' AND '.join(where)}
             ORDER BY an.data_publicacao DESC, an.id DESC
             LIMIT %s OFFSET %s""",
        params + [limit + 1, offset],
    )
    return jsonify(items=rows[:limit], has_more=len(rows) > limit)


# ---------- Detalhe do anúncio ----------
@bp.route("/anuncio/<uuid:anuncio_id>")
def anuncio(anuncio_id):
    a = query(
        """SELECT an.*, o.nome AS ong_nome, o.cidade, o.estado, o.telefone AS ong_telefone,
                  o.descricao AS ong_descricao, o.status_verificacao
             FROM anuncios an JOIN ongs o ON o.id = an.ong_id
            WHERE an.id = %s""",
        (anuncio_id,), one=True,
    )
    if not a:
        abort(404)

    actor = g.actor
    dono = bool(actor) and actor["role"] == "ong" and actor["id"] == str(a["ong_id"])
    admin = bool(actor) and actor["role"] == "admin"
    visivel = a["status"] != "inativo" and a["status_verificacao"] == "verificada"
    if not (visivel or dono or admin):
        abort(404)

    imagens = query(
        """SELECT id, url, principal FROM imagens_anuncios
            WHERE anuncio_id = %s ORDER BY principal DESC, ordem, data_upload""",
        (anuncio_id,),
    )
    chat_existente = None
    if actor and actor["role"] == "user":
        chat_existente = query(
            "SELECT id FROM chat WHERE anuncio_id = %s AND user_id = %s ORDER BY data_criacao LIMIT 1",
            (anuncio_id, actor["id"]), one=True,
        )
    return render_template("anuncio.html", a=a, imagens=imagens, dono=dono,
                           chat_existente=chat_existente)
