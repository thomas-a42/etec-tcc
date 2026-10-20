"""6. Dashboard da ONG: anúncios (CRUD) + mensagens."""
import os
import uuid

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

import config
from db import execute, query, tx
from security import require, safe_next

bp = Blueprint("ong", __name__, url_prefix="/ong")

SEXOS = ("macho", "femea", "desconhecido")
PORTES = ("pequeno", "medio", "grande")
STATUS = ("disponivel", "reservado", "adotado", "inativo")


# ---------- helpers ----------
def _anuncio_da_ong(anuncio_id):
    a = query("SELECT * FROM anuncios WHERE id = %s AND ong_id = %s",
              (anuncio_id, g.actor["id"]), one=True)
    if not a:
        abort(404)
    return a


def _parse_form():
    f = request.form
    dados = {
        "nome_animal": f.get("nome_animal", "").strip(),
        "especie": f.get("especie", "").strip().lower(),
        "raca": f.get("raca", "").strip() or None,
        "sexo": f.get("sexo") or None,
        "porte": f.get("porte") or None,
        "descricao": f.get("descricao", "").strip(),
        "vacinado": bool(f.get("vacinado")),
        "castrado": bool(f.get("castrado")),
        "idade": None,
    }
    erro = None
    idade = f.get("idade", "").strip()
    if idade:
        try:
            dados["idade"] = int(idade)
            if dados["idade"] < 0:
                raise ValueError
        except ValueError:
            erro = "Idade inválida."
    if not dados["nome_animal"] or not dados["especie"] or not dados["descricao"]:
        erro = "Nome, espécie e descrição são obrigatórios."
    if len(dados["especie"]) > 30:
        erro = "Espécie muito longa (máx. 30 caracteres)."
    if dados["sexo"] not in (None, *SEXOS) or dados["porte"] not in (None, *PORTES):
        erro = "Sexo ou porte inválido."
    return dados, erro


def _save_images(anuncio_id, arquivos):
    arquivos = [f for f in arquivos if f and f.filename]
    info = query(
        "SELECT count(*) AS n, COALESCE(bool_or(principal), FALSE) AS tem "
        "FROM imagens_anuncios WHERE anuncio_id = %s",
        (anuncio_id,), one=True,
    )
    n, tem_principal = info["n"], info["tem"]
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    salvas = 0
    for f in arquivos:
        if n >= config.MAX_IMAGENS:
            break
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in config.ALLOWED_IMG:
            continue
        nome = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(config.UPLOAD_DIR, nome))
        execute(
            "INSERT INTO imagens_anuncios (anuncio_id, url, principal, ordem) VALUES (%s, %s, %s, %s)",
            (anuncio_id, config.UPLOAD_URL_PREFIX + nome, not tem_principal, n),
        )
        tem_principal = True
        n += 1
        salvas += 1
    return salvas


def _apagar_arquivo(url):
    if url.startswith(config.UPLOAD_URL_PREFIX):
        caminho = os.path.join(config.UPLOAD_DIR, os.path.basename(url))
        try:
            os.remove(caminho)
        except OSError:
            pass


# ---------- dashboard ----------
@bp.route("/")
@require("ong")
def dashboard():
    aba = request.args.get("aba", "anuncios")
    if aba not in ("anuncios", "mensagens"):
        aba = "anuncios"
    anuncios = []
    if aba == "anuncios":
        anuncios = query(
            """SELECT a.id, a.nome_animal, a.especie, a.status, a.data_publicacao,
                      (SELECT count(*) FROM chat c WHERE c.anuncio_id = a.id) AS conversas,
                      (SELECT url FROM imagens_anuncios i WHERE i.anuncio_id = a.id
                        ORDER BY i.principal DESC, i.ordem LIMIT 1) AS imagem
                 FROM anuncios a WHERE a.ong_id = %s
                ORDER BY a.data_publicacao DESC""",
            (g.actor["id"],),
        )
    return render_template("ong_dashboard.html", aba=aba, anuncios=anuncios,
                           status_opcoes=STATUS, selected=request.args.get("c", ""))


