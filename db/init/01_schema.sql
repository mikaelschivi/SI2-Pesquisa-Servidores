CREATE TABLE servidores (
    id       SERIAL PRIMARY KEY,
    nome     TEXT NOT NULL,
    cargo    TEXT,
    orgao    TEXT,
    uf       CHAR(2),
    situacao TEXT NOT NULL CHECK (situacao IN ('ativo', 'aposentado'))
);
