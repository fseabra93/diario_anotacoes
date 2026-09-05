-- ==============================================================================
-- PROJETO: DIÁRIO DE ANOTAÇÕES PESSOAL
-- ARQUIVO: 02_dados_teste.sql
-- DESCRIÇÃO: Carga de dados de teste realistas para validação de integridade,
--            relacionamentos N:N, filtros estruturados e busca textual FTS.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CADASTRO DE PESSOAS
-- ------------------------------------------------------------------------------
INSERT INTO pessoa (nome, observacoes) VALUES
('João Silva', 'Diretor Comercial da Distribuidora Alfa - fornecedor de peças e insumos.'),
('Maria Oliveira', 'Gerente de TI e líder técnica do time de desenvolvimento.'),
('Carlos Souza', 'Advogado corporativo e consultor em licitações e contratos públicos.'),
('Ana Costa', 'Supervisora financeira responsável pelo fluxo de caixa e pagamentos.');

-- ------------------------------------------------------------------------------
-- 2. CADASTRO DE ASSUNTOS (Independentes)
-- ------------------------------------------------------------------------------
INSERT INTO assunto (nome) VALUES
('Projeto X'),
('Licitação Y'),
('Contrato Fornecedor'),
('Orçamento Anual'),
('Infraestrutura de TI');

-- ------------------------------------------------------------------------------
-- 3. CADASTRO DE KEYWORDS (Independentes)
-- ------------------------------------------------------------------------------
INSERT INTO keyword (nome) VALUES
('licitação'),
('contrato'),
('fornecedor'),
('projeto x'),
('prazo'),
('atraso'),
('pagamento'),
('orçamento'),
('urgente');

-- ------------------------------------------------------------------------------
-- 4. CADASTRO DE CONVERSAS
-- ------------------------------------------------------------------------------

-- Conversa 1: João Silva (Fornecedor, atraso de entrega)
INSERT INTO conversa (data_hora, id_pessoa, titulo, resumo, conteudo) VALUES
(
    '2026-02-15 14:30:00-03',
    (SELECT id_pessoa FROM pessoa WHERE nome = 'João Silva'),
    'Reunião sobre atraso na entrega de insumos',
    'Discussão sobre atraso crítico do lote de materiais e renegociação do prazo de entrega.',
    'Reunião com João Silva da Distribuidora Alfa. O fornecedor não entregou material no prazo acordado de 10 de fevereiro devido a uma paralisação na transportadora parceira. Ficou acordado formalmente que uma nova remessa expressa será despachada com prioridade máxima até o dia 20 de fevereiro. Caso haja novo atraso, haverá notificação formal e aplicação de multa contratual de 5% conforme estipulado na cláusula 7 do contrato vigente.'
),

-- Conversa 2: Carlos Souza (Licitação Y e parecer jurídico)
(
    '2026-02-22 10:00:00-03',
    (SELECT id_pessoa FROM pessoa WHERE nome = 'Carlos Souza'),
    'Parecer jurídico sobre edital da Licitação Y',
    'Revisão técnica das cláusulas de habilitação jurídica e econômico-financeira.',
    'Conversa por videoconferência com Dr. Carlos Souza para sanar dúvidas quanto aos critérios de qualificação técnica da Licitação Y. Analisamos os riscos de impugnação por parte de concorrentes e ajustamos a redação do item referente ao patrimônio líquido mínimo. O edital final está juridicamente seguro e liberado para publicação oficial no Diário Oficial.'
),

-- Conversa 3: Maria Oliveira (Status do Projeto X)
(
    '2026-03-01 16:00:00-03',
    (SELECT id_pessoa FROM pessoa WHERE nome = 'Maria Oliveira'),
    'Alinhamento de cronograma e metas do Projeto X',
    'Revisão do roadmap da sprint de março e levantamento de gargalos em infraestrutura.',
    'Reunião presencial com Maria Oliveira. Avaliamos o progresso do Projeto X. As entregas do módulo de relatórios e autenticação estão adiantadas, porém o ambiente de homologação está apresentando lentidão devido à infraestrutura de banco de dados. Maria solicitou a contratação temporária de um especialista em tuning de banco de dados para garantir que a entrega final ocorra dentro do prazo previsto para abril.'
),

