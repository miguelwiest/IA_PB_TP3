"""
População inicial do banco SQLite (TP3).

Cria dois usuários com senhas distintas e tickets de exemplo pertencentes a
cada um deles, para permitir o teste automatizado de BOLA (Broken Object
Level Authorization): o usuário "cliente_fernanda" não pode ler o ticket do
usuário "admin" através de `GET /tickets/{id}`, e vice-versa.

Uso:
    python sqlite_populate.py
"""
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from sqlite_database import DB_PATH, init_db, get_connection
from security.auth import get_password_hash

# Credenciais de exemplo (documentadas aqui propositalmente: ambiente didático).
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_PLAIN = "AdminInfnet2026!"

CUSTOMER_USERNAME = "cliente_fernanda"
CUSTOMER_PASSWORD_PLAIN = "Fernanda2026!"

USERS = [
    {
        "username": ADMIN_USERNAME,
        "email": "admin@infnet.edu.br",
        "full_name": "Administrador do Atendimento IA",
        "disabled": 0,
        "hashed_password": get_password_hash(ADMIN_PASSWORD_PLAIN),
    },
    {
        "username": CUSTOMER_USERNAME,
        "email": "fernanda@cliente.com",
        "full_name": "Fernanda Lima (Cliente)",
        "disabled": 0,
        "hashed_password": get_password_hash(CUSTOMER_PASSWORD_PLAIN),
    },
]

TICKETS = [
    {
        "owner_username": ADMIN_USERNAME,
        "subject": "Acesso ao painel administrativo",
        "text": "Preciso validar os logs de acesso do painel administrativo desta semana.",
        "intent": "Technical issue",
    },
    {
        "owner_username": CUSTOMER_USERNAME,
        "subject": "Cobrança duplicada no cartão",
        "text": "Fui cobrada duas vezes pela mesma fatura neste mês, peço o estorno do valor duplicado.",
        "intent": "Billing inquiry",
    },
]


def populate(db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        for user in USERS:
            conn.execute(
                """
                INSERT INTO users (username, email, full_name, disabled, hashed_password)
                VALUES (:username, :email, :full_name, :disabled, :hashed_password)
                ON CONFLICT(username) DO UPDATE SET
                    email=excluded.email,
                    full_name=excluded.full_name,
                    disabled=excluded.disabled,
                    hashed_password=excluded.hashed_password
                """,
                user,
            )

        existing = conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"]
        if existing == 0:
            for ticket in TICKETS:
                conn.execute(
                    """
                    INSERT INTO tickets (owner_username, subject, text, intent)
                    VALUES (:owner_username, :subject, :text, :intent)
                    """,
                    ticket,
                )
        conn.commit()
    finally:
        conn.close()
    print(f"Banco populado com {len(USERS)} usuários e tickets de exemplo em: {db_path}")


if __name__ == "__main__":
    populate()
