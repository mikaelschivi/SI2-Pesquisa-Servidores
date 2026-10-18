import os

import pytest
from sqlalchemy import create_engine, text

URL_TESTE = os.environ.get("TEST_DATABASE_URL")
if not URL_TESTE:
    pytest.skip("TEST_DATABASE_URL nao definida", allow_module_level=True)
os.environ["DATABASE_URL"] = URL_TESTE

import app as api
from carregar import SCHEMA


LINHAS = [
    {"nome": "ANA LIMA", "cargo": "ANALISTA", "orgao": "MINISTERIO DA FAZENDA", "uf": "SP", "situacao": "ativo"},
    {"nome": "JOSE PEREIRA", "cargo": "TECNICO", "orgao": "MINISTERIO DA SAUDE", "uf": "RS", "situacao": "aposentado"},
    {"nome": "MARIA SOUZA", "cargo": "ANALISTA", "orgao": "UNIVERSIDADE FEDERAL DO RIO GRANDE", "uf": "RS", "situacao": "ativo"},
    {"nome": "PEDRO ALVES", "cargo": "AUDITOR", "orgao": "CONTROLADORIA-GERAL DA UNIAO", "uf": "DF", "situacao": "ativo"},
] + [
    {"nome": f"SERVIDOR {i:02d}", "cargo": "TECNICO", "orgao": "MINISTERIO DA SAUDE", "uf": "MG", "situacao": "ativo"}
    for i in range(22)
]


@pytest.fixture(scope="module", autouse=True)
def base_de_teste():
    engine = create_engine(URL_TESTE)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS servidores"))
        conn.execute(text(SCHEMA))
        conn.execute(
            text(
                "INSERT INTO servidores (nome, cargo, orgao, uf, situacao) "
                "VALUES (:nome, :cargo, :orgao, :uf, :situacao)"
            ),
            LINHAS,
        )
    engine.dispose()
    yield


@pytest.fixture
def cliente():
    api.limiter.enabled = False
    return api.app.test_client()


def buscar(cliente, query):
    resposta = cliente.get(f"/api/servidores?{query}")
    return resposta, resposta.get_json()


def test_busca_nome_parcial_ignora_maiusculas(cliente):
    resposta, corpo = buscar(cliente, "nome=ana%20lima")
    assert resposta.status_code == 200
    assert corpo["total"] == 1
    assert corpo["data"][0]["nome"] == "ANA LIMA"


def test_busca_exata_nao_casa_parte_do_nome(cliente):
    _, corpo = buscar(cliente, "nome=souza")
    assert corpo["total"] == 0


def test_busca_similar_limit(cliente):
    _, corpo = buscar(cliente, "nome=%25SERVIDOR%25&similar=true&limit=3")
    assert len(corpo["data"]) == 3
    assert corpo["total"] == 3


def test_busca_similar_cargo_e_orgao(cliente):
    _, corpo = buscar(cliente, "cargo=%25ANAL%25&similar=true")
    assert corpo["total"] == 2
    _, corpo = buscar(cliente, "orgao=%25FAZENDA%25&similar=true")
    assert corpo["total"] == 1


def test_busca_similar_com_coringa(cliente):
    resposta, corpo = buscar(cliente, "nome=%25MARIA%25&similar=true")
    assert resposta.status_code == 200
    assert [linha["nome"] for linha in corpo["data"]] == ["MARIA SOUZA"]


def test_filtro_cargo(cliente):
    _, corpo = buscar(cliente, "cargo=AUDITOR")
    assert corpo["total"] == 1
    assert corpo["data"][0]["nome"] == "PEDRO ALVES"


def test_filtro_uf(cliente):
    _, corpo = buscar(cliente, "uf=rs")
    assert corpo["total"] == 2


def test_filtro_orgao(cliente):
    _, corpo = buscar(cliente, "orgao=MINISTERIO%20DA%20SAUDE")
    assert corpo["total"] == 23


def test_filtros_combinados(cliente):
    _, corpo = buscar(cliente, "uf=RS&cargo=ANALISTA")
    assert corpo["total"] == 1
    assert corpo["data"][0]["nome"] == "MARIA SOUZA"


def test_nome_sem_resultado_retorna_vazio(cliente):
    resposta, corpo = buscar(cliente, "nome=NINGUEM")
    assert resposta.status_code == 200
    assert corpo["data"] == []
    assert corpo["total"] == 0


def test_pagina_alem_do_total_retorna_vazio(cliente):
    resposta, corpo = buscar(cliente, "page=99")
    assert resposta.status_code == 200
    assert corpo["data"] == []
    assert corpo["total"] == 26


def test_uf_invalida(cliente):
    resposta, corpo = buscar(cliente, "uf=XX")
    assert resposta.status_code == 400
    assert "error" in corpo


def test_page_invalido(cliente):
    resposta, corpo = buscar(cliente, "page=abc")
    assert resposta.status_code == 400
    assert "error" in corpo


def test_similar_sem_nome(cliente):
    resposta, corpo = buscar(cliente, "similar=true")
    assert resposta.status_code == 400
    assert "error" in corpo


def test_injecao_sql_nao_retorna_tabela(cliente):
    resposta, corpo = buscar(cliente, "nome=%27%20OR%20%271%27%3D%271")
    assert resposta.status_code == 200
    assert corpo["data"] == []
    assert corpo["total"] == 0


def test_injecao_sql_em_similar(cliente):
    resposta, corpo = buscar(cliente, "nome=%27%20OR%20%271%27%3D%271&similar=true")
    assert resposta.status_code == 200
    assert corpo["total"] == 0


def test_paginacao_sem_repetir_nem_pular(cliente):
    _, primeira = buscar(cliente, "page=1&page_size=10")
    _, segunda = buscar(cliente, "page=2&page_size=10")
    ids_primeira = [linha["id"] for linha in primeira["data"]]
    ids_segunda = [linha["id"] for linha in segunda["data"]]
    assert len(ids_primeira) == 10
    assert len(ids_segunda) == 10
    assert not set(ids_primeira) & set(ids_segunda)
    assert ids_primeira + ids_segunda == sorted(ids_primeira + ids_segunda)
    assert primeira["total_pages"] == 3
