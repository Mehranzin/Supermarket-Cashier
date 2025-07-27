from flask import Flask, render_template
from livereload import Server

app = Flask(__name__)

produtos = [
    {"id": 1, "nome": "Arroz", "preco": 7.0, "estoque": 10},
    {"id": 2, "nome": "Feijão", "preco": 5.50, "estoque": 7},
    {"id": 3, "nome": "Pão do Sírio", "preco": 6.0, "estoque": 2},
]

@app.route("/")
def index():
    return render_template("index.html", produtos=produtos)

@app.route("/lista")
def lista():
    return render_template("lista.html", produtos=produtos)

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html", produtos=produtos)

if __name__ == "__main__":
    server = Server(app.wsgi_app)
    server.serve(debug=True)
