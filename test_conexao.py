"""Script auxiliar para testar a conexão com o PostgreSQL do Supabase e validar a presença das tabelas e registros."""

import sys
from pathlib import Path

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adiciona o diretório do projeto ao sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from src import database as db


def main():
    print("=" * 60)
    print("TESTE DE CONEXAO COM O SUPABASE POSTGRESQL")
    print("=" * 60)

    sucesso, msg = db.testar_conexao()
    if not sucesso:
        print(f"\n[FALHA NA CONEXAO]:\n{msg}\n")
        print(
            "DICA: Verifique se voce preencheu a DATABASE_URL no arquivo .env com a senha e host corretos."
        )
        sys.exit(1)

    print(f"\n[SUCESSO]: {msg}\n")

    # Contagem de registros nas tabelas
    try:
        with db.get_db() as conn:
            with conn.cursor() as cur:
                tabelas = [
                    "pessoa",
                    "conversa",
                    "assunto",
                    "keyword",
                    "conversa_assunto",
                    "conversa_keyword",
                ]
                print("Status das tabelas no banco de dados:")
                for t in tabelas:
                    cur.execute(f"SELECT COUNT(*) AS total FROM {t};")
                    qtd = cur.fetchone()["total"]
                    print(f"  - Tabela '{t}': {qtd} registro(s)")
        print("\nTodas as tabelas foram encontradas e estao acessiveis!")
    except Exception as e:
        print(f"\n[AVISO]: Erro ao consultar tabelas: {e}")
        print(
            "DICA: Certifique-se de executar o script 'sql/01_schema.sql' no SQL Editor do Supabase."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