# ---------- criar / editar anúncio ----------
@bp.route("/anuncios/novo", methods=["GET", "POST"])
@require("ong")
def novo():
    if not g.actor["verificada"]:
        flash("Sua ONG ainda não foi verificada. Você poderá publicar assim que um admin aprovar.", "erro")
        return redirect(url_for("ong.dashboard"))
    dados = {}
    if request.method == "POST":
        dados, erro = _parse_form()
        if erro:
            flash(erro, "erro")
        else:
            row = execute(
                """INSERT INTO anuncios (ong_id, nome_animal, especie, raca, sexo, idade,
                                         porte, descricao, vacinado, castrado)
                   VALUES (%(ong)s, %(nome_animal)s, %(especie)s, %(raca)s, %(sexo)s, %(idade)s,
                           %(porte)s, %(descricao)s, %(vacinado)s, %(castrado)s) RETURNING id""",
                {**dados, "ong": g.actor["id"]},
            )
            _save_images(row["id"], request.files.getlist("imagens"))
            flash("Anúncio publicado!", "ok")
            return redirect(url_for("ong.dashboard"))
    return render_template("anuncio_form.html", a=dados, imagens=[], modo="novo")


@bp.route("/anuncios/<uuid:anuncio_id>/editar", methods=["GET", "POST"])
@require("ong")
def editar(anuncio_id):
    a = _anuncio_da_ong(anuncio_id)
    if request.method == "POST":
        dados, erro = _parse_form()
        if erro:
            flash(erro, "erro")
            a = {**a, **dados}
        else:
            execute(
                """UPDATE anuncios SET nome_animal=%(nome_animal)s, especie=%(especie)s,
                          raca=%(raca)s, sexo=%(sexo)s, idade=%(idade)s, porte=%(porte)s,
                          descricao=%(descricao)s, vacinado=%(vacinado)s, castrado=%(castrado)s,
                          data_atualizacao=CURRENT_TIMESTAMP
                    WHERE id=%(id)s""",
                {**dados, "id": anuncio_id},
            )
            _save_images(anuncio_id, request.files.getlist("imagens"))
            flash("Anúncio atualizado.", "ok")
            return redirect(url_for("ong.editar", anuncio_id=anuncio_id))
    imagens = query(
        "SELECT id, url, principal FROM imagens_anuncios WHERE anuncio_id = %s "
        "ORDER BY principal DESC, ordem, data_upload", (anuncio_id,))
    return render_template("anuncio_form.html", a=a, imagens=imagens, modo="editar")


@bp.route("/anuncios/<uuid:anuncio_id>/status", methods=["POST"])
@require("ong")
def status(anuncio_id):
    _anuncio_da_ong(anuncio_id)
    valor = request.form.get("valor")
    if valor not in STATUS:
        abort(400)
    execute("UPDATE anuncios SET status=%s, data_atualizacao=CURRENT_TIMESTAMP WHERE id=%s",
            (valor, anuncio_id))
    flash("Status atualizado.", "ok")
    return redirect(safe_next(request.form.get("voltar")) or url_for("ong.dashboard"))


# ---------- imagens ----------
def _imagem_da_ong(imagem_id):
    img = query(
        """SELECT i.id, i.url, i.principal, i.anuncio_id
             FROM imagens_anuncios i JOIN anuncios a ON a.id = i.anuncio_id
            WHERE i.id = %s AND a.ong_id = %s""",
        (imagem_id, g.actor["id"]), one=True,
    )
    if not img:
        abort(404)
    return img


@bp.route("/imagens/<uuid:imagem_id>/remover", methods=["POST"])
@require("ong")
def remover_imagem(imagem_id):
    img = _imagem_da_ong(imagem_id)
    with tx() as cur:
        cur.execute("DELETE FROM imagens_anuncios WHERE id = %s", (imagem_id,))
        if img["principal"]:  # promove a próxima imagem
            cur.execute(
                """UPDATE imagens_anuncios SET principal = TRUE
                    WHERE id = (SELECT id FROM imagens_anuncios WHERE anuncio_id = %s
                                 ORDER BY ordem, data_upload LIMIT 1)""",
                (img["anuncio_id"],),
            )
    _apagar_arquivo(img["url"])
    return redirect(url_for("ong.editar", anuncio_id=img["anuncio_id"]))


@bp.route("/imagens/<uuid:imagem_id>/principal", methods=["POST"])
@require("ong")
def imagem_principal(imagem_id):
    img = _imagem_da_ong(imagem_id)
    with tx() as cur:
        cur.execute("UPDATE imagens_anuncios SET principal = FALSE "
                    "WHERE anuncio_id = %s AND principal", (img["anuncio_id"],))
        cur.execute("UPDATE imagens_anuncios SET principal = TRUE WHERE id = %s", (imagem_id,))
    return redirect(url_for("ong.editar", anuncio_id=img["anuncio_id"]))
