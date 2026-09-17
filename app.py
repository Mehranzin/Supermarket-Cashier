from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from banco import (
    inicializar_bancos,
    conectar_usuarios,
    conectar_produtos,
    conectar_vendas
)
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY não configurada.")


# Inicializa os três bancos
inicializar_bancos()


# ============================================================
# DECORATORS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:
            flash(
                "Você precisa estar logado para acessar essa página.",
                "error"
            )
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:
            flash(
                "Você precisa estar logado para acessar essa página.",
                "error"
            )
            return redirect(url_for("login"))

        if session.get("cargo") not in ("admin", "master"):
            flash(
                "Acesso restrito ao administrador.",
                "error"
            )
            return redirect(url_for("index"))

        return f(*args, **kwargs)

    return decorated_function


def master_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:
            flash(
                "Você precisa estar logado para acessar essa página.",
                "error"
            )
            return redirect(url_for("login"))

        if session.get("cargo") != "master":
            flash(
                "Acesso restrito.",
                "error"
            )
            return redirect(url_for("index"))

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "usuario_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":

        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        if not usuario or not senha:
            flash(
                "Informe usuário e senha.",
                "error"
            )
            return render_template("login.html")

        conn = conectar_usuarios()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                nome,
                senha_hash,
                cargo,
                ativo
            FROM usuarios
            WHERE usuario = ?
        """, (usuario,))

        user = cursor.fetchone()

        if not user:
            conn.close()

            flash(
                "Usuário ou senha incorretos.",
                "error"
            )

            return render_template("login.html")

        if not user["ativo"]:
            conn.close()

            flash(
                "Esta conta está desativada.",
                "error"
            )

            return render_template("login.html")

        if not check_password_hash(
            user["senha_hash"],
            senha
        ):
            conn.close()

            flash(
                "Usuário ou senha incorretos.",
                "error"
            )

            return render_template("login.html")

        cursor.execute("""
            UPDATE usuarios
            SET ultimo_login = ?
            WHERE id = ?
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user["id"]
        ))

        conn.commit()
        conn.close()

        session.clear()

        session["usuario_id"] = user["id"]
        session["nome"] = user["nome"]
        session["cargo"] = user["cargo"]

        flash(
            f"Bem-vindo, {user['nome']}!",
            "success"
        )

        return redirect(url_for("index"))

    return render_template("login.html")


# ============================================================
# ATIVAÇÃO INICIAL DO SISTEMA
# ============================================================

