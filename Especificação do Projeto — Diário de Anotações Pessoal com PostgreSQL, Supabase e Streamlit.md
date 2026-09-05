PROJETO: DIÁRIO DE ANOTAÇÕES PESSOAL

VERSÃO DO CONTEXTO: 1.0
DATA: 05/09/2026

============================================================
1. OBJETIVO DO PROJETO
============================================================

Criar uma aplicação pessoal de diário de anotações que permita registrar e posteriormente localizar facilmente informações sobre conversas e acontecimentos.

O foco principal é registrar conversas com pessoas, permitindo armazenar:

- data e hora;
- pessoa envolvida;
- assunto(s);
- resumo;
- conteúdo completo da conversa/anotação;
- keywords/palavras-chave.

A aplicação deverá permitir pesquisar e filtrar os registros de forma eficiente.

O projeto deve priorizar:

- simplicidade de uso;
- organização dos dados;
- boa capacidade de pesquisa;
- independência de um formato proprietário;
- facilidade de backup;
- facilidade de exportação;
- possibilidade de evolução futura com recursos de Inteligência Artificial.

============================================================
2. TECNOLOGIAS ESCOLHIDAS
============================================================

Banco de dados:
- PostgreSQL hospedado gratuitamente no Supabase.

Backend/aplicação:
- Python.

Interface:
- Streamlit.

Banco de dados:
- Supabase PostgreSQL.

Exportação:
- CSV.
- JSON.

Backup:
- Backup independente do banco, além dos mecanismos eventualmente disponíveis no Supabase.

Possibilidade futura:
- integração com modelos de IA para geração automática de resumos e keywords.

============================================================
3. DECISÕES DE ARQUITETURA
============================================================

O banco será relacional e deverá seguir boas práticas de normalização, especialmente até a Terceira Forma Normal (3FN), sem realizar normalização excessiva que prejudique a simplicidade da aplicação.

A estrutura básica será:

PESSOA
   |
   | 1:N
   |
CONVERSA
   |
   +------ N:N ------ ASSUNTO
   |
   +------ N:N ------ KEYWORD


============================================================
4. MODELO DE DADOS
============================================================

4.1 TABELA PESSOA

Representa as pessoas relacionadas às conversas.

Campos previstos:

- id_pessoa — chave primária
- nome
- observacoes

Possíveis campos futuros:
- apelido
- contato
- empresa/organização
- outras informações não sensíveis

O cadastro de pessoas deverá ser independente das conversas.

Uma pessoa poderá estar relacionada a várias conversas.

Relacionamento:

PESSOA 1:N CONVERSA


------------------------------------------------------------
4.2 TABELA CONVERSA
------------------------------------------------------------

Representa cada registro do diário.

Campos previstos:

- id_conversa — chave primária
- data_hora
- id_pessoa — chave estrangeira para PESSOA
- titulo
- resumo
- conteudo
- criado_em
- atualizado_em

O campo RESUMO NÃO precisa ser colocado em uma tabela separada para atender à 3FN.

O resumo é um atributo da própria conversa:

id_conversa -> resumo

Assim, enquanto existir apenas um resumo associado àquela conversa, ele pode permanecer diretamente na tabela CONVERSA.

Uma tabela separada RESUMO_CONVERSA somente deverá ser considerada se futuramente houver necessidade de armazenar:

- múltiplos resumos;
- versões históricas do resumo;
- resumos gerados por diferentes modelos de IA;
- data de geração;
- modelo utilizado;
- outras informações específicas sobre cada resumo.


------------------------------------------------------------
4.3 TABELA ASSUNTO
------------------------------------------------------------

Representa assuntos cadastrados no sistema.

Campos previstos:

- id_assunto — chave primária
- nome

Os assuntos devem ser entidades independentes.

Uma conversa poderá ter mais de um assunto.

Por isso, o relacionamento será N:N.

Exemplo:

