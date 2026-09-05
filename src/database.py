"""Módulo de acesso ao banco de dados PostgreSQL (Supabase) para o Diário de Anotações.

Implementa operações CRUD, controle transacional, busca estruturada e
Full Text Search com dicionário em português, além de rotinas de exportação.
"""

from contextlib import contextmanager
from datetime import date, datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_db_url() -> str:
    """Retorna a URL de conexão configurada ou dispara exceção se ausente."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url or "SUA_SENHA_AQUI" in url:
        raise ValueError(
            "DATABASE_URL não configurada ou contém placeholders. "
            "Edite o arquivo .env na raiz do projeto com a connection string do Supabase."
        )
    return url


@contextmanager
def get_db():
    """Context manager para gerenciar conexão e transação com o PostgreSQL."""
    conn = psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def testar_conexao() -> Tuple[bool, str]:
    """Testa se a conexão com o PostgreSQL do Supabase está funcional."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                v = cur.fetchone()
                return True, f"Conexão estabelecida com sucesso! ({v['version'].split(',')[0]})"
    except Exception as e:
        return False, str(e)


# ==============================================================================
# CRUD: PESSOA
# ==============================================================================


def listar_pessoas() -> List[Dict[str, Any]]:
    """Lista todas as pessoas cadastradas em ordem alfabética."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id_pessoa, nome, observacoes, criado_em, atualizado_em
                FROM pessoa
                ORDER BY nome ASC;
            """)
            return cur.fetchall()


def obter_pessoa(id_pessoa: int) -> Optional[Dict[str, Any]]:
    """Obtém os detalhes de uma pessoa por ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_pessoa, nome, observacoes, criado_em, atualizado_em
                FROM pessoa
                WHERE id_pessoa = %s;
            """,
                (id_pessoa,),
            )
            return cur.fetchone()


def criar_pessoa(nome: str, observacoes: Optional[str] = None) -> int:
    """Cadastra uma nova pessoa e retorna seu ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pessoa (nome, observacoes)
                VALUES (%s, %s)
                RETURNING id_pessoa;
            """,
                (nome.strip(), observacoes.strip() if observacoes else None),
            )
            return cur.fetchone()["id_pessoa"]


def atualizar_pessoa(
    id_pessoa: int, nome: str, observacoes: Optional[str] = None
) -> None:
    """Atualiza os dados de uma pessoa."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pessoa
                SET nome = %s, observacoes = %s
                WHERE id_pessoa = %s;
            """,
                (nome.strip(), observacoes.strip() if observacoes else None, id_pessoa),
            )


def excluir_pessoa(id_pessoa: int) -> Tuple[bool, str]:
    """Exclui uma pessoa caso ela não possua conversas vinculadas."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM pessoa WHERE id_pessoa = %s;", (id_pessoa,)
                )
                return True, "Pessoa excluída com sucesso."
    except psycopg2.IntegrityError as e:
        return (
            False,
            "Não é possível excluir esta pessoa porque existem conversas vinculadas a ela.",
        )
    except Exception as e:
        return False, f"Erro ao excluir pessoa: {str(e)}"


# ==============================================================================
# CRUD: ASSUNTO
# ==============================================================================


def listar_assuntos() -> List[Dict[str, Any]]:
    """Lista todos os assuntos cadastrados em ordem alfabética."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id_assunto, nome, criado_em
                FROM assunto
                ORDER BY nome ASC;
            """)
            return cur.fetchall()


def obter_ou_criar_assunto(nome: str) -> int:
    """Cria um assunto ou retorna o ID se já existir."""
    nome_limpo = nome.strip()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_assunto FROM assunto WHERE lower(nome) = lower(%s);",
                (nome_limpo,),
            )
            row = cur.fetchone()
            if row:
                return row["id_assunto"]

            cur.execute(
                """
                INSERT INTO assunto (nome)
                VALUES (%s)
                RETURNING id_assunto;
            """,
                (nome_limpo,),
            )
            return cur.fetchone()["id_assunto"]


def excluir_assunto(id_assunto: int) -> Tuple[bool, str]:
    """Exclui um assunto e seus vínculos em conversas (via CASCADE)."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM assunto WHERE id_assunto = %s;", (id_assunto,)
                )
                return True, "Assunto excluído com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir assunto: {str(e)}"


# ==============================================================================
# CRUD: KEYWORD
# ==============================================================================


def listar_keywords() -> List[Dict[str, Any]]:
    """Lista todas as palavras-chave cadastradas em ordem alfabética."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id_keyword, nome, criado_em
                FROM keyword
                ORDER BY nome ASC;
            """)
            return cur.fetchall()


