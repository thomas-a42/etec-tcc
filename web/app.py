"""Ponto de entrada. Rodar:  python app.py   (ou: flask --app app run)"""
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

from flask import Flask, g, render_template

import config
from routes import register_routes
from security import load_actor

ROTULOS = {
    "macho": "Macho", "femea": "Fêmea", "desconhecido": "Não informado",
    "pequeno": "Pequeno", "medio": "Médio", "grande": "Grande",
    "disponivel": "Disponível", "reservado": "Reservado", "adotado": "Adotado", "inativo": "Inativo",
    "ativo": "Ativo", "suspenso": "Suspenso",
    "pendente": "Pendente", "verificada": "Verificada", "rejeitada": "Rejeitada",
    "aberto": "Aberto", "encerrado": "Encerrado", "bloqueado": "Bloqueado",
}


def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, uuid.UUID):
        return str(o)
    raise TypeError(f"Tipo não serializável: {type(o)}")


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.json.default = _json_default

    app.before_request(load_actor)

    @app.context_processor
    def globais():
        return {"actor": g.get("actor"), "SITE_NOME": config.SITE_NOME}

    @app.template_filter("datahora")
    def datahora(v):
        if not v:
            return "—"
        return v.astimezone(ZoneInfo(config.TIMEZONE)).strftime("%d/%m/%Y %H:%M")

    @app.template_filter("rotulo")
    def rotulo(v):
        return ROTULOS.get(v, v)

    @app.template_filter("idade")
    def idade(v):
        if v is None:
            return "Idade não informada"
        return f"{v} ano" if v == 1 else f"{v} anos"

    register_routes(app)

    @app.errorhandler(404)
    def nao_encontrado(_):
        return render_template("erro.html", titulo="Página não encontrada",
                               msg="O que você procura não existe ou não está mais disponível."), 404

    @app.errorhandler(413)
    def grande_demais(_):
        return render_template("erro.html", titulo="Arquivo muito grande",
                               msg="O envio ultrapassou o limite de 16 MB."), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
