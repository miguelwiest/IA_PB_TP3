"""
Criação do esquema SQLite utilizado pela API (TP3).

Substitui a base de usuários 100% in-code do TP1/TP2 por um banco de dados
real (`fastapi/database.db`), com duas tabelas:

- users:   credenciais de autenticação (uma linha por usuário).
- tickets: recursos de suporte, cada um pertencente a um único `owner_username`.
           É essa tabela que permite testar BOLA (Broken Object Level
           Authorization) no TP3: dois usuários distintos, cada um dono de
           tickets diferentes.

Uso:
    python sqlite_database.py   # cria o arquivo e as tabelas (idempotente)
    python sqlite_populate.py   # popula com usuários/tickets de exemplo
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username        TEXT PRIMARY KEY,
    email           TEXT,
    full_name       TEXT,
    disabled        INTEGER NOT NULL DEFAULT 0,
    hashed_password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_username TEXT NOT NULL,
    subject        TEXT NOT NULL,
    text           TEXT NOT NULL,
    intent         TEXT NOT NULL,
    FOREIGN KEY (owner_username) REFERENCES users (username)
);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Abre uma conexão com row_factory em dict-like (sqlite3.Row)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Cria o arquivo de banco e as tabelas, caso ainda não existam."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_user_by_username(username: str, db_path: Path = DB_PATH) -> sqlite3.Row | None:
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cur.fetchone()
    finally:
        conn.close()


def get_ticket_by_id(ticket_id: int, db_path: Path = DB_PATH) -> sqlite3.Row | None:
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return cur.fetchone()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Banco inicializado em: {DB_PATH}")
