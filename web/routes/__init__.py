from . import admin, auth, chat, ong, public


def register_routes(app):
    for modulo in (auth, public, chat, ong, admin):
        app.register_blueprint(modulo.bp)