CONVERSA:
"Conversa com João em que falamos sobre o projeto X e sobre a licitação Y."

ASSUNTOS:
- Projeto X
- Licitação Y


------------------------------------------------------------
4.4 TABELA CONVERSA_ASSUNTO
------------------------------------------------------------

Tabela associativa entre CONVERSA e ASSUNTO.

Campos:

- id_conversa — FK
- id_assunto — FK

A chave primária deverá ser composta por:

(id_conversa, id_assunto)

Relacionamento:

CONVERSA N:N ASSUNTO


------------------------------------------------------------
4.5 TABELA KEYWORD
------------------------------------------------------------

Representa palavras-chave cadastradas.

Campos previstos:

- id_keyword — chave primária
- nome

Keywords deverão ser armazenadas separadamente, e não como uma lista de palavras dentro da tabela CONVERSA.

Isso evita problemas de atomicidade e facilita consultas.

Exemplo:

KEYWORD

1 | licitação
2 | contrato
3 | fornecedor
4 | projeto X


------------------------------------------------------------
4.6 TABELA CONVERSA_KEYWORD
------------------------------------------------------------

Tabela associativa entre CONVERSA e KEYWORD.

Campos:

- id_conversa — FK
- id_keyword — FK

Chave primária composta:

(id_conversa, id_keyword)

Relacionamento:

CONVERSA N:N KEYWORD


============================================================
5. ESTRUTURA CONCEITUAL DO BANCO
============================================================

PESSOA
------
id_pessoa PK
nome
observacoes

       |
       | 1:N
       v

CONVERSA
--------
id_conversa PK
data_hora
id_pessoa FK
titulo
resumo
conteudo
criado_em
atualizado_em

       |
       | N:N
       |
       +--------------------+
       |                    |
       v                    v

CONVERSA_ASSUNTO       CONVERSA_KEYWORD
----------------       -----------------
id_conversa PK/FK      id_conversa PK/FK
id_assunto PK/FK       id_keyword PK/FK
       |                    |
       v                    v

ASSUNTO                KEYWORD
-------                -------
id_assunto PK          id_keyword PK
nome                   nome


============================================================
6. BUSCA TEXTUAL
============================================================

A aplicação deverá possuir dois tipos diferentes de pesquisa.

6.1 PESQUISA ESTRUTURADA

Pesquisa através de:

- pessoa;
- assunto;
- keyword;
- intervalo de datas.

Exemplos:

"Todas as conversas com João."

"Todas as conversas sobre licitação."

"Todas as conversas que possuem a keyword fornecedor."

"Conversas com João entre janeiro e março de 2026."


6.2 BUSCA TEXTUAL

Também deverá existir busca dentro do conteúdo das conversas.

A busca deverá considerar, inicialmente:

- titulo;
- resumo;
- conteudo.

Deve-se utilizar os recursos de Full Text Search do PostgreSQL sempre que apropriado.

Exemplo de pesquisa:

"fornecedor não entregou material"

A aplicação deverá conseguir localizar conversas cujo conteúdo tenha relação com esses termos, mesmo que o usuário não esteja filtrando especificamente por pessoa ou assunto.


============================================================
7. ÍNDICES E RESTRIÇÕES
============================================================

Deverão ser criados índices apropriados para melhorar o desempenho.

Inicialmente considerar índices para:

- CONVERSA.data_hora
- CONVERSA.id_pessoa
- PESSOA.nome
- ASSUNTO.nome
- KEYWORD.nome

Também deverão ser criadas restrições UNIQUE onde fizer sentido.

Por exemplo:

PESSOA.nome
ASSUNTO.nome
KEYWORD.nome

A implementação final deverá avaliar se nomes de pessoas precisam ser únicos ou se pode haver pessoas com o mesmo nome.

As tabelas associativas deverão possuir chave primária composta.

As chaves estrangeiras deverão possuir as restrições adequadas.


