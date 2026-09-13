import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "produtos.db"


def conectar():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=10,
        check_same_thread=False
    )

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")

    return conn


def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            peso TEXT,
            preco REAL NOT NULL,
            validade TEXT,
            estoque INTEGER NOT NULL DEFAULT 0,
            codigo TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            total REAL NOT NULL,
            data_venda TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            cargo TEXT NOT NULL
                CHECK (cargo IN ('admin', 'funcionario'))
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_produtos_codigo
        ON produtos(codigo)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vendas_data
        ON vendas(data_venda DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vendas_nome
        ON vendas(nome)
    """)

    conn.commit()
    conn.close()