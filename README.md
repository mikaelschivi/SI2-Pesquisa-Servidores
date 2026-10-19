# Pesquisa de Servidores

Busca de servidores públicos federais (ativos e aposentados) com dados do [dados.gov.br](https://dados.gov.br), competência agosto/2026.

Stack: Postgres 16, Flask + Gunicorn, Vue 3 + Vite, tudo em Docker Compose.

## Como rodar

Precisa de Docker e Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Quando subir:

- Frontend: http://localhost:8080
- API: http://localhost:5000/api/servidores

A primeira subida demora porque o `loader` baixa os arquivos do dados.gov.br antes do backend iniciar. Ele termina sozinho com `carga concluida`.

Para parar: `docker compose down`. Para apagar também o banco: `docker compose down -v`.

## Serviços

| Serviço    | O que faz                                                                 |
|------------|---------------------------------------------------------------------------|
| `db`       | Postgres 16 (build de `db/`, aplica `schema.sql`). Tem healthcheck com `pg_isready`. |
| `loader`   | Roda uma vez. Cria a tabela, baixa os dados e carrega com `COPY`.         |
| `backend`  | API Flask na porta 5000. Só sobe depois que o `loader` termina com sucesso. |
| `frontend` | Build do Vue servido na porta 8080.                                       |

O `loader` faz `TRUNCATE` antes de inserir. Pode rodar de novo sem duplicar: `docker compose run --rm loader`.

## Variáveis de ambiente

No `.env`:

| Variável            | Para que serve        |
|---------------------|-----------------------|
| `POSTGRES_USER`     | Usuário do Postgres   |
| `POSTGRES_PASSWORD` | Senha do Postgres     |
| `POSTGRES_DB`       | Nome do banco         |

O compose monta o `DATABASE_URL` a partir dessas três. O `STATEMENT_TIMEOUT_MS` do backend é `5000` e fica no `docker-compose.yml`.

No frontend, a URL da API vem de `VITE_API_URL` em tempo de build. Sem ela, usa `http://localhost:5000`.

## API

`GET /api/servidores`

| Parâmetro   | Descrição                                                              |
|-------------|------------------------------------------------------------------------|
| `nome`      | Filtra por nome                                                        |
| `cargo`     | Filtra por cargo                                                       |
| `orgao`     | Filtra por órgão                                                       |
| `uf`        | Sigla do estado (ex.: `RS`). Só vale para ativos.                      |
| `similar`   | `true` ou `false` (padrão). `true` usa busca parcial, sem diferenciar maiúscula. |
| `page`      | Página, começa em 1 (padrão 1). Só na busca exata.                     |
| `page_size` | Itens por página, de 1 a 100 (padrão 20). Só na busca exata.           |
| `limit`     | Máximo de resultados, de 1 a 100 (padrão 100). Só na busca similar.    |

Regras:

- Busca exata compara o texto inteiro, sem diferenciar maiúscula. Tem paginação.
- Busca similar exige pelo menos um entre `nome`, `cargo` e `orgao`. Não tem paginação, volta uma página só.
- Limite de 20 requisições por minuto por IP.
- Consultas acima de 5 segundos são canceladas.
- CORS liberado só para `http://localhost:8080`.

Exemplo:

```bash
curl "http://localhost:5000/api/servidores?nome=ana&similar=true&uf=SP"
```

Resposta:

```json
{
  "data": [{"id": 1, "nome": "ANA LIMA", "cargo": "ANALISTA", "orgao": "MINISTERIO DA FAZENDA", "uf": "SP", "situacao": "ativo"}],
  "page": 1,
  "page_size": 100,
  "total": 1,
  "total_pages": 1
}
```

Erros voltam em JSON, sem stack trace: `{"error": "mensagem"}`. Códigos: `400` parâmetro inválido, `429` limite estourado, `504` consulta lenta, `500` erro interno.

## Testes

Os testes do backend usam um Postgres descartável. Eles apagam e recriam a tabela `servidores`, então **não aponte para o banco real**.

```bash
# Postgres de teste
docker run --rm -d --name pg-teste -p 5433:5432 -e POSTGRES_PASSWORD=teste postgres:16-alpine

# dependências e testes
cd backend
pip install -r requirements.txt
TEST_DATABASE_URL=postgresql+psycopg2://postgres:teste@localhost:5433/postgres pytest

# limpar
docker stop pg-teste
```

Sem `TEST_DATABASE_URL`, os testes são ignorados.

## Estrutura

```
backend/    API Flask, script de carga (carregar.py) e testes
frontend/   App Vue 3 com Vite
db/         Dockerfile do Postgres e schema.sql (criado na primeira subida)
docker-compose.yml
.env.example
```

## Observações

- O backend roda com 1 worker e 8 threads. O rate limiter fica em memória, então mais de um processo quebraria o limite.
- Os dados vêm de `repositorio.dados.gov.br`. Se o site estiver fora do ar, o `loader` tenta 5 vezes e falha, e o backend não sobe.
- Aposentados não têm UF na fonte, então o filtro por UF não retorna aposentados.
