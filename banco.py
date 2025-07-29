import sqlite3

def inicializar_banco():
    conn = sqlite3.connect("produtos.db")
    cursor = conn.cursor()

    # Criação da tabela de produtos
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

    # Criação da tabela de vendas
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

    conn.commit()
    conn.close()
