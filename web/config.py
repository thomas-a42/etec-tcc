"""Configurações do projeto. Tudo pode ser sobrescrito por variáveis de ambiente."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Conexão com o PostgreSQL local
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/adocao"
)

# Troque em produção (assina o cookie de sessão)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-troque-esta-chave")

# JWT (autenticação). Em produção defina JWT_SECRET (>= 32 caracteres aleatórios).
JWT_SECRET = os.environ.get("JWT_SECRET", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "adocao-animal"
JWT_EXPIRES_MIN = int(os.environ.get("JWT_EXPIRES_MIN", "120"))  # validade do token
JWT_COOKIE_NAME = "access_token"
# Ative (=1) quando o site estiver em HTTPS
JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "0") == "1"

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
