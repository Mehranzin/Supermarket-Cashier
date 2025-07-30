from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from banco import inicializar_banco
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "GodIsTheTrue11"

inicializar_banco()

def conectar():
    return sqlite3.connect("produtos.db")

# --- DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Você precisa estar logado para acessar essa página.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("cargo") != "admin":
            flash("Acesso restrito ao administrador.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE LOGIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, cargo FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["usuario_id"] = user[0]
            session["nome"] = user[1]
            session["cargo"] = user[2]
            flash(f"Bem-vindo, {user[1]}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha incorretos.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome"]
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        codigo_secreto = request.form["codigo_secreto"]

        if codigo_secreto == "admin011@":
            cargo = "admin"
        elif codigo_secreto == "funcionario@":
            cargo = "funcionario"
        else:
            flash("Código de acesso inválido.", "error")
            return redirect(url_for("register"))

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, usuario, senha, cargo) VALUES (?, ?, ?, ?)", 
                           (nome, usuario, senha, cargo))
            conn.commit()
            flash("Usuário registrado com sucesso!", "success")
        except sqlite3.IntegrityError:
            flash("Usuário já existe!", "error")
        conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "success")
    return redirect(url_for("login"))

# --- ROTAS DE PRODUTO / CARRINHO ---
@app.route("/", methods=["GET", "POST"])
@login_required
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
@login_required
def diminuir(id_produto):
    carrinho = session.get("carrinho", {})
    if id_produto in carrinho:
        if carrinho[id_produto]["quantidade"] > 1:
            carrinho[id_produto]["quantidade"] -= 1
            flash(f"Quantidade de {carrinho[id_produto]['nome']} diminuída.", "success")
        else:
            carrinho.pop(id_produto)
            flash("Produto removido do carrinho.", "success")
        session["carrinho"] = carrinho
    return redirect(url_for("index"))

@app.route("/remover/<id_produto>")
@login_required
def remover(id_produto):
    carrinho = session.get("carrinho", {})
    if id_produto in carrinho:
        carrinho.pop(id_produto)
        flash("Produto removido.", "success")
        session["carrinho"] = carrinho
    return redirect(url_for("index"))

@app.route("/finalizar", methods=["POST"])
@login_required
def finalizar():
    carrinho = session.get("carrinho", {})
    if not carrinho:
        flash("Carrinho vazio.", "error")
        return redirect(url_for("index"))

    conn = conectar()
    cursor = conn.cursor()

    for id_produto, item in carrinho.items():
        cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (id_produto,))
        estoque_atual = cursor.fetchone()
        if not estoque_atual or estoque_atual[0] < item["quantidade"]:
            conn.close()
            flash(f"Estoque insuficiente para {item['nome']}.", "error")
            return redirect(url_for("index"))

    for id_produto, item in carrinho.items():
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item["quantidade"], id_produto))
        total = item["preco"] * item["quantidade"]
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO vendas (nome, preco, quantidade, total, data_venda) VALUES (?, ?, ?, ?, ?)",
                       (item["nome"], item["preco"], item["quantidade"], total, data))

    conn.commit()
    conn.close()
    session.pop("carrinho", None)
    flash("Compra finalizada!", "success")
    return redirect(url_for("index"))

# --- OUTRAS ROTAS ---
def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    resultado = cursor.fetchall()
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
        } for row in resultado
    ]

@app.route("/lista")
@login_required
def lista():
    produtos = listar_produtos()
    return render_template("lista.html", produtos=produtos)

@app.route("/cadastro")
@admin_required
def cadastro():
    return render_template("cadastro.html")

@app.route("/relatorio")
@admin_required
def relatorio():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, preco, quantidade, total, data_venda FROM vendas ORDER BY data_venda DESC")
    vendas = cursor.fetchall()
    lucro_total = sum(row[3] for row in vendas)
    conn.close()
    return render_template("relatorio.html", vendas=vendas, lucro_total=lucro_total)

@app.route("/adicionar", methods=["POST"])
@admin_required
def adicionar():
    nome = request.form["nome"]
    peso = request.form["peso"]
    preco = float(request.form["preco"])
    validade = request.form["validade"]
    estoque = int(request.form["estoque"])
    codigo = request.form["codigo"]

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO produtos (nome, peso, preco, validade, estoque, codigo)
                      VALUES (?, ?, ?, ?, ?, ?)""",
                   (nome, peso, preco, validade, estoque, codigo))
    conn.commit()
    conn.close()
    return redirect(url_for("lista"))

if __name__ == "__main__":
    app.run(debug=True)
