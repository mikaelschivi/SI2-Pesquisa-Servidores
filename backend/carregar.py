import csv
import http.client
import io
import itertools
import os
import time
import urllib.request

import psycopg2

BASE = "https://repositorio.dados.gov.br/segrt"
CARREIRAS = BASE + "/Cargos%20e%20Carreiras/2026/CARREIRA_082026.txt"
APOSENTADOS = BASE + "/Aposentados/2026/APOSENTADOS_082026.csv"


def baixar(url):
    for tentativa in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as resposta:
                return resposta.read().decode("latin-1")
        except (OSError, http.client.HTTPException):
            if tentativa == 4:
                raise
            time.sleep(10)


def ativos(texto):
    for i, r in enumerate(csv.reader(io.StringIO(texto), delimiter=";")):
        if i < 2 or len(r) < 8 or not r[0].strip():
            continue
        uf = r[4].strip()
        yield [r[0].strip(), r[3].strip(), r[5].strip(), uf if len(uf) == 2 else "", "ativo"]


def aposentados(texto):
    for r in csv.reader(io.StringIO(texto), delimiter=";"):
        if len(r) < 7 or not r[0].strip():
            continue
        yield [r[0].strip(), r[6].strip(), r[3].strip(), "", "aposentado"]


def main():
    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg2://", "postgresql://")
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerows(itertools.chain(ativos(baixar(CARREIRAS)), aposentados(baixar(APOSENTADOS))))
    buffer.seek(0)
    with psycopg2.connect(url) as conexao, conexao.cursor() as cursor:
        cursor.execute("TRUNCATE servidores RESTART IDENTITY")
        cursor.copy_expert(
            "COPY servidores (nome, cargo, orgao, uf, situacao) FROM STDIN WITH CSV", buffer
        )
    print("carga concluida")


if __name__ == "__main__":
    main()
