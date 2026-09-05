# 📓 Diário de Anotações Pessoal

Aplicação para registro, organização e consulta inteligente de conversas e anotações pessoais, construída com **Python**, **Streamlit** e **PostgreSQL** hospedado no **Supabase**.

---

## 🌟 Funcionalidades Principais

- **Modelagem Relacional (3FN):** Entidades independentes para Pessoas, Assuntos e Palavras-chave (*keywords*), com tabelas associativas N:N e integridade referencial com proteção contra deleções acidentais (`RESTRICT` e `CASCADE`).
- **Busca Híbrida Inteligente:**
  - **Full Text Search (FTS):** Motor de busca textual nativo do PostgreSQL configurado com dicionário `'portuguese'`, coluna vetorial gerada e ponderada (`busca_vetor tsvector`), stemming em português e índice **GIN**.
  - **Relevância e Destaque:** Classificação por relevância (`ts_rank`) e realce visual dos termos encontrados no texto longo com tags `<mark>` (`ts_headline`).
  - **Filtros Estruturados:** Filtragem combinada por pessoa, assunto, palavra-chave e períodos de datas.
- **Gestão Transacional:** Inclusão, edição e exclusão de conversas com sincronização atômica dos vínculos associativos (`COMMIT`/`ROLLBACK`).
- **Cadastros Básicos:** Interface dedicada para gerenciar pessoas (com observações/contatos), assuntos e tags, além de cadastros rápidos inline dentro do próprio formulário de conversa.
- **Portabilidade Total e Backup Independente:**
  - Exportação completa em formato **JSON** hierárquico, preservando todas as entidades e relacionamentos.
  - Exportação das tabelas em planilhas **CSV** (visão consolidada e tabelas normalizadas).
  - Download em um clique do script DDL de recriação do schema SQL (`01_schema.sql`).

---

## 📁 Estrutura do Projeto

```text
diario_anotacoes/
├── .env.example                 # Modelo com instruções de variáveis de ambiente
├── .env                         # Configurações e credenciais locais (ignorado no git)
├── .gitignore                   # Arquivos ignorados pelo controle de versão
├── requirements.txt             # Dependências Python pinadas
├── inicializar_banco.py         # Script para criar schema e carregar dados no Supabase
├── test_conexao.py              # Script de teste e diagnóstico de conexão
├── README.md                    # Este manual de instruções
├── sql/
│   ├── 01_schema.sql            # DDL: tabelas, triggers, índices e FTS
│   ├── 02_dados_teste.sql       # Carga inicial com registros realistas de teste
│   └── 03_consultas_validacao.sql # Consultas de validação e testes de integridade
└── src/
    ├── __init__.py              # Módulo do pacote
    ├── database.py              # Camada de banco de dados, FTS e exportações
    └── app.py                   # Interface do usuário em Streamlit
```

---

## 🚀 Passo a Passo: Configuração e Execução

### 1. Clonar ou Acessar o Diretório do Projeto
Abra o terminal na pasta raiz do projeto:

```powershell
cd c:\caminho\para\diario_anotacoes
```

---

### 2. Criar o Ambiente Virtual (venv)

Recomendamos utilizar o Python 3.10 ou superior (totalmente compatível com Python 3.14).

- **No Windows (PowerShell ou Prompt de Comando):**
  ```powershell
  python -m venv my_env
  ```

- **No Linux ou macOS:**
  ```bash
  python3 -m venv my_env
  ```

---

### 3. Ativar o Ambiente Virtual

- **No Windows (PowerShell):**
  ```powershell
  .\my_env\Scripts\Activate.ps1
  ```
  > *Dica:* Caso o PowerShell bloqueie a execução de scripts, execute previamente uma única vez:
  > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

- **No Windows (Prompt de Comando / CMD):**
  ```cmd
  my_env\Scripts\activate.bat
  ```

- **No Linux ou macOS:**
  ```bash
  source my_env/bin/activate
  ```

Após a ativação, você verá o prefixo `(my_env)` no seu terminal.

---

### 4. Instalar as Dependências

Com o ambiente virtual ativado, instale todos os pacotes necessários via `requirements.txt`:

```powershell
pip install -r requirements.txt
```

---

