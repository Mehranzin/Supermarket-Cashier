import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"

DATABASE_DIR.mkdir(exist_ok=True)


def conectar_usuarios():
    conn = sqlite3.connect(DATABASE_DIR / "usuarios.db")
    conn.row_factory = sqlite3.Row
    return conn


def conectar_produtos():
    conn = sqlite3.connect(DATABASE_DIR / "produtos.db")
    conn.row_factory = sqlite3.Row
    return conn


def conectar_vendas():
    conn = sqlite3.connect(DATABASE_DIR / "vendas.db")
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_usuarios():
    conn = conectar_usuarios()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            cargo TEXT NOT NULL CHECK (
                cargo IN ('master', 'admin', 'funcionario')
            ),
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ultimo_login TEXT
        )
    """)

    conn.commit()
    conn.close()


def inicializar_produtos():
    conn = conectar_produtos()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            peso TEXT,
            preco REAL NOT NULL,
            validade TEXT,
            estoque INTEGER NOT NULL DEFAULT 0,
            codigo TEXT UNIQUE NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def inicializar_vendas():
    conn = conectar_vendas()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_venda TEXT NOT NULL,
            total REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            nome_produto TEXT NOT NULL,
            preco_unitario REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            subtotal REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def inicializar_bancos():
    inicializar_usuarios()
    inicializar_produtos()
    inicializar_vendas()