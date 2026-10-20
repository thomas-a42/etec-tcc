"""Configurações do projeto. Tudo pode ser sobrescrito por variáveis de ambiente."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Conexão com o PostgreSQL local
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/adocao"
)

# Troque em produção (assina o cookie de sessão)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-troque-esta-chave")

SITE_NOME = "Adoção Animal"
TIMEZONE = "America/Sao_Paulo"

# Feed / busca
PAGE_SIZE = 12

# Upload de imagens dos anúncios
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
UPLOAD_URL_PREFIX = "/static/uploads/"
ALLOWED_IMG = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGENS = 8
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB por requisição