### 5. Configurar as Credenciais do Banco (`.env`)

1. Crie ou edite o arquivo [`.env`](.env) na raiz do projeto (use o arquivo [`.env.example`](.env.example) como referência).
2. Obtenha a sua **Connection String URI** no painel do Supabase:
   - Vá em: **Project Settings** ➔ **Database** ➔ **Connection string** ➔ **URI** (ou clique no botão **Connect** no topo do painel).
3. Insira a URL no arquivo `.env`:

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA_AQUI@db.SEU_PROJETO_ID.supabase.co:5432/postgres
```
*(Substitua `SUA_SENHA_AQUI` pela senha definida na criação do banco e `SEU_PROJETO_ID` pelo identificador do projeto no Supabase).*

---

### 6. Inicializar o Banco de Dados no Supabase

Você tem duas formas de criar a estrutura no PostgreSQL:

- **Opção A (Mais rápida via terminal Python):**
  ```powershell
  python inicializar_banco.py --com-dados-teste
  ```
  *Esse comando executa o `01_schema.sql` (tabelas, índices, FTS e triggers) e popula com os registros de teste do `02_dados_teste.sql`.*

- **Opção B (Pelo painel web do Supabase):**
  Acesse o menu **SQL Editor** no painel do Supabase, copie o conteúdo de [`sql/01_schema.sql`](sql/01_schema.sql) e clique em **Run**. Em seguida, repita o processo com [`sql/02_dados_teste.sql`](sql/02_dados_teste.sql).

---

### 7. Testar a Conexão e a Estrutura

Execute o script de diagnóstico para verificar a conectividade e a contagem de registros em cada tabela:

```powershell
python test_conexao.py
```

Você deverá ver uma saída similar a:
```text
============================================================
TESTE DE CONEXAO COM O SUPABASE POSTGRESQL
============================================================

[SUCESSO]: Conexão estabelecida com sucesso! (PostgreSQL 17.6 on x86_64-pc-linux-gnu)

Status das tabelas no banco de dados:
  - Tabela 'pessoa': 4 registro(s)
  - Tabela 'conversa': 4 registro(s)
  - Tabela 'assunto': 5 registro(s)
  - Tabela 'keyword': 9 registro(s)
  - Tabela 'conversa_assunto': 5 registro(s)
  - Tabela 'conversa_keyword': 10 registro(s)

Todas as tabelas foram encontradas e estao acessiveis!
```

---

### 8. Iniciar a Aplicação Streamlit

Para iniciar a interface web:

```powershell
streamlit run src/app.py
```

O navegador abrirá automaticamente no endereço:
👉 **`http://localhost:8501`**

---

## 🧭 Como Usar a Interface

1. **🔍 Pesquisar & Explorar:**
   - Faça buscas textuais livres usando Full Text Search (ex: *"fornecedor não entregou material"*, *"licitação"*, *"projeto x"*).
   - Abra o painel de filtros para refinar por pessoa, assunto, keyword ou intervalo de datas.
   - Visualize os trechos destacados no texto (`<mark>`) e clique em *📖 Ler Conteúdo Completo* para ver a anotação na íntegra.
   - Use os botões ✏️ para editar ou 🗑️ para excluir registros.

2. **📝 Nova / Editar Conversa:**
   - Preencha data, hora, pessoa participante, assuntos e palavras-chave.
   - Use a seção *⚡ Cadastros Rápidos* para adicionar novas pessoas, assuntos ou tags na hora, sem trocar de tela.
   - Salve o registro: o PostgreSQL indexará automaticamente o texto para pesquisas imediatas.

3. **👥 Gestão de Cadastros:**
   - Visualize, edite e gerencie seus contatos (pessoas), lista de assuntos e palavras-chave.
   - A exclusão de pessoas com histórico de conversas é protegida contra perda acidental de dados.

4. **💾 Backup & Exportação:**
   - **Backup Completo em JSON:** Baixe um arquivo estruturado com metadados e todos os relacionamentos N:N preservados.
   - **Planilhas em CSV:** Baixe tabelas individuais ou o arquivo consolidado de conversas com assuntos e tags concatenados.
   - **Schema DDL:** Baixe o arquivo SQL completo para reconstruir o banco em qualquer servidor PostgreSQL.
