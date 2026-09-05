"""Script para inicializar o schema do banco de dados no Supabase e opcionalmente carregar dados de teste."""

import argparse
from pathlib import Path
import sys

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.append(str(Path(__file__).resolve().parent))

from src import database as db


def executar_sql(arquivo_sql: Path, descricao: str):
    print(f"\nExecutando: {descricao} ({arquivo_sql.name})...")
    if not arquivo_sql.exists():
        print(f"Erro: Arquivo {arquivo_sql} nao encontrado.")
        sys.exit(1)

    conteudo = arquivo_sql.read_text(encoding="utf-8")

    with db.get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(conteudo)
    print(f"OK: {descricao} executado com sucesso!")


def main():
    parser = argparse.ArgumentParser(
        description="Inicializa o banco de dados Supabase com schema e dados de teste."
    )
    parser.add_argument(
        "--com-dados-teste",
        action="store_true",
        help="Carrega tambem os dados de teste iniciais (02_dados_teste.sql)",
    )
    args = parser.parse_args()

    diretorio_sql = Path(__file__).resolve().parent / "sql"
    schema_file = diretorio_sql / "01_schema.sql"
    seed_file = diretorio_sql / "02_dados_teste.sql"

    print("=" * 60)
    print("INICIALIZADOR DO BANCO DE DADOS (SUPABASE POSTGRESQL)")
    print("=" * 60)

    sucesso, msg = db.testar_conexao()
    if not sucesso:
        print(f"Falha de conexao: {msg}")
        sys.exit(1)
    print(f"Conexao: {msg}")

    # Executa o schema DDL
    executar_sql(schema_file, "Criacao de Tabelas, Indices, Triggers e FTS")

    # Executa carga de teste se solicitada
    if args.com_dados_teste:
        executar_sql(seed_file, "Carga de Dados de Teste")

    print("\nInicializacao concluida com sucesso!")


if __name__ == "__main__":
    main()

