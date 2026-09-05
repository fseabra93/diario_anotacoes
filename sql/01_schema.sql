-- ==============================================================================
-- PROJETO: DIÁRIO DE ANOTAÇÕES PESSOAL
-- ARQUIVO: 01_schema.sql
-- DESCRIÇÃO: Definição de tabelas, chaves primárias e estrangeiras, constraints,
--            gatilhos de timestamp, coluna gerada para Full Text Search (FTS)
--            e índices de performance (B-tree e GIN).
-- COMPATIBILIDADE: PostgreSQL 14+ (Supabase)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. LIMPEZA PREVENTIVA (OPCIONAL - Útil para reset completo do banco se necessário)
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS conversa_keyword CASCADE;
DROP TABLE IF EXISTS conversa_assunto CASCADE;
DROP TABLE IF EXISTS conversa CASCADE;
DROP TABLE IF EXISTS keyword CASCADE;
DROP TABLE IF EXISTS assunto CASCADE;
DROP TABLE IF EXISTS pessoa CASCADE;
DROP FUNCTION IF EXISTS fn_atualizar_timestamp CASCADE;

-- ------------------------------------------------------------------------------
-- 2. FUNÇÃO E TRIGGER PARA ATUALIZAÇÃO AUTOMÁTICA DE 'atualizado_em'
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = timezone('utc', now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- 3. TABELA: PESSOA
-- Representa as pessoas com quem as conversas/anotações ocorreram.
-- ------------------------------------------------------------------------------
CREATE TABLE pessoa (
    id_pessoa BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(255) NOT NULL CHECK (length(trim(nome)) > 0),
    observacoes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE TRIGGER trg_pessoa_atualizado_em
    BEFORE UPDATE ON pessoa
    FOR EACH ROW
    EXECUTE FUNCTION fn_atualizar_timestamp();

-- ------------------------------------------------------------------------------
-- 4. TABELA: ASSUNTO
-- Entidade independente para categorias/tópicos abordados nas conversas.
-- ------------------------------------------------------------------------------
CREATE TABLE assunto (
    id_assunto BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE CHECK (length(trim(nome)) > 0),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ------------------------------------------------------------------------------
-- 5. TABELA: KEYWORD
-- Entidade independente para tags e palavras-chave de busca e indexação.
-- ------------------------------------------------------------------------------
CREATE TABLE keyword (
    id_keyword BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE CHECK (length(trim(nome)) > 0),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- ------------------------------------------------------------------------------
-- 6. TABELA: CONVERSA
-- Tabela central do diário. Armazena o registro completo de cada conversa.
-- Inclui coluna tsvector gerada automaticamente com dicionário em português.
-- ------------------------------------------------------------------------------
CREATE TABLE conversa (
    id_conversa BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_hora TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    id_pessoa BIGINT NOT NULL REFERENCES pessoa(id_pessoa) ON DELETE RESTRICT,
    titulo VARCHAR(255) NOT NULL CHECK (length(trim(titulo)) > 0),
    resumo TEXT,
    conteudo TEXT NOT NULL CHECK (length(trim(conteudo)) > 0),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    
    -- Full Text Search: Coluna vetorial gerada e mantida automaticamente pelo PostgreSQL
    -- Pesos: 'A' para título (maior relevância), 'B' para resumo, 'C' para conteúdo
    busca_vetor tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('portuguese', coalesce(titulo, '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(resumo, '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(conteudo, '')), 'C')
    ) STORED
);

CREATE TRIGGER trg_conversa_atualizado_em
    BEFORE UPDATE ON conversa
    FOR EACH ROW
    EXECUTE FUNCTION fn_atualizar_timestamp();

-- ------------------------------------------------------------------------------
-- 7. TABELA ASSOCIATIVA: CONVERSA_ASSUNTO (N:N)
-- Relaciona uma conversa a múltiplos assuntos.
-- ------------------------------------------------------------------------------
CREATE TABLE conversa_assunto (
    id_conversa BIGINT NOT NULL REFERENCES conversa(id_conversa) ON DELETE CASCADE,
    id_assunto BIGINT NOT NULL REFERENCES assunto(id_assunto) ON DELETE CASCADE,
    PRIMARY KEY (id_conversa, id_assunto)
);

-- ------------------------------------------------------------------------------
-- 8. TABELA ASSOCIATIVA: CONVERSA_KEYWORD (N:N)
-- Relaciona uma conversa a múltiplas keywords.
-- ------------------------------------------------------------------------------
CREATE TABLE conversa_keyword (
    id_conversa BIGINT NOT NULL REFERENCES conversa(id_conversa) ON DELETE CASCADE,
    id_keyword BIGINT NOT NULL REFERENCES keyword(id_keyword) ON DELETE CASCADE,
    PRIMARY KEY (id_conversa, id_keyword)
);

-- ------------------------------------------------------------------------------
-- 9. ÍNDICES DE DESEMPENHO
-- ------------------------------------------------------------------------------

-- Índice GIN para busca Full Text Search ultrarrápida
CREATE INDEX idx_conversa_busca_vetor ON conversa USING GIN (busca_vetor);

-- Índices B-tree para filtros temporais e por chave estrangeira
CREATE INDEX idx_conversa_data_hora ON conversa(data_hora DESC);
CREATE INDEX idx_conversa_id_pessoa ON conversa(id_pessoa);

-- Índices B-tree para junções reversas nas tabelas associativas
CREATE INDEX idx_conversa_assunto_id_assunto ON conversa_assunto(id_assunto);
CREATE INDEX idx_conversa_keyword_id_keyword ON conversa_keyword(id_keyword);

-- Índices funcionais em lower(nome) para agilizar buscas textuais e autocompletes
CREATE INDEX idx_pessoa_nome ON pessoa(lower(nome));
CREATE INDEX idx_assunto_nome ON assunto(lower(nome));
CREATE INDEX idx_keyword_nome ON keyword(lower(nome));