@app.route("/ativar-sistema", methods=["GET", "POST"])
def ativar_sistema():

    conn = conectar_usuarios()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM usuarios
        WHERE cargo = 'master'
    """)

    master_existente = cursor.fetchone()["total"]

    if master_existente > 0:
        conn.close()

        flash(
            "O sistema já foi ativado.",
            "error"
        )

        return redirect(url_for("login"))

    if request.method == "POST":

        senha = request.form.get("senha", "")

        senha_ativacao = os.environ.get("MASTER_ACTIVATION_PASSWORD")

        if not senha_ativacao:
            conn.close()

            raise RuntimeError(
                "MASTER_ACTIVATION_PASSWORD não configurada."
            )

        if senha != senha_ativacao:
            conn.close()

            flash(
                "Senha de ativação inválida.",
                "error"
            )

            return redirect(url_for("ativar_sistema"))

        senha_hash = generate_password_hash(senha)

        try:

            cursor.execute("""
                INSERT INTO usuarios
                (
                    nome,
                    usuario,
                    senha_hash,
                    cargo,
                    ativo
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Alemomn",
                "Alemomn",
                senha_hash,
                "master",
                1
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            flash(
                "O usuário Master já existe.",
                "error"
            )

            return redirect(url_for("login"))

        conn.close()

        flash(
            "Sistema ativado com sucesso.",
            "success"
        )

        return redirect(url_for("login"))

    conn.close()

    return render_template("ativar_sistema.html")


# ============================================================
# USUÁRIOS
# ============================================================

@app.route("/admin/usuarios")
@admin_required
def usuarios():

    conn = conectar_usuarios()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            usuario,
            cargo,
            ativo,
            criado_em,
            ultimo_login
        FROM usuarios
        WHERE cargo != 'master'
        ORDER BY nome
    """)

    usuarios = cursor.fetchall()

    conn.close()

    return render_template(
        "usuarios.html",
        usuarios=usuarios
    )


# ============================================================
# CRIAR ADMINISTRADOR
# ============================================================

@app.route("/master/criar-admin", methods=["GET", "POST"])
@master_required
def criar_admin():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        senha = request.form.get(
            "senha",
            ""
        )

        if not nome or not usuario or not senha:

            flash(
                "Todos os campos são obrigatórios.",
                "error"
            )

            return redirect(
                url_for("criar_admin")
            )

        senha_hash = generate_password_hash(senha)

        conn = conectar_usuarios()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO usuarios
                (
                    nome,
                    usuario,
                    senha_hash,
                    cargo,
                    ativo
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                usuario,
                senha_hash,
                "admin",
                1
            ))

            conn.commit()

            flash(
                "Administrador criado com sucesso.",
                "success"
            )

        except sqlite3.IntegrityError:

            flash(
                "Esse nome de usuário já existe.",
                "error"
            )

        finally:

            conn.close()

        return redirect(
            url_for("usuarios")
        )

    return render_template(
        "criar_admin.html"
    )


# ============================================================
# CRIAR FUNCIONÁRIO
# ============================================================

@app.route("/admin/criar-funcionario", methods=["GET", "POST"])
@admin_required
def criar_funcionario():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        senha = request.form.get(
            "senha",
            ""
        )

        if not nome or not usuario or not senha:

            flash(
                "Todos os campos são obrigatórios.",
                "error"
            )

            return redirect(
                url_for("criar_funcionario")
            )

        senha_hash = generate_password_hash(senha)

        conn = conectar_usuarios()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO usuarios
                (
                    nome,
                    usuario,
                    senha_hash,
                    cargo,
                    ativo
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                usuario,
                senha_hash,
                "funcionario",
                1
            ))

            conn.commit()

            flash(
                "Funcionário criado com sucesso.",
                "success"
            )

        except sqlite3.IntegrityError:

            flash(
                "Esse nome de usuário já existe.",
                "error"
            )

        finally:

            conn.close()

        return redirect(
            url_for("usuarios")
        )

    return render_template(
        "criar_funcionario.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Você saiu da conta.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ============================================================
# CAIXA / CARRINHO
# ============================================================

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if "carrinho" not in session:
        session["carrinho"] = {}

    if request.method == "POST":

        codigo = request.form.get(
            "codigo",
            ""
        ).strip()

        quantidade = int(
            request.form.get(
                "quantidade",
                1
            )
        )

        if quantidade < 1:

            flash(
                "Quantidade deve ser no mínimo 1.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        conn = conectar_produtos()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM produtos
            WHERE codigo LIKE ?
            ORDER BY codigo
            LIMIT 1
        """, (
            codigo + "%",
        ))

        produto = cursor.fetchone()

        conn.close()

        if not produto:

            flash(
                "Produto não encontrado.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        id_produto = str(
            produto["id"]
        )

        nome = produto["nome"]
        preco = produto["preco"]
        estoque = produto["estoque"]

        carrinho = session["carrinho"]

        if id_produto in carrinho:

            nova_quantidade = (
                carrinho[id_produto]["quantidade"]
                + quantidade
            )

            if nova_quantidade <= estoque:

                carrinho[id_produto]["quantidade"] = (
                    nova_quantidade
                )

                flash(
                    f"Quantidade de {nome} aumentada para {nova_quantidade}.",
                    "success"
                )

            else:

                flash(
                    f"Estoque insuficiente para o produto {nome}.",
                    "error"
                )

        else:

            if quantidade <= estoque:

                carrinho[id_produto] = {
                    "nome": nome,
                    "preco": preco,
                    "quantidade": quantidade,
                    "estoque": estoque
                }

                session["ultimo_id"] = id_produto

                flash(
                    f"{nome} adicionado ao carrinho.",
                    "success"
                )

            else:

                flash(
                    f"Quantidade solicitada maior que o estoque disponível para {nome}.",
                    "error"
                )

        session["carrinho"] = carrinho

        return redirect(
            url_for("index")
        )

    carrinho = session.get(
        "carrinho",
        {}
    )

    total = sum(
        item["preco"] * item["quantidade"]
        for item in carrinho.values()
    )

    return render_template(
        "index.html",
        carrinho=carrinho,
        total=total
    )


# ============================================================
# DIMINUIR PRODUTO
# ============================================================

@app.route("/diminuir/<id_produto>")
@login_required
def diminuir(id_produto):

    carrinho = session.get(
        "carrinho",
        {}
    )

    if id_produto in carrinho:

        if carrinho[id_produto]["quantidade"] > 1:

            carrinho[id_produto]["quantidade"] -= 1

            flash(
                f"Quantidade de {carrinho[id_produto]['nome']} diminuída.",
                "success"
            )

        else:

            carrinho.pop(id_produto)

            flash(
                "Produto removido do carrinho.",
                "success"
            )

        session["carrinho"] = carrinho

    return redirect(
        url_for("index")
    )


# ============================================================
# REMOVER PRODUTO
# ============================================================

@app.route("/remover/<id_produto>")
@login_required
def remover(id_produto):

    carrinho = session.get(
        "carrinho",
        {}
    )

    if id_produto in carrinho:

        carrinho.pop(id_produto)

        flash(
            "Produto removido.",
            "success"
        )

        session["carrinho"] = carrinho

    return redirect(
        url_for("index")
    )


