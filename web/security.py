"""Sessão, papéis (user / ong / admin) e decorator de proteção de rotas."""
from functools import wraps

from flask import flash, g, jsonify, redirect, request, session, url_for

from db import query

ROLES = ("user", "ong", "admin")


def load_actor():
    """Roda antes de cada request: carrega quem está logado em g.actor."""
    g.actor = None
    if request.endpoint == "static":
        return
    role, aid = session.get("role"), session.get("id")
    if role not in ROLES or not aid:
        return

    if role == "ong":
        row = query(
            "SELECT id, nome, email, status_verificacao FROM ongs WHERE id = %s",
            (aid,), one=True,
        )
        ok = bool(row) and row["status_verificacao"] != "rejeitada"
    else:
        tabela = "users" if role == "user" else "admins"
        row = query(
            f"SELECT id, nome, email, status FROM {tabela} WHERE id = %s",
            (aid,), one=True,
        )
        ok = bool(row) and row["status"] == "ativo"

    if not ok:  # conta removida, suspensa ou rejeitada -> derruba a sessão
        session.clear()
        return

    g.actor = {
        "role": role,
        "id": str(row["id"]),
        "nome": row["nome"],
        "email": row["email"],
        "verificada": role == "ong" and row["status_verificacao"] == "verificada",
    }


def safe_next(url):
    """Só aceita redirecionamento para caminhos internos."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return None


def login_session(role, actor_id):
    session.clear()
    session["role"] = role
    session["id"] = str(actor_id)


def require(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.actor is None or g.actor["role"] not in roles:
                if request.path.startswith("/api/"):
                    return jsonify(erro="Não autorizado"), 401
                flash("Faça login para continuar.", "erro")
                destino = "auth.login_user" if "user" in roles else "auth.login_staff"
                nxt = request.full_path.rstrip("?") if request.method == "GET" else None
                return redirect(url_for(destino, next=nxt))
            return view(*args, **kwargs)
        return wrapper
    return decorator
