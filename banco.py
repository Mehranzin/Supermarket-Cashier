import sqlite3
import os

def inicializar_banco():
    caminho = os.path.abspath("produtos.db")
    conn = sqlite3.connect(caminho)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            peso TEXT NOT NULL,
            preco REAL NOT NULL,
            validade TEXT NOT NULL,
            estoque INTEGER NOT NULL,
            codigo TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Tabela criada ou já existia no banco: {caminho}")