============================================================
8. ORDEM DE IMPLEMENTAÇÃO
============================================================

O projeto deverá ser desenvolvido na seguinte ordem.

ETAPA 1 — Criar o projeto PostgreSQL no Supabase

Criar um projeto gratuito no Supabase.

Não criar as tabelas manualmente pela interface.

Preferir criar toda a estrutura através de SQL no SQL Editor do Supabase, para que a estrutura seja reproduzível e facilmente documentada.


ETAPA 2 — Criar as tabelas e relacionamentos

Criar:

- pessoa
- conversa
- assunto
- conversa_assunto
- keyword
- conversa_keyword

Criar:

- PKs;
- FKs;
- relacionamentos;
- constraints.


ETAPA 3 — Criar índices e restrições

Criar índices para os campos utilizados frequentemente em pesquisa.

Criar UNIQUEs e outras constraints necessárias.


ETAPA 4 — Implementar busca textual

Utilizar recursos nativos do PostgreSQL para Full Text Search.

A busca deverá considerar inicialmente:

- título;
- resumo;
- conteúdo.


ETAPA 5 — Testar tudo no SQL Editor do Supabase

Antes de construir a interface Streamlit, testar o banco diretamente no SQL Editor.

Criar registros de teste.

Testar:

- inserção;
- atualização;
- exclusão;
- relacionamentos;
- consultas por pessoa;
- consultas por assunto;
- consultas por keyword;
- consultas por período;
- busca textual.


ETAPA 6 — Criar a aplicação Streamlit

Criar a aplicação Python/Streamlit conectada ao PostgreSQL do Supabase.

A interface inicial deverá ser simples e funcional.


ETAPA 7 — Adicionar cadastro e edição de conversas

A aplicação deverá permitir:

- criar conversa;
- selecionar/cadastrar pessoa;
- selecionar/cadastrar assuntos;
- selecionar/cadastrar keywords;
- informar data e hora;
- informar título;
- informar resumo;
- informar conteúdo;
- editar registros existentes;
- excluir registros.


ETAPA 8 — Implementar filtros e pesquisa

Criar uma tela de pesquisa com filtros como:

- texto livre;
- pessoa;
- assunto;
- keyword;
- data inicial;
- data final.

Os resultados deverão apresentar pelo menos:

- data;
- pessoa;
- título;
- assuntos;
- resumo.

Ao selecionar um resultado, o usuário deverá conseguir visualizar o conteúdo completo.


ETAPA 9 — Criar exportação CSV/JSON

A aplicação deverá permitir exportar os dados.

Formatos obrigatórios:

- CSV
- JSON

A exportação deverá ser pensada para permitir recuperação futura dos dados.

Idealmente, também deverá existir uma opção de exportação completa preservando os relacionamentos entre:

- pessoas;
- conversas;
- assuntos;
- keywords.


ETAPA 10 — Criar rotina de backup

Criar uma estratégia de backup independente do banco hospedado no Supabase.

Considerar:

- backup completo do PostgreSQL;
- exportação JSON;
- exportação CSV.

A aplicação poderá posteriormente possuir um botão:

"Fazer backup"

Também deverá ser possível executar backup externamente utilizando ferramentas PostgreSQL, como pg_dump, quando apropriado.


ETAPA 11 — Adicionar IA posteriormente

A IA NÃO faz parte da primeira versão.

Ela será adicionada somente depois que o sistema básico estiver funcionando.

Possíveis funções:

1. Gerar resumo automaticamente a partir do conteúdo da conversa.

2. Gerar keywords automaticamente.

3. Sugerir assuntos.

4. Melhorar/organizar uma anotação.

5. Pesquisar semanticamente conversas relacionadas.

6. Possivelmente gerar perguntas/respostas sobre o histórico do diário.


============================================================
9. IA E MODELO DE DADOS FUTURO
============================================================