def obter_ou_criar_keyword(nome: str) -> int:
    """Cria uma palavra-chave ou retorna o ID se já existir."""
    nome_limpo = nome.strip()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_keyword FROM keyword WHERE lower(nome) = lower(%s);",
                (nome_limpo,),
            )
            row = cur.fetchone()
            if row:
                return row["id_keyword"]

            cur.execute(
                """
                INSERT INTO keyword (nome)
                VALUES (%s)
                RETURNING id_keyword;
            """,
                (nome_limpo,),
            )
            return cur.fetchone()["id_keyword"]


def excluir_keyword(id_keyword: int) -> Tuple[bool, str]:
    """Exclui uma keyword e seus vínculos em conversas (via CASCADE)."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM keyword WHERE id_keyword = %s;", (id_keyword,)
                )
                return True, "Palavra-chave excluída com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir keyword: {str(e)}"


# ==============================================================================
# CRUD: CONVERSA & RELACIONAMENTOS (Transacional)
# ==============================================================================


def salvar_conversa(
    id_pessoa: int,
    titulo: str,
    conteudo: str,
    data_hora: datetime,
    resumo: Optional[str] = None,
    ids_assuntos: Optional[List[int]] = None,
    ids_keywords: Optional[List[int]] = None,
    id_conversa: Optional[int] = None,
) -> int:
    """Cria ou atualiza uma conversa e sincroniza os vínculos N:N em transação."""
    ids_assuntos = ids_assuntos or []
    ids_keywords = ids_keywords or []

    with get_db() as conn:
        with conn.cursor() as cur:
            if id_conversa:
                # Atualização da conversa
                cur.execute(
                    """
                    UPDATE conversa
                    SET data_hora = %s,
                        id_pessoa = %s,
                        titulo = %s,
                        resumo = %s,
                        conteudo = %s
                    WHERE id_conversa = %s;
                """,
                    (
                        data_hora,
                        id_pessoa,
                        titulo.strip(),
                        resumo.strip() if resumo else None,
                        conteudo.strip(),
                        id_conversa,
                    ),
                )
                # Remove vínculos antigos para reinserção sincronizada
                cur.execute(
                    "DELETE FROM conversa_assunto WHERE id_conversa = %s;",
                    (id_conversa,),
                )
                cur.execute(
                    "DELETE FROM conversa_keyword WHERE id_conversa = %s;",
                    (id_conversa,),
                )
                cid = id_conversa
            else:
                # Criação de nova conversa
                cur.execute(
                    """
                    INSERT INTO conversa (data_hora, id_pessoa, titulo, resumo, conteudo)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_conversa;
                """,
                    (
                        data_hora,
                        id_pessoa,
                        titulo.strip(),
                        resumo.strip() if resumo else None,
                        conteudo.strip(),
                    ),
                )
                cid = cur.fetchone()["id_conversa"]

            # Vincula assuntos selecionados
            if ids_assuntos:
                valores_assuntos = [(cid, aid) for aid in ids_assuntos]
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO conversa_assunto (id_conversa, id_assunto) VALUES %s ON CONFLICT DO NOTHING;",
                    valores_assuntos,
                )

            # Vincula keywords selecionadas
            if ids_keywords:
                valores_keywords = [(cid, kid) for kid in ids_keywords]
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO conversa_keyword (id_conversa, id_keyword) VALUES %s ON CONFLICT DO NOTHING;",
                    valores_keywords,
                )

            return cid


def excluir_conversa(id_conversa: int) -> Tuple[bool, str]:
    """Exclui uma conversa (CASCADE limpa as associativas automaticamente)."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM conversa WHERE id_conversa = %s;",
                    (id_conversa,),
                )
                return True, "Conversa excluída com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir conversa: {str(e)}"


def obter_conversa_detalhes(id_conversa: int) -> Optional[Dict[str, Any]]:
    """Retorna os dados completos de uma conversa com listas de assuntos e keywords."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    c.id_conversa,
                    c.data_hora,
                    c.id_pessoa,
                    p.nome AS pessoa_nome,
                    c.titulo,
                    c.resumo,
                    c.conteudo,
                    c.criado_em,
                    c.atualizado_em,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id_assunto', a.id_assunto, 'nome', a.nome) ORDER BY a.nome)
                         FROM conversa_assunto ca
                         JOIN assunto a ON a.id_assunto = ca.id_assunto
                         WHERE ca.id_conversa = c.id_conversa),
                        '[]'::json
                    ) AS assuntos,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id_keyword', k.id_keyword, 'nome', k.nome) ORDER BY k.nome)
                         FROM conversa_keyword ck
                         JOIN keyword k ON k.id_keyword = ck.id_keyword
                         WHERE ck.id_conversa = c.id_conversa),
                        '[]'::json
                    ) AS keywords
                FROM conversa c
                JOIN pessoa p ON p.id_pessoa = c.id_pessoa
                WHERE c.id_conversa = %s;
            """,
                (id_conversa,),
            )
            return cur.fetchone()


