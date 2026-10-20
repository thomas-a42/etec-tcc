"""Dados de exemplo para testar o protótipo.

    python seed.py                        -> cria admin, ONG, usuário e animais de exemplo
    python seed.py admin EMAIL SENHA [NOME] -> cria só um admin

Contas de exemplo (senha entre parênteses):
    admin@adocao.local (admin123) | ong@adocao.local (ong123) | user@adocao.local (user123)
"""
import sys

from werkzeug.security import generate_password_hash

from db import execute, query


def criar_admin(email, senha, nome="Administrador"):
    if query("SELECT 1 FROM admins WHERE email = %s", (email,)):
        print(f"admin {email} já existe")
        return
    execute("INSERT INTO admins (nome, email, senha_hash) VALUES (%s, %s, %s)",
            (nome, email, generate_password_hash(senha)))
    print(f"admin {email} criado")


ANIMAIS = [
    # nome, especie, raca, sexo, idade, porte, vacinado, castrado, descricao
    ("Thor", "cachorro", "Vira-lata", "macho", 3, "medio", True, True, "Dócil, adora brincar de bolinha e se dá bem com crianças."),
    ("Luna", "gato", "Siamês", "femea", 1, "pequeno", True, False, "Curiosa e carinhosa. Procura um lar com janelas protegidas."),
    ("Mel", "cachorro", "Labrador", "femea", 5, "grande", True, True, "Calma, ótima com idosos. Resgatada de maus-tratos."),
    ("Bolinha", "cachorro", "Poodle", "macho", 8, "pequeno", True, True, "Sênior tranquilo, só quer colo e uma caminhada curta."),
    ("Nina", "gato", "Vira-lata", "femea", 2, "pequeno", True, True, "Muito brincalhona, se adapta bem a apartamentos."),
    ("Rex", "cachorro", "Pastor Alemão", "macho", 4, "grande", True, False, "Ativo e inteligente, precisa de espaço e rotina de exercícios."),
    ("Pipoca", "coelho", "Mini Lop", "femea", 1, "pequeno", False, False, "Dócil, gosta de cenoura e de ser acariciada."),
    ("Simba", "gato", "Persa", "macho", 6, "medio", True, True, "Majestoso e tranquilo, ideal para quem busca companhia calma."),
    ("Dora", "cachorro", "Vira-lata", "femea", 0, "pequeno", False, False, "Filhote de 4 meses, cheia de energia."),
    ("Zeca", "cachorro", "Beagle", "macho", 2, "medio", True, True, "Farejador incansável, adora passeios longos."),
    ("Mimi", "gato", "Angorá", "femea", 3, "pequeno", True, True, "Independente, mas retribui carinho no tempo dela."),
    ("Branquinho", "cachorro", "Vira-lata", "macho", 7, "medio", True, True, "Companheiro fiel, convive bem com outros animais."),
    ("Tico", "ave", "Calopsita", "macho", 2, "pequeno", False, False, "Assobia várias melodias e é bem sociável."),
    ("Maya", "gato", "Vira-lata", "femea", 1, "pequeno", True, False, "Resgatada com os irmãos; adoção separada ou em dupla."),
]


def demo():
    criar_admin("admin@adocao.local", "admin123")

    if not query("SELECT 1 FROM users WHERE email = 'user@adocao.local'"):
        execute("INSERT INTO users (nome, email, senha_hash, telefone) VALUES (%s,%s,%s,%s)",
                ("Usuário Teste", "user@adocao.local", generate_password_hash("user123"), "11 90000-0000"))

    ong = query("SELECT id FROM ongs WHERE email = 'ong@adocao.local'", one=True)
    if not ong:
        ong = execute(
            """INSERT INTO ongs (nome, email, senha_hash, telefone, descricao, cidade, estado,
                                 status_verificacao)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'verificada') RETURNING id""",
            ("Patas Amigas", "ong@adocao.local", generate_password_hash("ong123"),
             "11 98888-8888", "ONG de resgate e adoção responsável.", "São Paulo", "SP"))

    if query("SELECT 1 FROM anuncios WHERE ong_id = %s LIMIT 1", (ong["id"],)):
        print("animais de exemplo já existem")
        return
    for nome, esp, raca, sexo, idade, porte, vac, cast, desc in ANIMAIS:
        execute(
            """INSERT INTO anuncios (ong_id, nome_animal, especie, raca, sexo, idade, porte,
                                     vacinado, castrado, descricao)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (ong["id"], nome, esp, raca, sexo, idade, porte, vac, cast, desc))
    print(f"{len(ANIMAIS)} animais criados")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "admin":
        criar_admin(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "Administrador")
    else:
        demo()
