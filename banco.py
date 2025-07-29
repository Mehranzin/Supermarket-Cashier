import sqlite3

def inicializar_banco():
    conn = sqlite3.connect("produtos.db")
    cursor = conn.cursor()

    # Tabela de produtos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            peso TEXT,
            preco REAL,
            validade TEXT,
            estoque INTEGER,
            codigo TEXT
        )
    """)

    # Tabela de vendas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            preco REAL,
            quantidade INTEGER,
            total REAL,
            data_venda TEXT
        )
    """)

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            cargo TEXT NOT NULL CHECK (cargo IN ('admin', 'funcionario'))
        )
    """)

    conn.commit()
    conn.close()
