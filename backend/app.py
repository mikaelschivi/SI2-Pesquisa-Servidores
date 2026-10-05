import math
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException

UFS = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
)
TIMEOUT_CANCELAMENTO = "57014"

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080"}})
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={
        "options": "-c statement_timeout="
        + os.environ.get("STATEMENT_TIMEOUT_MS", "5000")
    },
)


class ErroApi(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


@app.errorhandler(ErroApi)
def erro_api(e):
    return jsonify(error=e.mensagem), e.status


@app.errorhandler(HTTPException)
def erro_http(e):
    return jsonify(error=e.description), e.code


@app.errorhandler(Exception)
def erro_interno(e):
    return jsonify(error="erro interno"), 500


def texto(campo):
    valor = request.args.get(campo)
    if valor is None:
        return None
    valor = valor.strip()
    if not valor or len(valor) > 200:
        raise ErroApi(400, f"parametro {campo} invalido")
    return valor


def inteiro(campo, padrao, maximo):
    bruto = request.args.get(campo, str(padrao))
    if not (bruto.isascii() and bruto.isdigit()):
        raise ErroApi(400, f"parametro {campo} invalido")
    valor = int(bruto)
    if valor < 1 or valor > maximo:
        raise ErroApi(400, f"parametro {campo} invalido")
    return valor


def similar():
    valor = request.args.get("similar", "false")
    if valor not in ("true", "false"):
        raise ErroApi(400, "parametro similar invalido")
    return valor == "true"


def filtros(usa_similar):
    nome = texto("nome")
    cargo = texto("cargo")
    orgao = texto("orgao")
    uf = texto("uf")
    textos = {"nome": nome, "cargo": cargo, "orgao": orgao}
    if usa_similar and all(valor is None for valor in textos.values()):
        raise ErroApi(400, "similar exige nome, cargo ou orgao")
    if uf is not None:
        uf = uf.upper()
        if uf not in UFS:
            raise ErroApi(400, "UF invalida")
    operador = "ILIKE" if usa_similar else "="
    condicoes = []
    params = {}
    for campo, valor in textos.items():
        if valor is not None:
            condicoes.append(f"LOWER({campo}) {operador} LOWER(:{campo})")
            params[campo] = valor
    if uf is not None:
        condicoes.append("uf = :uf")
        params["uf"] = uf
    return " AND ".join(condicoes) or "TRUE", params


def consultar(sql_fim, params, where):
    try:
        with engine.connect() as conn:
            return conn.execute(
                text(
                    "SELECT id, nome, cargo, orgao, uf, situacao FROM servidores "
                    f"WHERE {where} {sql_fim}"
                ),
                params,
            ).mappings().all()
    except OperationalError as e:
        if getattr(e.orig, "pgcode", None) == TIMEOUT_CANCELAMENTO:
            raise ErroApi(504, "consulta excedeu o tempo limite")
        raise


@app.get("/api/servidores")
@limiter.limit("20/minute")
def servidores():
    if similar():
        limite = inteiro("limit", 100, 100)
        where, params = filtros(True)
        params["limite"] = limite
        linhas = consultar("ORDER BY nome, id LIMIT :limite", params, where)
        total = len(linhas)
        return jsonify(
            data=[dict(linha) for linha in linhas],
            page=1,
            page_size=limite,
            total=total,
            total_pages=1,
        )
    pagina = inteiro("page", 1, 1000000)
    tamanho = inteiro("page_size", 20, 100)
    where, params = filtros(False)
    params["limite"] = tamanho
    params["deslocamento"] = (pagina - 1) * tamanho
    try:
        with engine.connect() as conn:
            total = conn.execute(
                text(f"SELECT COUNT(*) FROM servidores WHERE {where}"), params
            ).scalar()
    except OperationalError as e:
        if getattr(e.orig, "pgcode", None) == TIMEOUT_CANCELAMENTO:
            raise ErroApi(504, "consulta excedeu o tempo limite")
        raise
    linhas = consultar("ORDER BY id LIMIT :limite OFFSET :deslocamento", params, where)
    return jsonify(
        data=[dict(linha) for linha in linhas],
        page=pagina,
        page_size=tamanho,
        total=total,
        total_pages=math.ceil(total / tamanho),
    )
