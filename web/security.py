"""Autenticação por JWT, papéis (user / ong / admin) e decorator de proteção de rotas.

O token é um JWT assinado (HS256) com sub (id), role, iat, exp e iss.
Ele viaja num cookie HttpOnly (o front-end não muda) ou, para clientes de API,
no cabeçalho `Authorization: Bearer <token>`. A cada request o usuário é
recarregado do banco, então conta suspensa/removida perde acesso na hora.
"""
import time
from functools import wraps

import jwt
from flask import flash, g, jsonify, redirect, request, url_for

import config
from db import query

ROLES = ("user", "ong", "admin")


def create_token(role, actor_id):
    now = int(time.time())
    payload = {
        "sub": str(actor_id),
        "role": role,
        "iat": now,
        "exp": now + config.JWT_EXPIRES_MIN * 60,
        "iss": config.JWT_ISSUER,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token):
    """Devolve os claims ou None se o token for inválido/expirado."""
    try:
        return jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],  # nunca aceitar "none"
            issuer=config.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "role"]},
        )
    except jwt.InvalidTokenError:
        return None


def _read_token():
    """(token, veio_do_cookie). Cabeçalho Bearer tem prioridade sobre o cookie."""
    auth = request.headers.get("Authorization", "")
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip(), False
    return request.cookies.get(config.JWT_COOKIE_NAME), True


def _set_cookie(response, token):
    response.set_cookie(
        config.JWT_COOKIE_NAME, token,
        max_age=config.JWT_EXPIRES_MIN * 60,
        httponly=True, samesite="Lax", secure=config.JWT_COOKIE_SECURE, path="/",
    )


def _clear_cookie(response):
    response.delete_cookie(config.JWT_COOKIE_NAME, path="/",
                           httponly=True, samesite="Lax", secure=config.JWT_COOKIE_SECURE)


def apply_token_cookie(response):
    """after_request: grava/renova/remove o cookie do JWT conforme o que ocorreu no request."""
    if g.get("clear_token"):
        _clear_cookie(response)
    elif g.get("new_token"):
        _set_cookie(response, g.new_token)
    elif g.get("actor") and g.get("token_from_cookie") and g.get("token_claims"):
        # renovação deslizante: passou da metade da validade -> emite um token novo
        restante = g.token_claims["exp"] - time.time()
        if restante < config.JWT_EXPIRES_MIN * 30:
            _set_cookie(response, create_token(g.actor["role"], g.actor["id"]))
    elif g.get("token_invalid"):
        _clear_cookie(response)
    return response


def load_actor():
    """Roda antes de cada request: carrega quem está logado em g.actor."""
    g.actor = None
    if request.endpoint == "static":
        return
    token, from_cookie = _read_token()
    if not token:
        return
    claims = decode_token(token)
    if not claims:
        g.token_invalid = True
        return
    role, aid = claims["role"], claims["sub"]
    if role not in ROLES or not aid:
        g.token_invalid = True
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

    if not ok:  # conta removida, suspensa ou rejeitada -> derruba o acesso
        g.clear_token = True
        return

    g.token_claims = claims
    g.token_from_cookie = from_cookie

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
    """Emite o JWT; o cookie é gravado em apply_token_cookie (after_request)."""
    g.new_token = create_token(role, actor_id)
    g.clear_token = False


def logout_session():
    g.new_token = None
    g.clear_token = True


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
