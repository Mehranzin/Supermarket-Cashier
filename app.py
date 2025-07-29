from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from banco import inicializar_banco

app = Flask(__name__)
app.secret_key = "GodIsTheTrue11"

inicializar_banco()

def conectar():
    return sqlite3.connect("produtos.db")

@app.route("/", methods=["GET", "POST"])
def index():
    if "carrinho" not in session:
        session["carrinho"] = {}

    if request.method == "POST":
        codigo = request.form["codigo"].strip()
        quantidade = int(request.form.get("quantidade", 1))
        if quantidade < 1:
            flash("Quantidade deve ser no mínimo 1.", "error")
            return redirect(url_for("index"))
            
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE codigo LIKE ? ORDER BY codigo LIMIT 1", (codigo + '%',))
        produto = cursor.fetchone()
        conn.close()

        if not produto:
            flash("Produto não encontrado.", "error")
            return redirect(url_for("index"))

        id_produto = str(produto[0])
        nome = produto[1]
        preco = produto[3]
        estoque = produto[5]

        carrinho = session["carrinho"]

        if id_produto in carrinho:
            nova_quantidade = carrinho[id_produto]["quantidade"] + quantidade
            if nova_quantidade <= estoque:
                carrinho[id_produto]["quantidade"] = nova_quantidade
                flash(f"Quantidade de {nome} aumentada para {nova_quantidade}.", "success")
            else:
                flash(f"Estoque insuficiente para o produto {nome}.", "error")
        else:
            if quantidade <= estoque:
                carrinho[id_produto] = {
                    "nome": nome,
                    "preco": preco,
                    "quantidade": quantidade,
                    "estoque": estoque
                }
                session["ultimo_id"] = id_produto
                flash(f"{nome} adicionado ao carrinho.", "success")
            else:
                flash(f"Quantidade solicitada maior que o estoque disponível para {nome}.", "error")

        session["carrinho"] = carrinho
        return redirect(url_for("index"))

    carrinho = session.get("carrinho", {})
    total = sum(item["preco"] * item["quantidade"] for item in carrinho.values())

    return render_template("index.html", carrinho=carrinho, total=total)

@app.route("/diminuir/<id_produto>")
def diminuir(id_produto):
    carrinho = session.get("carrinho", {})
    if id_produto in carrinho:
        if carrinho[id_produto]["quantidade"] > 1:
            carrinho[id_produto]["quantidade"] -= 1
            flash(f"Quantidade de {carrinho[id_produto]['nome']} diminuída para {carrinho[id_produto]['quantidade']}.", "success")
        else:
            nome = carrinho[id_produto]["nome"]
            carrinho.pop(id_produto)
            flash(f"{nome} removido do carrinho.", "success")
        session["carrinho"] = carrinho
    else:
        flash("Produto não encontrado no carrinho.", "error")

    return redirect(url_for("index"))

@app.route("/remover/<id_produto>")
def remover(id_produto):
    carrinho = session.get("carrinho", {})
    if id_produto in carrinho:
        nome = carrinho[id_produto]["nome"]
        carrinho.pop(id_produto)
        session["carrinho"] = carrinho
        flash(f"{nome} removido do carrinho.", "success")
    else:
        flash("Produto não encontrado no carrinho.", "error")

    return redirect(url_for("index"))

@app.route("/finalizar", methods=["POST"])
def finalizar():
    carrinho = session.get("carrinho", {})
    if not carrinho:
        flash("Carrinho vazio.", "error")
        return redirect(url_for("index"))

    conn = conectar()
    cursor = conn.cursor()

    # Verificar estoque
    for id_produto, item in carrinho.items():
        cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (id_produto,))
        estoque_atual = cursor.fetchone()
        if not estoque_atual:
            conn.close()
            flash(f"Produto {item['nome']} não encontrado no banco.", "error")
            return redirect(url_for("index"))
        if estoque_atual[0] < item["quantidade"]:
            conn.close()
            flash(f"Estoque insuficiente para o produto {item['nome']}.", "error")
            return redirect(url_for("index"))

    # Atualizar estoque
    for id_produto, item in carrinho.items():
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], id_produto)
        )
    conn.commit()
    conn.close()

    session.pop("carrinho", None)
    session.pop("ultimo_id", None)
    flash("Compra finalizada com sucesso!", "success")

    return redirect(url_for("index"))

# Rotas para as outras páginas já existentes
def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    resultado = cursor.fetchall()
    conn.close()
    
    produtos = [
        {
            "id": row[0],
            "nome": row[1],
            "peso": row[2],
            "preco": row[3],
            "validade": row[4],
            "estoque": row[5],
            "codigo": row[6],
        }
        for row in resultado
    ]
    return produtos

@app.route("/lista")
def lista():
    produtos = listar_produtos()
    return render_template("lista.html", produtos=produtos)

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/relatorio")
def relatorio():
    return render_template("relatorio.html")

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
    app.run(debug=True, port=5000)
