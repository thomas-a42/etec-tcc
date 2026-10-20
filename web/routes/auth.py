"""Login, cadastro e logout."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from psycopg2 import errors
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, query
from security import login_session, safe_next

bp = Blueprint("auth", __name__)


# ---------- 1. Login (usuário) ----------
@bp.route("/login", methods=["GET", "POST"])
def login_user():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        u = query(
            "SELECT id, senha_hash, status FROM users WHERE lower(email) = %s",
            (email,), one=True,
        )
        if not u or not check_password_hash(u["senha_hash"], senha):
            flash("E-mail ou senha incorretos.", "erro")
        elif u["status"] != "ativo":
            flash("Esta conta está suspensa.", "erro")
        else:
            login_session("user", u["id"])
            return redirect(safe_next(request.args.get("next")) or url_for("public.home"))
    return render_template("login_user.html")


@bp.route("/cadastro", methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        f = request.form
        nome, email = f.get("nome", "").strip(), f.get("email", "").strip().lower()
        senha, telefone = f.get("senha", ""), f.get("telefone", "").strip() or None
        if not nome or not email or len(senha) < 6:
            flash("Preencha nome, e-mail e uma senha com pelo menos 6 caracteres.", "erro")
        else:
            try:
                row = execute(
                    "INSERT INTO users (nome, email, senha_hash, telefone) "
                    "VALUES (%s, %s, %s, %s) RETURNING id",
                    (nome, email, generate_password_hash(senha), telefone),
                )
                login_session("user", row["id"])
                flash("Conta criada! Bem-vindo(a).", "ok")
                return redirect(url_for("public.home"))
            except errors.UniqueViolation:
                flash("Já existe uma conta com esse e-mail.", "erro")
    return render_template("register.html", tipo="user")


# ---------- 2. Login (ONGs / Admins) ----------
@bp.route("/painel/login", methods=["GET", "POST"])
def login_staff():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        admin = query(
            "SELECT id, senha_hash, status FROM admins WHERE lower(email) = %s",
            (email,), one=True,
        )
        if admin and check_password_hash(admin["senha_hash"], senha):
            if admin["status"] != "ativo":
                flash("Esta conta está suspensa.", "erro")
            else:
                login_session("admin", admin["id"])
                return redirect(safe_next(request.args.get("next")) or url_for("admin.painel"))
            return render_template("login_staff.html")

        ong = query(
            "SELECT id, senha_hash, status_verificacao FROM ongs WHERE lower(email) = %s",
            (email,), one=True,
        )
        if ong and check_password_hash(ong["senha_hash"], senha):
            if ong["status_verificacao"] == "rejeitada":
                flash("O cadastro desta ONG foi rejeitado.", "erro")
            else:
                login_session("ong", ong["id"])
                return redirect(safe_next(request.args.get("next")) or url_for("ong.dashboard"))
            return render_template("login_staff.html")

        flash("E-mail ou senha incorretos.", "erro")
    return render_template("login_staff.html")


@bp.route("/painel/cadastro", methods=["GET", "POST"])
def register_ong():
    dados = {}
    if request.method == "POST":
        f = request.form
        dados = {k: f.get(k, "").strip() for k in
                 ("nome", "email", "cnpj", "telefone", "cidade", "estado", "endereco", "descricao")}
        dados["email"] = dados["email"].lower()
        dados["estado"] = dados["estado"].upper()
        senha = f.get("senha", "")
        if not dados["nome"] or not dados["email"] or not dados["cidade"] or len(dados["estado"]) != 2:
            flash("Preencha nome, e-mail, cidade e estado (2 letras).", "erro")
        elif len(senha) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "erro")
        else:
            try:
                row = execute(
                    """INSERT INTO ongs (nome, email, senha_hash, cnpj, telefone,
                                         descricao, cidade, estado, endereco)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (dados["nome"], dados["email"], generate_password_hash(senha),
                     dados["cnpj"] or None, dados["telefone"] or None,
                     dados["descricao"] or None, dados["cidade"], dados["estado"],
                     dados["endereco"] or None),
                )
                login_session("ong", row["id"])
                flash("ONG cadastrada! Aguarde a verificação para publicar anúncios.", "ok")
                return redirect(url_for("ong.dashboard"))
            except errors.UniqueViolation:
                flash("E-mail ou CNPJ já cadastrado.", "erro")
            except errors.CheckViolation:
                flash("Dados inválidos (confira o estado, ex.: SP).", "erro")
    return render_template("register.html", tipo="ong", dados=dados)


@bp.route("/sair")
def logout():
    session.clear()
    return redirect(url_for("public.home"))