# ============================================================
# FINALIZAR VENDA
# ============================================================

@app.route("/finalizar", methods=["POST"])
@login_required
def finalizar():

    carrinho = session.get(
        "carrinho",
        {}
    )

    if not carrinho:

        flash(
            "Carrinho vazio.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    conn_produtos = conectar_produtos()
    cursor_produtos = conn_produtos.cursor()

    # Verifica estoque
    for id_produto, item in carrinho.items():

        cursor_produtos.execute("""
            SELECT estoque
            FROM produtos
            WHERE id = ?
        """, (
            id_produto,
        ))

        estoque_atual = cursor_produtos.fetchone()

        if (
            not estoque_atual
            or estoque_atual["estoque"] < item["quantidade"]
        ):

            conn_produtos.close()

            flash(
                f"Estoque insuficiente para {item['nome']}.",
                "error"
            )

            return redirect(
                url_for("index")
            )

    total_venda = sum(
        item["preco"] * item["quantidade"]
        for item in carrinho.values()
    )

    data = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn_vendas = conectar_vendas()
    cursor_vendas = conn_vendas.cursor()

    try:

        # Cria a venda
        cursor_vendas.execute("""
            INSERT INTO vendas
            (
                usuario_id,
                data_venda,
                total
            )
            VALUES (?, ?, ?)
        """, (
            session["usuario_id"],
            data,
            total_venda
        ))

        venda_id = cursor_vendas.lastrowid

        # Registra os produtos vendidos
        for id_produto, item in carrinho.items():

            subtotal = (
                item["preco"]
                * item["quantidade"]
            )

            cursor_vendas.execute("""
                INSERT INTO itens_venda
                (
                    venda_id,
                    produto_id,
                    nome_produto,
                    preco_unitario,
                    quantidade,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                venda_id,
                int(id_produto),
                item["nome"],
                item["preco"],
                item["quantidade"],
                subtotal
            ))

            # Baixa estoque
            cursor_produtos.execute("""
                UPDATE produtos
                SET estoque = estoque - ?
                WHERE id = ?
            """, (
                item["quantidade"],
                id_produto
            ))

        conn_vendas.commit()
        conn_produtos.commit()

    except Exception:

        conn_vendas.rollback()
        conn_produtos.rollback()

        conn_vendas.close()
        conn_produtos.close()

        flash(
            "Não foi possível finalizar a compra.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    conn_vendas.close()
    conn_produtos.close()

    session.pop(
        "carrinho",
        None
    )

    flash(
        "Compra finalizada!",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# PRODUTOS
# ============================================================

def listar_produtos():

    conn = conectar_produtos()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM produtos
    """)

    resultado = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "nome": row["nome"],
            "peso": row["peso"],
            "preco": row["preco"],
            "validade": row["validade"],
            "estoque": row["estoque"],
            "codigo": row["codigo"]
        }
        for row in resultado
    ]


# ============================================================
# LISTA DE PRODUTOS
# ============================================================

@app.route("/lista")
@login_required
def lista():

    produtos = listar_produtos()

    return render_template(
        "lista.html",
        produtos=produtos
    )


# ============================================================
# CADASTRO DE PRODUTOS
# ============================================================

@app.route("/cadastro")
@admin_required
def cadastro():

    return render_template(
        "cadastro.html"
    )


# ============================================================
# RELATÓRIO
# ============================================================

@app.route("/relatorio")
@admin_required
def relatorio():

    conn = conectar_vendas()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            v.id,
            v.usuario_id,
            v.data_venda,
            v.total
        FROM vendas v
        ORDER BY v.data_venda DESC
    """)

    vendas = cursor.fetchall()

    lucro_total = sum(
        row["total"]
        for row in vendas
    )

    conn.close()

    return render_template(
        "relatorio.html",
        vendas=vendas,
        lucro_total=lucro_total
    )


# ============================================================
# ADICIONAR PRODUTO
# ============================================================

@app.route("/adicionar", methods=["POST"])
@admin_required
def adicionar():

    nome = request.form["nome"]
    peso = request.form["peso"]
    preco = float(
        request.form["preco"]
    )
    validade = request.form["validade"]
    estoque = int(
        request.form["estoque"]
    )
    codigo = request.form["codigo"]

    conn = conectar_produtos()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO produtos
            (
                nome,
                peso,
                preco,
                validade,
                estoque,
                codigo
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            nome,
            peso,
            preco,
            validade,
            estoque,
            codigo
        ))

        conn.commit()

        flash(
            "Produto cadastrado com sucesso.",
            "success"
        )

    except sqlite3.IntegrityError:

        flash(
            "O código do produto já existe.",
            "error"
        )

    finally:

        conn.close()

    return redirect(
        url_for("lista")
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)