A estrutura deverá permitir que a IA posteriormente gere informações sem comprometer a normalização.

Por exemplo:

CONVERSA
    |
    +-- resumo
    |
    +-- assuntos
    |
    +-- keywords

A primeira implementação pode armazenar um único resumo diretamente em CONVERSA.

Caso no futuro seja necessário manter histórico de resumos gerados por IA, criar:

RESUMO_CONVERSA

com campos possíveis:

- id_resumo
- id_conversa
- resumo
- modelo_ia
- data_geracao

Da mesma forma, keywords geradas pela IA deverão ser relacionadas através da tabela KEYWORD e da tabela associativa CONVERSA_KEYWORD.


============================================================
10. BACKUP E PORTABILIDADE
============================================================

Um requisito fundamental do projeto é NÃO ficar dependente exclusivamente do Supabase.

Os dados deverão poder ser recuperados caso:

- o projeto seja encerrado;
- o serviço seja alterado;
- seja necessário migrar para outro PostgreSQL;
- seja necessário trabalhar localmente;
- seja necessário processar os dados com Python.

Por isso, o projeto deverá possuir:

- exportação JSON;
- exportação CSV;
- backup PostgreSQL;
- estrutura SQL documentada.

Idealmente, o projeto deverá permitir reconstruir o banco em outro PostgreSQL utilizando o schema SQL e os dados exportados.


============================================================
11. POSSÍVEL EVOLUÇÃO DO PROJETO
============================================================

A aplicação poderá evoluir de um simples diário para uma base de conhecimento pessoal.

Possíveis funcionalidades futuras:

- dashboard;
- estatísticas de conversas;
- linha do tempo;
- busca avançada;
- pesquisa semântica;
- embeddings/vector search;
- IA para resumo;
- IA para classificação;
- IA para sugestão de keywords;
- importação de anotações antigas;
- anexos;
- imagens;
- documentos;
- áudio/transcrição;
- integração com outros serviços.


============================================================
12. PRINCÍPIOS IMPORTANTES PARA O DESENVOLVIMENTO
============================================================

1. Não começar pela interface.

Primeiro construir e testar corretamente o banco de dados.


2. Não criar tabelas desnecessárias apenas para "normalizar".

A normalização deve ser utilizada quando houver uma razão relacional clara.


3. RESUMO permanece em CONVERSA na primeira versão.

Não criar uma tabela separada para resumo sem uma necessidade funcional.


4. KEYWORD é uma entidade independente.

Não armazenar keywords como:

"licitação, contrato, fornecedor"

em um único campo.


5. ASSUNTO será tratado como entidade independente.

Uma conversa poderá ter múltiplos assuntos.


6. Utilizar tabelas associativas para relacionamentos N:N.


7. A busca textual deverá utilizar os recursos do PostgreSQL.


8. A aplicação deverá manter os dados portáveis.


9. Backup e exportação são requisitos do projeto, não funcionalidades secundárias.


10. A IA será implementada somente depois que a versão básica estiver funcionando.


============================================================
13. PRÓXIMO PASSO
============================================================

O próximo passo do projeto é:

CRIAR O PROJETO POSTGRESQL NO SUPABASE.

Depois que o projeto Supabase estiver criado, a próxima tarefa será produzir o SQL completo da primeira versão do banco, contendo:

- CREATE TABLE;
- PRIMARY KEY;
- FOREIGN KEY;
- UNIQUE;
- CHECKs necessários;
- índices iniciais;
- relacionamentos;
- timestamps;
- estrutura preparada para Full Text Search.

Após executar esse SQL no Supabase, deverão ser criados dados de teste e executadas consultas para validar toda a estrutura antes de iniciar o desenvolvimento do Streamlit.

IMPORTANTE:

Não avançar para o Streamlit antes de testar o modelo relacional diretamente no PostgreSQL.

============================================================
FIM DO CONTEXTO DO PROJETO
============================================================