# Relatório do líder técnico

> Rascunho baseado no histórico do git. O líder técnico deve revisar e completar.

## Divisão de trabalho (conforme commits)

| Desenvolvedor | Áreas |
|---|---|
| jcesar-fx | Schema da tabela, download dos dados do dados.gov.br, configuração e Dockerfile do frontend |
| Vinícius Martins Borges | API de busca com validação, testes de backend, componente de busca e tabela, ponto de entrada do frontend |
| mikael | Dockerfile e requirements do backend, docker-compose, setup do banco via Docker, README, .gitignore e .env.example |

Commits completos: `git log`. Gráfico: [burndown.png](burndown.png), gerado por [burndown.ipynb](burndown.ipynb).

## Pontos fortes

- Divisão clara por camada (dados, backend, frontend, infraestrutura).
- Testes de backend com pytest contra Postgres real, incluindo casos de injeção SQL.
- Subida completa com um comando (`docker compose up --build`), com healthcheck e carga automática.
- Mensagens de commit no padrão convencional.

## Pontos fracos

- Backend e frontend desenvolvimento começou tarde, concentrou o trabalho no fim do prazo como mostra o gráfico de burndown.
- Frontend sem testes, backend sem muitos testes de ponta a ponta.
- Esquema da tabela duplicado em `db/schema.sql` e `backend/carregar.py`.

## Principais dificuldades e impedimentos

> Preencher com a experiência real da equipe. Pontos que o histórico sugere:

- Fonte de dados externa (`repositorio.dados.gov.br`) instável: o `loader` precisou de tentativas repetidas.
- Volume grande (cerca de 1,09 milhão de registros), exigindo carga com `COPY`, limite de tempo de consulta e paginação.
- Mudança do setup do banco de script para Docker direto (18/10).
- Aposentados não têm UF na fonte, então o filtro por UF não os retorna.