# ==============================================================================
# BUSCA HÍBRIDA: ESTRUTURADA + FULL TEXT SEARCH (FTS)
# ==============================================================================


def buscar_conversas(
    termo_busca: Optional[str] = None,
    id_pessoa: Optional[int] = None,
    id_assunto: Optional[int] = None,
    id_keyword: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    limite: int = 100,
) -> List[Dict[str, Any]]:
    """Executa a busca combinando filtros estruturados e/ou Full Text Search no PostgreSQL.

    Se houver termo_busca:
      - Utiliza websearch_to_tsquery('portuguese', %s)
      - Ordena por relevância (ts_rank) decrescente
      - Extrai trecho destacado com marcações <mark>...</mark> via ts_headline
    Se não houver termo_busca:
      - Ordena cronologicamente decrescente (c.data_hora DESC)
    """
    where_clauses = []
    params = []

    tem_fts = bool(termo_busca and termo_busca.strip())

    if tem_fts:
        fts_query = termo_busca.strip()
        where_clauses.append("c.busca_vetor @@ q")
        headline_expr = """ts_headline(
            'portuguese', 
            c.conteudo, 
            q, 
            'StartSel = <mark>, StopSel = </mark>, MaxWords=35, MinWords=15'
        ) AS trecho_destacado"""
        rank_expr = "ts_rank(c.busca_vetor, q) AS relevancia,"
        from_fts = ", websearch_to_tsquery('portuguese', %s) q"
        params.append(fts_query)
    else:
        headline_expr = "NULL AS trecho_destacado"
        rank_expr = "0.0 AS relevancia,"
        from_fts = ""

    if id_pessoa:
        where_clauses.append("c.id_pessoa = %s")
        params.append(id_pessoa)

    if id_assunto:
        where_clauses.append("""EXISTS (
            SELECT 1 FROM conversa_assunto ca 
            WHERE ca.id_conversa = c.id_conversa AND ca.id_assunto = %s
        )""")
        params.append(id_assunto)

    if id_keyword:
        where_clauses.append("""EXISTS (
            SELECT 1 FROM conversa_keyword ck 
            WHERE ck.id_conversa = c.id_conversa AND ck.id_keyword = %s
        )""")
        params.append(id_keyword)

    if data_inicio:
        where_clauses.append("c.data_hora >= %s")
        params.append(datetime.combine(data_inicio, datetime.min.time()))

    if data_fim:
        where_clauses.append("c.data_hora <= %s")
        params.append(datetime.combine(data_fim, datetime.max.time()))

    where_sql = (
        ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    )
    order_sql = (
        "ORDER BY relevancia DESC, c.data_hora DESC"
        if tem_fts
        else "ORDER BY c.data_hora DESC"
    )

    query = f"""
        SELECT 
            c.id_conversa,
            c.data_hora,
            p.id_pessoa,
            p.nome AS pessoa_nome,
            c.titulo,
            c.resumo,
            c.conteudo,
            {rank_expr}
            {headline_expr},
            COALESCE(
                (SELECT string_agg(a.nome, ', ' ORDER BY a.nome)
                 FROM conversa_assunto ca
                 JOIN assunto a ON a.id_assunto = ca.id_assunto
                 WHERE ca.id_conversa = c.id_conversa),
                ''
            ) AS assuntos_str,
            COALESCE(
                (SELECT string_agg(k.nome, ', ' ORDER BY k.nome)
                 FROM conversa_keyword ck
                 JOIN keyword k ON k.id_keyword = ck.id_keyword
                 WHERE ck.id_conversa = c.id_conversa),
                ''
            ) AS keywords_str
        FROM conversa c
        JOIN pessoa p ON p.id_pessoa = c.id_pessoa
        {from_fts}
        {where_sql}
        {order_sql}
        LIMIT %s;
    """
    params.append(limite)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall()


# ==============================================================================
# EXPORTAÇÃO E BACKUP INDEPENDENTE (Etapas 9 e 10)
# ==============================================================================


