from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from livereload import Server
from banco import inicializar_banco

app = Flask(__name__)

inicializar_banco()

def conectar():
    return sqlite3.connect("produtos.db")

def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "nome": row[1],
            "peso": row[2],
            "preco": row[3],
            "validade": row[4],
            "estoque": row[5],
            "codigo": row[6],
        }
        for row in produtos
    ]
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/lista")
def lista():
    produtos = listar_produtos()
    return render_template("lista.html", produtos=produtos)

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/adicionar", methods=["POST"])
def adicionar():
    nome = request.form["nome"]
    peso = request.form["peso"]
    preco = float(request.form["preco"])
    validade = request.form["validade"]
    estoque = int(request.form["estoque"])
    codigo = request.form["codigo"]

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO produtos (nome, peso, preco, validade, estoque, codigo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, peso, preco, validade, estoque, codigo))
    conn.commit()
    conn.close()

    return redirect(url_for("lista"))

if __name__ == "__main__":
    server = Server(app.wsgi_app)
    server.serve(debug=True, port=5000)