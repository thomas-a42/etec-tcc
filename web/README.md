# Adoção Animal — protótipo (Flask + PostgreSQL)

## Rodando

```bash
# 1. banco (PostgreSQL local, versão 13+ por causa do gen_random_uuid)
createdb adocao
psql -d adocao -f schema.sql

# 2. dependências
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# 3. conexão (ajuste usuário/senha/porta se precisar)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/adocao"
export SECRET_KEY="uma-chave-qualquer"

# 4. dados de exemplo (opcional) e execução
python seed.py
python app.py            # http://127.0.0.1:5000
```

Contas de exemplo (criadas pelo `seed.py`):

| Papel   | E-mail             | Senha    | Entrar em        |
|---------|--------------------|----------|------------------|
| Usuário | user@adocao.local  | user123  | `/login`         |
| ONG     | ong@adocao.local   | ong123   | `/painel/login`  |
| Admin   | admin@adocao.local | admin123 | `/painel/login`  |

Só criar um admin: `python seed.py admin EMAIL SENHA "Nome"`.

## Páginas

| # | Página | URL | Template |
|---|--------|-----|----------|
| 1 | Login (usuário) | `/login` (cadastro em `/cadastro`) | `login_user.html` |
| 2 | Login (ONG/admin) | `/painel/login` (cadastro de ONG em `/painel/cadastro`) | `login_staff.html` |
| 3 | Home (feed infinito) | `/` | `home.html` |
| 4 | Busca com filtros | `/busca` | `busca.html` |
| 5 | Chat do usuário | `/chat` | `chat.html` |
| 6 | Dashboard da ONG | `/ong/` | `ong_dashboard.html`, `anuncio_form.html` |
| 7 | Painel admin | `/admin/` | `admin.html`, `admin_chat.html` |
| – | Detalhe do anúncio | `/anuncio/<id>` | `anuncio.html` |

## Estrutura

```
app.py            cria o app, filtros Jinja
config.py         DATABASE_URL, SECRET_KEY, limites de upload, tamanho da página
db.py             pool de conexões + query()/execute()/tx()
security.py       sessão, papéis e @require(...)
routes/           um arquivo por área (auth, public, chat, ong, admin)
templates/        base.html + uma página por arquivo (partials/ = pedaços reutilizados)
static/css/       tokens.css (cores/fontes) → base.css (reset, forms, botões) → components.css
static/js/        common.js (utilitários), feed.js, chat.js, anuncio.js, admin.js
```

### Para quem for mexer no front-end
- Cores, fontes, espaçamentos e raios ficam todos em `static/css/tokens.css`.
- `components.css` tem um bloco por componente (navbar, card, tabela, chat…), nomes no padrão BEM (`.card__titulo`, `.badge--reservado`).
- O HTML do card de animal do feed está em `cardAnimal()` no `static/js/common.js`.
- Os dados vêm de JSON (`/api/anuncios`, `/api/chats`), então o visual pode ser trocado sem mexer no Python.

## Decisões e limitações do protótipo
- **Idade** é tratada como anos (o schema só diz INTEGER).
- Só aparecem no site anúncios de **ONGs verificadas** e com status `disponivel`/`reservado`. ONG nova fica `pendente` até um admin aprovar na aba ONGs; ONG `rejeitada` não consegue entrar.
- Anúncios não são apagados (as FKs são RESTRICT): a ONG usa o status `inativo`.
- Uma conversa por par (anúncio, usuário), criada em "Tenho interesse em adotar".
- O chat atualiza por polling a cada 4 s (sem websockets).
- Fotos enviadas ficam em `static/uploads/` e a URL vai para `imagens_anuncios.url`.
- Paginação do feed por offset: se alguém publicar durante a rolagem, um card pode repetir/pular.
- Faltam para produção: proteção CSRF, rate limit no login, recuperação de senha, servidor WSGI (gunicorn) atrás de nginx.