def exportar_tudo_json() -> str:
    """Gera um arquivo JSON completo e hierárquico com todas as entidades e relacionamentos."""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Pessoas
            cur.execute(
                "SELECT id_pessoa, nome, observacoes, criado_em, atualizado_em FROM pessoa ORDER BY id_pessoa;"
            )
            pessoas = cur.fetchall()

            # Assuntos
            cur.execute(
                "SELECT id_assunto, nome, criado_em FROM assunto ORDER BY id_assunto;"
            )
            assuntos = cur.fetchall()

            # Keywords
            cur.execute(
                "SELECT id_keyword, nome, criado_em FROM keyword ORDER BY id_keyword;"
            )
            keywords = cur.fetchall()

            # Conversas completas com relacionamentos
            cur.execute("""
                SELECT 
                    c.id_conversa,
                    c.data_hora,
                    c.id_pessoa,
                    p.nome AS pessoa_nome,
                    c.titulo,
                    c.resumo,
                    c.conteudo,
                    c.criado_em,
                    c.atualizado_em,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id_assunto', a.id_assunto, 'nome', a.nome) ORDER BY a.nome)
                         FROM conversa_assunto ca
                         JOIN assunto a ON a.id_assunto = ca.id_assunto
                         WHERE ca.id_conversa = c.id_conversa),
                        '[]'::json
                    ) AS assuntos,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id_keyword', k.id_keyword, 'nome', k.nome) ORDER BY k.nome)
                         FROM conversa_keyword ck
                         JOIN keyword k ON k.id_keyword = ck.id_keyword
                         WHERE ck.id_conversa = c.id_conversa),
                        '[]'::json
                    ) AS keywords
                FROM conversa c
                JOIN pessoa p ON p.id_pessoa = c.id_pessoa
                ORDER BY c.data_hora DESC;
            """)
            conversas = cur.fetchall()

    backup_payload = {
        "metadata": {
            "sistema": "Diário de Anotações Pessoal",
            "gerado_em": datetime.utcnow().isoformat() + "Z",
            "versao_schema": "1.0",
        },
        "pessoas": pessoas,
        "assuntos": assuntos,
        "keywords": keywords,
        "conversas": conversas,
    }

    # Serializador para datetime e date
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    return json.dumps(backup_payload, ensure_ascii=False, indent=2, default=json_serial)


def exportar_tabelas_csv() -> Dict[str, pd.DataFrame]:
    """Retorna dicionário de DataFrames para cada tabela do sistema."""
    queries = {
        "conversas_consolidado.csv": """
            SELECT 
                c.id_conversa,
                c.data_hora,
                c.id_pessoa,
                p.nome AS pessoa_nome,
                c.titulo,
                c.resumo,
                c.conteudo,
                c.criado_em,
                c.atualizado_em,
                COALESCE((SELECT string_agg(a.nome, '; ') FROM conversa_assunto ca JOIN assunto a ON a.id_assunto = ca.id_assunto WHERE ca.id_conversa = c.id_conversa), '') AS assuntos,
                COALESCE((SELECT string_agg(k.nome, '; ') FROM conversa_keyword ck JOIN keyword k ON k.id_keyword = ck.id_keyword WHERE ck.id_conversa = c.id_conversa), '') AS keywords
            FROM conversa c
            JOIN pessoa p ON p.id_pessoa = c.id_pessoa
            ORDER BY c.data_hora DESC;
        """,
        "pessoas.csv": "SELECT * FROM pessoa ORDER BY id_pessoa;",
        "assuntos.csv": "SELECT * FROM assunto ORDER BY id_assunto;",
        "keywords.csv": "SELECT * FROM keyword ORDER BY id_keyword;",
        "conversa_assunto.csv": "SELECT * FROM conversa_assunto;",
        "conversa_keyword.csv": "SELECT * FROM conversa_keyword;",
    }

    resultado = {}
    with get_db() as conn:
        with conn.cursor() as cur:
            for nome_arquivo, sql in queries.items():
                cur.execute(sql)
                rows = cur.fetchall()
                resultado[nome_arquivo] = pd.DataFrame(rows) if rows else pd.DataFrame()

    return resultado


def ler_schema_ddl() -> str:
    """Lê o arquivo de schema SQL do disco para fornecer download na interface."""
    caminho = (
        Path(__file__).resolve().parent.parent / "sql" / "01_schema.sql"
    )
    if caminho.exists():
        return caminho.read_text(encoding="utf-8")
    return "-- Arquivo 01_schema.sql não encontrado na pasta sql/"

