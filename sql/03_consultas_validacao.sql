-- ==============================================================================
-- PROJETO: DIÁRIO DE ANOTAÇÕES PESSOAL
-- ARQUIVO: 03_consultas_validacao.sql
-- DESCRIÇÃO: Bateria de testes e consultas no SQL Editor do Supabase para
--            validar o modelo relacional, integridade, filtros e Full Text Search.
-- ==============================================================================

-- ==============================================================================
-- PARTE 1: CONSULTAS ESTRUTURADAS
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1.1 TODAS AS CONVERSAS COM UMA PESSOA (ex: "João Silva")
-- Retorna os dados da conversa com a lista agregada de assuntos e keywords.
-- ------------------------------------------------------------------------------
SELECT 
    c.id_conversa,
    c.data_hora,
    p.nome AS pessoa,
    c.titulo,
    c.resumo,
    COALESCE(string_agg(DISTINCT a.nome, ', ' ORDER BY a.nome), 'Nenhum') AS assuntos,
    COALESCE(string_agg(DISTINCT k.nome, ', ' ORDER BY k.nome), 'Nenhum') AS keywords
FROM conversa c
INNER JOIN pessoa p ON p.id_pessoa = c.id_pessoa
LEFT JOIN conversa_assunto ca ON ca.id_conversa = c.id_conversa
LEFT JOIN assunto a ON a.id_assunto = ca.id_assunto
LEFT JOIN conversa_keyword ck ON ck.id_conversa = c.id_conversa
LEFT JOIN keyword k ON k.id_keyword = ck.id_keyword
WHERE p.nome ILIKE '%João Silva%'
GROUP BY c.id_conversa, c.data_hora, p.nome, c.titulo, c.resumo
ORDER BY c.data_hora DESC;

-- ------------------------------------------------------------------------------
-- 1.2 TODAS AS CONVERSAS POR ASSUNTO ESPECÍFICO (ex: "Projeto X")
-- Demonstra navegação N:N via tabela associativa conversa_assunto.
-- ------------------------------------------------------------------------------
SELECT 
    c.id_conversa,
    c.data_hora,
    p.nome AS pessoa,
    c.titulo,
    c.resumo,
    a_filtro.nome AS assunto_filtrado
FROM conversa c
INNER JOIN pessoa p ON p.id_pessoa = c.id_pessoa
INNER JOIN conversa_assunto ca ON ca.id_conversa = c.id_conversa
INNER JOIN assunto a_filtro ON a_filtro.id_assunto = ca.id_assunto
WHERE a_filtro.nome = 'Projeto X'
ORDER BY c.data_hora DESC;

-- ------------------------------------------------------------------------------
-- 1.3 TODAS AS CONVERSAS POR KEYWORD (ex: "fornecedor")
-- Demonstra navegação N:N via tabela associativa conversa_keyword.
-- ------------------------------------------------------------------------------
SELECT 
    c.id_conversa,
    c.data_hora,
    p.nome AS pessoa,
    c.titulo,
    c.resumo,
    k_filtro.nome AS keyword_filtrada
FROM conversa c
INNER JOIN pessoa p ON p.id_pessoa = c.id_pessoa
INNER JOIN conversa_keyword ck ON ck.id_conversa = c.id_conversa
INNER JOIN keyword k_filtro ON k_filtro.id_keyword = ck.id_keyword
WHERE k_filtro.nome = 'fornecedor'
ORDER BY c.data_hora DESC;

-- ------------------------------------------------------------------------------
-- 1.4 CONVERSAS POR INTERVALO DE DATAS (ex: Fevereiro de 2026)
-- Utiliza o índice B-tree idx_conversa_data_hora.
-- ------------------------------------------------------------------------------
SELECT 
    c.id_conversa,
    c.data_hora,
    p.nome AS pessoa,
    c.titulo,
    c.resumo
FROM conversa c
INNER JOIN pessoa p ON p.id_pessoa = c.id_pessoa
WHERE c.data_hora >= '2026-02-01 00:00:00-03' 
  AND c.data_hora <  '2026-03-01 00:00:00-03'
ORDER BY c.data_hora ASC;

-- ==============================================================================
-- PARTE 2: FULL TEXT SEARCH (FTS) NO POSTGRESQL
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 2.1 BUSCA TEXTUAL ESPECIFICADA NO REQUISITO:
-- "fornecedor não entregou material"
-- 
-- Utiliza websearch_to_tsquery com o dicionário 'portuguese'.
-- O PostgreSQL remove stop words ("não") e aplica stemming às raízes das palavras
-- (ex: "entregou" -> raiz "entreg"). Localiza a Conversa 1 instantaneamente via índice GIN.
-- ------------------------------------------------------------------------------
SELECT 
    c.id_conversa,
    c.data_hora,
    p.nome AS pessoa,
    c.titulo,
    c.resumo,
    ts_rank(c.busca_vetor, query) AS pontuacao_relevancia
FROM conversa c
INNER JOIN pessoa p ON p.id_pessoa = c.id_pessoa,
websearch_to_tsquery('portuguese', 'fornecedor não entregou material') query
WHERE c.busca_vetor @@ query
ORDER BY pontuacao_relevancia DESC;

-- ------------------------------------------------------------------------------
-- 2.2 BUSCA COM HIGHLIGHT/DESTAQUE DO TRECHO ENCONTRADO (ts_headline)
-- Muito útil para a interface Streamlit mostrar onde o termo foi achado no texto longo.
-- ------------------------------------------------------------------------------
SELECT 
    c.id_conversa,
    p.nome AS pessoa,
    c.titulo,
    ts_headline(
        'portuguese', 
        c.conteudo, 
        query, 
        'StartSel = <mark>, StopSel = </mark>, MaxWords=35, MinWords=15'
    ) AS trecho_destacado
FROM conversa c
INNER JOIN pessoa p ON p.id_pessoa = c.id_pessoa,
websearch_to_tsquery('portuguese', 'edital licitação') query
WHERE c.busca_vetor @@ query;

-- ==============================================================================
-- PARTE 3: TESTES DE INTEGRIDADE, TRIGGERS E REGRAS DE NEGÓCIO
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 3.1 TESTE DO TRIGGER 'atualizado_em'
-- Ao atualizar uma conversa, o campo 'atualizado_em' deve ser atualizado para now().
-- ------------------------------------------------------------------------------
-- Passo A: Verificar timestamp atual
SELECT id_conversa, criado_em, atualizado_em 
FROM conversa 
WHERE titulo = 'Alinhamento de cronograma e metas do Projeto X';

-- Passo B: Fazer um update
UPDATE conversa 
SET resumo = 'Revisão do roadmap e alocação confirmada de especialista em banco de dados.'
WHERE titulo = 'Alinhamento de cronograma e metas do Projeto X';

-- Passo C: Verificar que atualizado_em mudou e é superior a criado_em
SELECT id_conversa, criado_em, atualizado_em 
FROM conversa 
WHERE titulo = 'Alinhamento de cronograma e metas do Projeto X';

-- ------------------------------------------------------------------------------
-- 3.2 TESTE DE INTEGRIDADE REFERENCIAL: ON DELETE RESTRICT
-- Tentar excluir a pessoa 'João Silva' que possui conversas vinculadas.
-- RESULTADO ESPERADO: O banco deve RECUSAR com erro de violação de chave estrangeira!
-- (Descomente para testar no SQL Editor):
-- ------------------------------------------------------------------------------
-- DELETE FROM pessoa WHERE nome = 'João Silva';
-- ERROR: update or delete on table "pessoa" violates foreign key constraint "conversa_id_pessoa_fkey" on table "conversa"

-- ------------------------------------------------------------------------------
-- 3.3 TESTE DE EXCLUSÃO EM CASCATA NAS TABELAS ASSOCIATIVAS: ON DELETE CASCADE
-- Ao excluir uma conversa, os vínculos em conversa_assunto e conversa_keyword
-- devem ser limpos automaticamente, mantendo as tabelas assunto e keyword intactas.
-- ------------------------------------------------------------------------------
DO $$
DECLARE
    v_id_conversa BIGINT;
    v_qtd_assuntos INT;
    v_qtd_keywords INT;
BEGIN
    -- 1. Inserir conversa temporária de teste
    INSERT INTO conversa (id_pessoa, titulo, conteudo)
    VALUES (
        (SELECT id_pessoa FROM pessoa LIMIT 1),
        'Conversa Temporária para Teste de Exclusão',
        'Conteúdo temporário para teste de cascata.'
    ) RETURNING id_conversa INTO v_id_conversa;

    -- 2. Associar assunto e keyword
    INSERT INTO conversa_assunto (id_conversa, id_assunto)
    VALUES (v_id_conversa, (SELECT id_assunto FROM assunto LIMIT 1));

    INSERT INTO conversa_keyword (id_conversa, id_keyword)
    VALUES (v_id_conversa, (SELECT id_keyword FROM keyword LIMIT 1));

    -- 3. Excluir a conversa
    DELETE FROM conversa WHERE id_conversa = v_id_conversa;

    -- 4. Verificar se sobrou algum vínculo órfão
    SELECT COUNT(*) INTO v_qtd_assuntos FROM conversa_assunto WHERE id_conversa = v_id_conversa;
    SELECT COUNT(*) INTO v_qtd_keywords FROM conversa_keyword WHERE id_conversa = v_id_conversa;

    IF v_qtd_assuntos = 0 AND v_qtd_keywords = 0 THEN
        RAISE NOTICE 'SUCESSO: ON DELETE CASCADE removeu perfeitamente os registros associativos!';
    ELSE
        RAISE EXCEPTION 'FALHA: Registros associativos órfãos foram encontrados!';
    END IF;
END $$;