-- Conversa 4: Ana Costa (Pagamento de fornecedores e fluxo de caixa)
(
    '2026-03-03 11:15:00-03',
    (SELECT id_pessoa FROM pessoa WHERE nome = 'Ana Costa'),
    'Fluxo de caixa de março e liberação de pagamentos',
    'Análise de desembolsos da quinzena e contingência de verba para fornecedores.',
    'Reunião com Ana Costa do setor financeiro. Revisamos as contas a pagar e autorizamos a liquidação das faturas do fornecedor de TI e da Distribuidora Alfa. Ana alertou que o orçamento anual está com 40% comprometido no primeiro trimestre, recomendando cautela com novos contratos ou aditivos nos próximos meses.'
);

-- ------------------------------------------------------------------------------
-- 5. RELACIONAMENTO: CONVERSA_ASSUNTO (N:N)
-- ------------------------------------------------------------------------------

-- Conversa 1 (Insumos João): 'Contrato Fornecedor' e 'Projeto X'
INSERT INTO conversa_assunto (id_conversa, id_assunto)
SELECT c.id_conversa, a.id_assunto
FROM conversa c, assunto a
WHERE c.titulo = 'Reunião sobre atraso na entrega de insumos'
  AND a.nome IN ('Contrato Fornecedor', 'Projeto X');

-- Conversa 2 (Licitação Carlos): 'Licitação Y'
INSERT INTO conversa_assunto (id_conversa, id_assunto)
SELECT c.id_conversa, a.id_assunto
FROM conversa c, assunto a
WHERE c.titulo = 'Parecer jurídico sobre edital da Licitação Y'
  AND a.nome IN ('Licitação Y');

-- Conversa 3 (Projeto X Maria): 'Projeto X' e 'Infraestrutura de TI'
INSERT INTO conversa_assunto (id_conversa, id_assunto)
SELECT c.id_conversa, a.id_assunto
FROM conversa c, assunto a
WHERE c.titulo = 'Alinhamento de cronograma e metas do Projeto X'
  AND a.nome IN ('Projeto X', 'Infraestrutura de TI');

-- Conversa 4 (Finanças Ana): 'Orçamento Anual' e 'Contrato Fornecedor'
INSERT INTO conversa_assunto (id_conversa, id_assunto)
SELECT c.id_conversa, a.id_assunto
FROM conversa c, assunto a
WHERE c.titulo = 'Revisão do fluxo de caixa e liberação de pagamentos'
  AND a.nome IN ('Orçamento Anual', 'Contrato Fornecedor');

-- ------------------------------------------------------------------------------
-- 6. RELACIONAMENTO: CONVERSA_KEYWORD (N:N)
-- ------------------------------------------------------------------------------

-- Conversa 1 (Insumos João): fornecedor, atraso, prazo, contrato, urgente
INSERT INTO conversa_keyword (id_conversa, id_keyword)
SELECT c.id_conversa, k.id_keyword
FROM conversa c, keyword k
WHERE c.titulo = 'Reunião sobre atraso na entrega de insumos'
  AND k.nome IN ('fornecedor', 'atraso', 'prazo', 'contrato', 'urgente');

-- Conversa 2 (Licitação Carlos): licitação, contrato, prazo
INSERT INTO conversa_keyword (id_conversa, id_keyword)
SELECT c.id_conversa, k.id_keyword
FROM conversa c, keyword k
WHERE c.titulo = 'Parecer jurídico sobre edital da Licitação Y'
  AND k.nome IN ('licitação', 'contrato', 'prazo');

-- Conversa 3 (Projeto X Maria): projeto x, prazo
INSERT INTO conversa_keyword (id_conversa, id_keyword)
SELECT c.id_conversa, k.id_keyword
FROM conversa c, keyword k
WHERE c.titulo = 'Alinhamento de cronograma e metas do Projeto X'
  AND k.nome IN ('projeto x', 'prazo');

-- Conversa 4 (Finanças Ana): fornecedor, pagamento, orçamento, contrato
INSERT INTO conversa_keyword (id_conversa, id_keyword)
SELECT c.id_conversa, k.id_keyword
FROM conversa c, keyword k
WHERE c.titulo = 'Revisão do fluxo de caixa e liberação de pagamentos'
  AND k.nome IN ('fornecedor', 'pagamento', 'orçamento', 'contrato');

