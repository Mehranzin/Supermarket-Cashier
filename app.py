from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import sqlite3

from banco import (
    inicializar_bancos,
    conectar_usuarios,
    conectar_produtos,
    conectar_vendas
)

from seguranca import (
    carregar_secret_key,
    validar_chave_master,
    criar_hash_senha
)

from datetime import datetime
from functools import wraps


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

app.secret_key = carregar_secret_key()

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

inicializar_bancos()


# ============================================================
# DECORATORS
# ============================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:

            flash(
                "Você precisa estar logado.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:

            flash(
                "Você precisa estar logado.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        if session.get("cargo") not in (
            "admin",
            "master"
        ):

            flash(
                "Acesso restrito ao administrador.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        return f(*args, **kwargs)

    return decorated_function


def master_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "usuario_id" not in session:

            flash(
                "Você precisa estar logado.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        if session.get("cargo") != "master":

            flash(
                "Acesso restrito ao Master.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# VERIFICA SE SISTEMA JÁ POSSUI MASTER
# ============================================================

def sistema_ativado():

    conn = conectar_usuarios()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM usuarios
        WHERE cargo = 'master'
    """)

    total = cursor.fetchone()["total"]

    conn.close()

    return total > 0


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "usuario_id" in session:

        return redirect(
            url_for("index")
        )

    if request.method == "POST":

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        senha = request.form.get(
            "senha",
            ""
        )

        if not usuario or not senha:

            flash(
                "Informe usuário e senha.",
                "error"
            )

            return render_template(
                "login.html"
            )

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

            return render_template(
                "login.html"
            )

        if not user["ativo"]:

            conn.close()

            flash(
                "Esta conta está desativada.",
                "error"
            )

            return render_template(
                "login.html"
            )

        from werkzeug.security import check_password_hash

        if not check_password_hash(
            user["senha_hash"],
            senha
        ):

            conn.close()

            flash(
                "Usuário ou senha incorretos.",
                "error"
            )

            return render_template(
                "login.html"
            )

        cursor.execute("""
            UPDATE usuarios
            SET ultimo_login = ?
            WHERE id = ?
        """, (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
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

        return redirect(
            url_for("index")
        )

    return render_template(
        "login.html"
    )


# ============================================================
# ATIVAÇÃO DO SISTEMA
# ============================================================

@app.route(
    "/ativar-sistema",
    methods=["GET", "POST"]
)
def ativar_sistema():

    if sistema_ativado():

        flash(
            "O sistema já foi ativado.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        chave = request.form.get(
            "chave",
            ""
        ).strip()

        if not chave:

            flash(
                "Informe a chave de ativação.",
                "error"
            )

            return render_template(
                "ativar_sistema.html"
            )

        if not validar_chave_master(chave):

            flash(
                "Chave de ativação inválida.",
                "error"
            )

            return render_template(
                "ativar_sistema.html"
            )

        conn = conectar_usuarios()
        cursor = conn.cursor()

        try:

            senha_hash = criar_hash_senha(
                chave
            )

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
                "O sistema já possui um Master.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        conn.close()

        flash(
            "Sistema ativado com sucesso. "
            "Faça login como Master.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "ativar_sistema.html"
    )


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
# CRIAR ADMIN
# ============================================================

@app.route(
    "/master/criar-admin",
    methods=["GET", "POST"]
)
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

        if len(senha) < 8:

            flash(
                "A senha deve possuir pelo menos 8 caracteres.",
                "error"
            )

            return redirect(
                url_for("criar_admin")
            )

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
                criar_hash_senha(senha),
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

@app.route(
    "/admin/criar-funcionario",
    methods=["GET", "POST"]
)
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

        if len(senha) < 8:

            flash(
                "A senha deve possuir pelo menos 8 caracteres.",
                "error"
            )

            return redirect(
                url_for("criar_funcionario")
            )

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
                criar_hash_senha(senha),
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

    return redirect(
        url_for("login")
    )


# ============================================================
# CAIXA
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
@login_required
def index():

    if "carrinho" not in session:

        session["carrinho"] = {}

    if request.method == "POST":

        codigo = request.form.get(
            "codigo",
            ""
        ).strip()

        try:

            quantidade = int(
                request.form.get(
                    "quantidade",
                    1
                )
            )

        except ValueError:

            flash(
                "Quantidade inválida.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        if not codigo:

            flash(
                "Informe o código do produto.",
                "error"
            )

            return redirect(
                url_for("index")
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
            WHERE codigo = ?
            LIMIT 1
        """, (codigo,))

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

        carrinho = session["carrinho"]

        quantidade_atual = 0

        if id_produto in carrinho:

            quantidade_atual = carrinho[
                id_produto
            ]["quantidade"]

        nova_quantidade = (
            quantidade_atual + quantidade
        )

        if nova_quantidade > produto["estoque"]:

            flash(
                f"Estoque insuficiente para {produto['nome']}.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        carrinho[id_produto] = {
            "nome": produto["nome"],
            "preco": produto["preco"],
            "quantidade": nova_quantidade,
            "estoque": produto["estoque"]
        }

        session["carrinho"] = carrinho

        flash(
            f"{produto['nome']} adicionado.",
            "success"
        )

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
# DIMINUIR
# ============================================================

@app.route(
    "/diminuir/<id_produto>",
    methods=["POST"]
)
@login_required
def diminuir(id_produto):

    carrinho = session.get(
        "carrinho",
        {}
    )

    if id_produto in carrinho:

        if carrinho[id_produto]["quantidade"] > 1:

            carrinho[id_produto]["quantidade"] -= 1

        else:

            carrinho.pop(id_produto)

        session["carrinho"] = carrinho

    return redirect(
        url_for("index")
    )


# ============================================================
# REMOVER
# ============================================================

@app.route(
    "/remover/<id_produto>",
    methods=["POST"]
)
@login_required
def remover(id_produto):

    carrinho = session.get(
        "carrinho",
        {}
    )

    carrinho.pop(
        id_produto,
        None
    )

    session["carrinho"] = carrinho

    return redirect(
        url_for("index")
    )


# ============================================================
# FINALIZAR VENDA
# ============================================================

@app.route(
    "/finalizar",
    methods=["POST"]
)
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
    conn_vendas = conectar_vendas()

    cursor_produtos = conn_produtos.cursor()
    cursor_vendas = conn_vendas.cursor()

    try:

        total_venda = 0

        produtos_venda = []

        for id_produto, item in carrinho.items():

            cursor_produtos.execute("""
                SELECT
                    id,
                    nome,
                    preco,
                    estoque
                FROM produtos
                WHERE id = ?
            """, (id_produto,))

            produto = cursor_produtos.fetchone()

            if not produto:

                raise ValueError(
                    f"Produto {id_produto} não existe."
                )

            if produto["estoque"] < item["quantidade"]:

                raise ValueError(
                    f"Estoque insuficiente para {produto['nome']}."
                )

            subtotal = (
                item["preco"]
                * item["quantidade"]
            )

            total_venda += subtotal

            produtos_venda.append(
                (
                    produto,
                    item,
                    subtotal
                )
            )

        data = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

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

        for produto, item, subtotal in produtos_venda:

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
                produto["id"],
                produto["nome"],
                item["preco"],
                item["quantidade"],
                subtotal
            ))

            cursor_produtos.execute("""
                UPDATE produtos
                SET estoque = estoque - ?
                WHERE id = ?
            """, (
                item["quantidade"],
                produto["id"]
            ))

        conn_vendas.commit()
        conn_produtos.commit()

    except Exception as erro:

        conn_vendas.rollback()
        conn_produtos.rollback()

        print(
            f"ERRO AO FINALIZAR VENDA: {erro}"
        )

        flash(
            "Não foi possível finalizar a venda.",
            "error"
        )

        conn_vendas.close()
        conn_produtos.close()

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
        "Compra finalizada com sucesso.",
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
        ORDER BY nome
    """)

    resultado = cursor.fetchall()

    conn.close()

    return resultado


@app.route("/lista")
@login_required
def lista():

    produtos = listar_produtos()

    return render_template(
        "lista.html",
        produtos=produtos
    )


# ============================================================
# CADASTRO
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
            iv.nome_produto,
            iv.preco_unitario,
            iv.quantidade,
            iv.subtotal,
            v.data_venda
        FROM itens_venda iv
        INNER JOIN vendas v
            ON iv.venda_id = v.id
        ORDER BY v.data_venda DESC
    """)

    vendas = cursor.fetchall()

    lucro_total = sum(
        row["subtotal"]
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

@app.route(
    "/adicionar",
    methods=["POST"]
)
@admin_required
def adicionar():

    try:

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        peso = request.form.get(
            "peso",
            ""
        ).strip()

        preco = float(
            request.form.get(
                "preco",
                0
            )
        )

        validade = request.form.get(
            "validade",
            ""
        ).strip()

        estoque = int(
            request.form.get(
                "estoque",
                0
            )
        )

        codigo = request.form.get(
            "codigo",
            ""
        ).strip()

    except ValueError:

        flash(
            "Dados inválidos.",
            "error"
        )

        return redirect(
            url_for("cadastro")
        )

    if not nome or not codigo:

        flash(
            "Nome e código são obrigatórios.",
            "error"
        )

        return redirect(
            url_for("cadastro")
        )

    if preco < 0 or estoque < 0:

        flash(
            "Preço e estoque não podem ser negativos.",
            "error"
        )

        return redirect(
            url_for("cadastro")
        )

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

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )