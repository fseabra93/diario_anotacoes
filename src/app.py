"""Interface Streamlit para o Diário de Anotações Pessoal.

Projetada com arquitetura modular, busca híbrida (FTS + estruturada),
gerenciamento transacional de conversas e exportações independentes (JSON/CSV).
"""

from datetime import date, datetime, time
import io
from pathlib import Path
import sys
from typing import List

import pandas as pd
import streamlit as st

# Garante que o diretório src e o root estejam no path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import database as db

# ==============================================================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Diário de Anotações Pessoal",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS customizada
st.markdown(
    """
<style>
    .badge-pessoa {
        background-color: #e3f2fd;
        color: #0d47a1;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-assunto {
        background-color: #f3e5f5;
        color: #4a148c;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 0.8rem;
        margin-right: 4px;
        display: inline-block;
    }
    .badge-keyword {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 0.8rem;
        margin-right: 4px;
        display: inline-block;
    }
    mark {
        background-color: #ffeaa7;
        color: #2d3436;
        padding: 2px 5px;
        border-radius: 4px;
        font-weight: bold;
    }
    .card-conversa {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Inicialização de variáveis no session_state
if "edit_id_conversa" not in st.session_state:
    st.session_state.edit_id_conversa = None

if "pagina_ativa" not in st.session_state:
    st.session_state.pagina_ativa = "🔍 Pesquisar & Explorar"


# ==============================================================================
# VERIFICAÇÃO DE CONEXÃO COM O BANCO DE DADOS
# ==============================================================================
conectado, msg_conexao = db.testar_conexao()

if not conectado:
    st.title("📓 Diário de Anotações Pessoal")
    st.error("⚠️ Não foi possível conectar ao banco de dados PostgreSQL!")

    with st.container(border=True):
        st.subheader("Configuração de Acesso (Supabase)")
        st.markdown(f"""
        **Detalhes do erro:** `{msg_conexao}`
        
        Para conectar a aplicação ao seu banco de dados:
        1. Abra o arquivo [`.env`](file:///{Path(__file__).resolve().parent.parent / '.env'}) na raiz do projeto.
        2. Obtenha a **URI de Conexão** no seu painel Supabase:
           - Acesse: **Project Settings** ➔ **Database** ➔ **Connection string** ➔ **URI**.
        3. Cole sua connection string no `.env`:
           ```env
           DATABASE_URL=postgresql://postgres:[SUA_SENHA]@db.[SEU_PROJETO].supabase.co:5432/postgres
           ```
        4. Clique no botão abaixo para testar novamente.
        """)

        if st.button("🔄 Testar Conexão Novamente", type="primary"):
            st.rerun()

    st.stop()


# ==============================================================================
# MENU LATERAL (SIDEBAR)
# ==============================================================================
with st.sidebar:
    st.title("📓 Diário Pessoal")
    st.caption("PostgreSQL + FTS + Streamlit")
    st.divider()

    opcoes_menu = [
        "🔍 Pesquisar & Explorar",
        "📝 Nova / Editar Conversa",
        "👥 Gestão de Cadastros",
        "💾 Backup & Exportação",
    ]

    pagina_selecionada = st.radio(
        "Navegação",
        opcoes_menu,
        index=opcoes_menu.index(st.session_state.pagina_ativa)
        if st.session_state.pagina_ativa in opcoes_menu
        else 0,
    )
    st.session_state.pagina_ativa = pagina_selecionada

    st.divider()
    st.success("🟢 Conectado ao Supabase")


# ==============================================================================
# VIEW 1: PESQUISAR & EXPLORAR (FTS + FILTROS ESTRUTURADOS)
# ==============================================================================
if st.session_state.pagina_ativa == "🔍 Pesquisar & Explorar":
    st.title("🔍 Pesquisar e Explorar Registros")
    st.caption(
        "Utilize a busca textual Full Text Search ou combine filtros de pessoa, assunto, keyword e data."
    )

    # Campo de busca livre FTS
    termo_busca = st.text_input(
        "Busca Textual Livre (PostgreSQL Full Text Search com Stemming em Português)",
        placeholder="Ex: fornecedor não entregou material, licitação, prazo do contrato...",
        help="Pesquisa instantânea em título, resumo e conteúdo completo, tolerante a flexões verbais e plurais.",
    )

    # Filtros estruturados colapsáveis
    with st.expander("Filtros Estruturados Adicionais", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)

        pessoas = db.listar_pessoas()
        opcoes_pessoas = {p["nome"]: p["id_pessoa"] for p in pessoas}
        with col_f1:
            pessoa_sel = st.selectbox(
                "Filtrar por Pessoa", ["(Todas)"] + list(opcoes_pessoas.keys())
            )
            id_pessoa_filtro = (
                opcoes_pessoas[pessoa_sel] if pessoa_sel != "(Todas)" else None
            )

        assuntos = db.listar_assuntos()
        opcoes_assuntos = {a["nome"]: a["id_assunto"] for a in assuntos}
        with col_f2:
            assunto_sel = st.selectbox(
                "Filtrar por Assunto",
                ["(Todos)"] + list(opcoes_assuntos.keys()),
            )
            id_assunto_filtro = (
                opcoes_assuntos[assunto_sel]
                if assunto_sel != "(Todos)"
                else None
            )

        keywords = db.listar_keywords()
        opcoes_keywords = {k["nome"]: k["id_keyword"] for k in keywords}
        with col_f3:
            keyword_sel = st.selectbox(
                "Filtrar por Palavra-chave",
                ["(Todas)"] + list(opcoes_keywords.keys()),
            )
            id_keyword_filtro = (
                opcoes_keywords[keyword_sel]
                if keyword_sel != "(Todas)"
                else None
            )

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_inicio = st.date_input(
                "Data Inicial", value=None, format="DD/MM/YYYY"
            )
        with col_d2:
            data_fim = st.date_input(
                "Data Final", value=None, format="DD/MM/YYYY"
            )

    # Executa a busca híbrida
    resultados = db.buscar_conversas(
        termo_busca=termo_busca,
        id_pessoa=id_pessoa_filtro,
        id_assunto=id_assunto_filtro,
        id_keyword=id_keyword_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    st.markdown(f"**{len(resultados)} registro(s) encontrado(s)**")

    if not resultados:
        st.info(
            "Nenhuma conversa encontrada para os termos e filtros selecionados."
        )

    for item in resultados:
        with st.container(border=True):
            col_header1, col_header2 = st.columns([4, 1])

            with col_header1:
                st.subheader(item["titulo"])
                data_formatada = (
                    item["data_hora"].strftime("%d/%m/%Y às %H:%M")
                    if isinstance(item["data_hora"], datetime)
                    else str(item["data_hora"])
                )
                st.markdown(
                    f"📅 **{data_formatada}** &nbsp; | &nbsp; 👤 <span class='badge-pessoa'>{item['pessoa_nome']}</span>",
                    unsafe_allow_html=True,
                )

            with col_header2:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button(
                        "✏️",
                        key=f"edit_{item['id_conversa']}",
                        help="Editar anotação",
                    ):
                        st.session_state.edit_id_conversa = item["id_conversa"]
                        st.session_state.pagina_ativa = (
                            "📝 Nova / Editar Conversa"
                        )
                        st.rerun()
                with btn_col2:
                    if st.button(
                        "🗑️",
                        key=f"del_{item['id_conversa']}",
                        help="Excluir anotação",
                    ):
                        st.session_state[f"confirm_del_{item['id_conversa']}"] = (
                            True
                        )

            # Confirmação de exclusão
            if st.session_state.get(f"confirm_del_{item['id_conversa']}", False):
                st.warning("Tem certeza que deseja excluir este registro?")
                c_conf1, c_conf2 = st.columns([1, 4])
                with c_conf1:
                    if st.button(
                        "Sim, excluir",
                        key=f"yes_del_{item['id_conversa']}",
                        type="primary",
                    ):
                        sucesso, msg = db.excluir_conversa(item["id_conversa"])
                        if sucesso:
                            st.success(msg)
                            st.session_state[
                                f"confirm_del_{item['id_conversa']}"
                            ] = False
                            st.rerun()
                        else:
                            st.error(msg)
                with c_conf2:
                    if st.button(
                        "Cancelar", key=f"no_del_{item['id_conversa']}"
                    ):
                        st.session_state[
                            f"confirm_del_{item['id_conversa']}"
                        ] = False
                        st.rerun()

            # Resumo
            if item.get("resumo"):
                st.markdown(f"**Resumo:** {item['resumo']}")

            # Trecho destacado FTS (quando houver busca textual)
            if item.get("trecho_destacado"):
                st.markdown(
                    f"**Trecho Relevante Encontrado:** ... {item['trecho_destacado']} ...",
                    unsafe_allow_html=True,
                )

            # Badges de Assuntos e Keywords
            badges_html = []
            if item.get("assuntos_str"):
                for a in item["assuntos_str"].split(", "):
                    badges_html.append(
                        f"<span class='badge-assunto'>📁 {a}</span>"
                    )
            if item.get("keywords_str"):
                for k in item["keywords_str"].split(", "):
                    badges_html.append(
                        f"<span class='badge-keyword'>🏷️ {k}</span>"
                    )

            if badges_html:
                st.markdown(" ".join(badges_html), unsafe_allow_html=True)

            # Expansor para leitura do conteúdo completo
            with st.expander("📖 Ler Conteúdo Completo da Conversa"):
                st.write(item["conteudo"])


# ==============================================================================
# VIEW 2: NOVA / EDITAR CONVERSA
# ==============================================================================
elif st.session_state.pagina_ativa == "📝 Nova / Editar Conversa":
    is_edit = st.session_state.edit_id_conversa is not None

    if is_edit:
        st.title("✏️ Editar Conversa")
        dados_antigos = db.obter_conversa_detalhes(
            st.session_state.edit_id_conversa
        )
        if not dados_antigos:
            st.error("Registro não encontrado.")
            st.session_state.edit_id_conversa = None
            st.rerun()
    else:
        st.title("📝 Registrar Nova Conversa / Anotação")
        dados_antigos = None

    pessoas = db.listar_pessoas()
    assuntos = db.listar_assuntos()
    keywords = db.listar_keywords()

    if not pessoas:
        st.warning(
            "Cadastre pelo menos uma pessoa antes de registrar uma conversa."
        )
        with st.expander("➕ Cadastrar Primeira Pessoa Agora", expanded=True):
            nome_p = st.text_input("Nome da Pessoa")
            obs_p = st.text_area("Observações")
            if st.button("Salvar Pessoa"):
                if nome_p.strip():
                    db.criar_pessoa(nome_p, obs_p)
                    st.success("Pessoa cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Informe o nome da pessoa.")
        st.stop()

    mapa_pessoas = {p["nome"]: p["id_pessoa"] for p in pessoas}
    lista_nomes_pessoas = list(mapa_pessoas.keys())

    mapa_assuntos = {a["nome"]: a["id_assunto"] for a in assuntos}
    lista_nomes_assuntos = list(mapa_assuntos.keys())

    mapa_keywords = {k["nome"]: k["id_keyword"] for k in keywords}
    lista_nomes_keywords = list(mapa_keywords.keys())

    # Valores padrão
    if is_edit:
        default_dt = dados_antigos["data_hora"]
        default_pessoa = dados_antigos["pessoa_nome"]
        default_titulo = dados_antigos["titulo"]
        default_resumo = dados_antigos["resumo"] or ""
        default_conteudo = dados_antigos["conteudo"]
        default_assuntos = [a["nome"] for a in dados_antigos["assuntos"]]
        default_keywords = [k["nome"] for k in dados_antigos["keywords"]]
    else:
        default_dt = datetime.now()
        default_pessoa = lista_nomes_pessoas[0]
        default_titulo = ""
        default_resumo = ""
        default_conteudo = ""
        default_assuntos = []
        default_keywords = []

    # Formulário
    with st.form("form_conversa", clear_on_submit=False):
        col_c1, col_c2, col_c3 = st.columns([2, 1, 1])

        with col_c1:
            idx_pessoa = (
                lista_nomes_pessoas.index(default_pessoa)
                if default_pessoa in lista_nomes_pessoas
                else 0
            )
            pessoa_escolhida = st.selectbox(
                "Pessoa Envolvida *", lista_nomes_pessoas, index=idx_pessoa
            )

        with col_c2:
            data_escolhida = st.date_input(
                "Data *", value=default_dt.date(), format="DD/MM/YYYY"
            )

        with col_c3:
            hora_escolhida = st.time_input(
                "Hora *", value=default_dt.time().replace(second=0, microsecond=0)
            )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            assuntos_escolhidos = st.multiselect(
                "Assuntos Abordados (N:N)",
                lista_nomes_assuntos,
                default=[
                    a for a in default_assuntos if a in lista_nomes_assuntos
                ],
                help="Selecione um ou mais assuntos.",
            )
        with col_m2:
            keywords_escolhidas = st.multiselect(
                "Palavras-chave (Keywords N:N)",
                lista_nomes_keywords,
                default=[
                    k for k in default_keywords if k in lista_nomes_keywords
                ],
                help="Tags e termos-chave para categorização e busca.",
            )

        titulo = st.text_input(
            "Título da Conversa *",
            value=default_titulo,
            placeholder="Ex: Reunião sobre prazos da licitação de serviços",
        )

        resumo = st.text_area(
            "Resumo Executivo (opcional)",
            value=default_resumo,
            height=70,
            placeholder="Breve síntese dos principais pontos acertados.",
        )

        conteudo = st.text_area(
            "Conteúdo Completo da Conversa / Anotação *",
            value=default_conteudo,
            height=200,
            placeholder="Registre detalhadamente tudo o que foi conversado, acordos, prazos e próximos passos...",
        )

        col_b1, col_b2 = st.columns([1, 4])
        with col_b1:
            salvar = st.form_submit_button(
                "💾 Salvar Registro", type="primary", use_container_width=True
            )
        with col_b2:
            if is_edit:
                cancelar = st.form_submit_button("❌ Cancelar Edição")
                if cancelar:
                    st.session_state.edit_id_conversa = None
                    st.session_state.pagina_ativa = "🔍 Pesquisar & Explorar"
                    st.rerun()

    if salvar:
        if not titulo.strip():
            st.error("O título é obrigatório.")
        elif not conteudo.strip():
            st.error("O conteúdo da conversa é obrigatório.")
        else:
            dt_completa = datetime.combine(data_escolhida, hora_escolhida)
            id_pessoa = mapa_pessoas[pessoa_escolhida]
            ids_assuntos = [mapa_assuntos[nome] for nome in assuntos_escolhidos]
            ids_keywords = [mapa_keywords[nome] for nome in keywords_escolhidas]

            try:
                novo_id = db.salvar_conversa(
                    id_pessoa=id_pessoa,
                    titulo=titulo,
                    conteudo=conteudo,
                    data_hora=dt_completa,
                    resumo=resumo,
                    ids_assuntos=ids_assuntos,
                    ids_keywords=ids_keywords,
                    id_conversa=st.session_state.edit_id_conversa,
                )
                st.success(
                    "Registro salvo com sucesso! O Full Text Search já indexou este conteúdo."
                )
                st.session_state.edit_id_conversa = None
                st.session_state.pagina_ativa = "🔍 Pesquisar & Explorar"
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {str(e)}")

    # Facilidade: Cadastros rápidos inline fora do formulário principal
    st.divider()
    with st.expander("⚡ Cadastros Rápidos (Pessoa, Assunto ou Palavra-chave)"):
        tab_qp, tab_qa, tab_qk = st.tabs(
            ["+ Nova Pessoa", "+ Novo Assunto", "+ Nova Palavra-chave"]
        )
        with tab_qp:
            col_qp1, col_qp2, col_qp3 = st.columns([2, 3, 1])
            with col_qp1:
                novo_p_nome = st.text_input("Nome da Pessoa", key="qp_nome")
            with col_qp2:
                novo_p_obs = st.text_input("Observações", key="qp_obs")
            with col_qp3:
                st.write("")
                st.write("")
                if st.button("Adicionar", key="btn_qp"):
                    if novo_p_nome.strip():
                        db.criar_pessoa(novo_p_nome, novo_p_obs)
                        st.success(f"Pessoa '{novo_p_nome}' cadastrada!")
                        st.rerun()
        with tab_qa:
            col_qa1, col_qa2 = st.columns([4, 1])
            with col_qa1:
                novo_a_nome = st.text_input("Novo Assunto", key="qa_nome")
            with col_qa2:
                st.write("")
                st.write("")
                if st.button("Adicionar", key="btn_qa"):
                    if novo_a_nome.strip():
                        db.obter_ou_criar_assunto(novo_a_nome)
                        st.success(f"Assunto '{novo_a_nome}' cadastrado!")
                        st.rerun()
        with tab_qk:
            col_qk1, col_qk2 = st.columns([4, 1])
            with col_qk1:
                novo_k_nome = st.text_input("Nova Palavra-chave", key="qk_nome")
            with col_qk2:
                st.write("")
                st.write("")
                if st.button("Adicionar", key="btn_qk"):
                    if novo_k_nome.strip():
                        db.obter_ou_criar_keyword(novo_k_nome)
                        st.success(f"Keyword '{novo_k_nome}' cadastrada!")
                        st.rerun()


# ==============================================================================
# VIEW 3: GESTÃO DE CADASTROS (PESSOAS, ASSUNTOS, KEYWORDS)
# ==============================================================================
elif st.session_state.pagina_ativa == "👥 Gestão de Cadastros":
    st.title("👥 Gestão de Cadastros Básicos")
    st.caption(
        "Gerencie as entidades independentes do sistema: pessoas envolvidas, assuntos e palavras-chave."
    )

    tab_pessoas, tab_assuntos, tab_keywords = st.tabs(
        ["👤 Pessoas", "📁 Assuntos", "🏷️ Palavras-chave"]
    )

    # SUBTAB: PESSOAS
    with tab_pessoas:
        st.subheader("Pessoas Cadastradas")
        lista_p = db.listar_pessoas()

        with st.expander("➕ Cadastrar Nova Pessoa"):
            with st.form("form_nova_pessoa", clear_on_submit=True):
                p_nome = st.text_input("Nome *")
                p_obs = st.text_area("Observações / Cargo / Empresa")
                if st.form_submit_button("Cadastrar Pessoa"):
                    if p_nome.strip():
                        db.criar_pessoa(p_nome, p_obs)
                        st.success(f"Pessoa '{p_nome}' cadastrada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Informe o nome.")

        if lista_p:
            df_p = pd.DataFrame(lista_p)[
                ["id_pessoa", "nome", "observacoes", "criado_em"]
            ]
            st.dataframe(df_p, use_container_width=True, hide_index=True)

            st.write("---")
            st.write("**Excluir Pessoa:**")
            col_del_p1, col_del_p2 = st.columns([3, 1])
            with col_del_p1:
                mapa_del_p = {
                    f"{p['nome']} (ID {p['id_pessoa']})": p["id_pessoa"]
                    for p in lista_p
                }
                pessoa_excluir = st.selectbox(
                    "Selecione a pessoa para excluir", list(mapa_del_p.keys())
                )
            with col_del_p2:
                st.write("")
                st.write("")
                if st.button("Excluir", key="btn_del_pessoa", type="primary"):
                    sucesso, msg = db.excluir_pessoa(
                        mapa_del_p[pessoa_excluir]
                    )
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("Nenhuma pessoa cadastrada ainda.")

    # SUBTAB: ASSUNTOS
    with tab_assuntos:
        st.subheader("Assuntos Cadastrados")
        lista_a = db.listar_assuntos()

        with st.expander("➕ Novo Assunto"):
            col_na1, col_na2 = st.columns([3, 1])
            with col_na1:
                novo_assunto_input = st.text_input(
                    "Nome do Assunto", key="input_na"
                )
            with col_na2:
                st.write("")
                st.write("")
                if st.button("Cadastrar Assunto"):
                    if novo_assunto_input.strip():
                        db.obter_ou_criar_assunto(novo_assunto_input)
                        st.success("Assunto criado!")
                        st.rerun()

        if lista_a:
            df_a = pd.DataFrame(lista_a)[["id_assunto", "nome", "criado_em"]]
            st.dataframe(df_a, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum assunto cadastrado ainda.")

    # SUBTAB: KEYWORDS
    with tab_keywords:
        st.subheader("Palavras-chave (Keywords)")
        lista_k = db.listar_keywords()

        with st.expander("➕ Nova Palavra-chave"):
            col_nk1, col_nk2 = st.columns([3, 1])
            with col_nk1:
                nova_kw_input = st.text_input(
                    "Nome da Palavra-chave", key="input_nk"
                )
            with col_nk2:
                st.write("")
                st.write("")
                if st.button("Cadastrar Palavra-chave"):
                    if nova_kw_input.strip():
                        db.obter_ou_criar_keyword(nova_kw_input)
                        st.success("Palavra-chave criada!")
                        st.rerun()

        if lista_k:
            df_k = pd.DataFrame(lista_k)[["id_keyword", "nome", "criado_em"]]
            st.dataframe(df_k, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma palavra-chave cadastrada ainda.")


# ==============================================================================
# VIEW 4: BACKUP & EXPORTAÇÃO INDEPENDENTE (Etapas 9 e 10)
# ==============================================================================
elif st.session_state.pagina_ativa == "💾 Backup & Exportação":
    st.title("💾 Backup e Exportação Independente")
    st.markdown("""
    Garanta total portabilidade dos seus dados. Esta funcionalidade permite extrair todas as suas conversas, 
    pessoas, assuntos e palavras-chave de forma independente do Supabase, possibilitando restauração em qualquer 
    outro PostgreSQL ou análise de dados com Python/Pandas.
    """)

    timestamp_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")

    col_bk1, col_bk2 = st.columns(2)

    with col_bk1:
        with st.container(border=True):
            st.subheader("📦 Exportação Completa em JSON")
            st.markdown(
                "Exporta todo o banco de dados em formato JSON hierárquico, "
                "preservando integralmente os relacionamentos e metadados das conversas."
            )
            try:
                json_str = db.exportar_tudo_json()
                st.download_button(
                    label="⬇️ Baixar Backup Completo (JSON)",
                    data=json_str,
                    file_name=f"diario_backup_{timestamp_arquivo}.json",
                    mime="application/json",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erro ao gerar JSON: {str(e)}")

    with col_bk2:
        with st.container(border=True):
            st.subheader("📄 Schema do Banco (DDL)")
            st.markdown(
                "Baixe o script SQL para recriar as tabelas, índices e Full Text Search "
                "em qualquer servidor PostgreSQL local ou nuvem."
            )
            schema_sql = db.ler_schema_ddl()
            st.download_button(
                label="⬇️ Baixar Script do Schema (01_schema.sql)",
                data=schema_sql,
                file_name="diario_schema.sql",
                mime="text/plain",
                use_container_width=True,
            )

    st.write("---")
    st.subheader("📊 Exportação de Tabelas em Planilhas CSV")
    st.caption(
        "Baixe as tabelas normalizadas ou o arquivo consolidado de conversas."
    )

    try:
        tabelas_csv = db.exportar_tabelas_csv()
        col_csv1, col_csv2 = st.columns(2)

        with col_csv1:
            # Conversas consolidado
            df_conv = tabelas_csv["conversas_consolidado.csv"]
            csv_conv = df_conv.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar Conversas Consolidado (CSV)",
                data=csv_conv,
                file_name=f"conversas_consolidado_{timestamp_arquivo}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # Pessoas
            df_pes = tabelas_csv["pessoas.csv"]
            csv_pes = df_pes.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar Pessoas (CSV)",
                data=csv_pes,
                file_name=f"pessoas_{timestamp_arquivo}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # Assuntos
            df_ass = tabelas_csv["assuntos.csv"]
            csv_ass = df_ass.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar Assuntos (CSV)",
                data=csv_ass,
                file_name=f"assuntos_{timestamp_arquivo}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_csv2:
            # Keywords
            df_key = tabelas_csv["keywords.csv"]
            csv_key = df_key.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar Palavras-chave (CSV)",
                data=csv_key,
                file_name=f"keywords_{timestamp_arquivo}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # Associativa conversa_assunto
            df_ca = tabelas_csv["conversa_assunto.csv"]
            csv_ca = df_ca.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar Vínculos Conversa-Assunto (CSV)",
                data=csv_ca,
                file_name=f"conversa_assunto_{timestamp_arquivo}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # Associativa conversa_keyword
            df_ck = tabelas_csv["conversa_keyword.csv"]
            csv_ck = df_ck.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Baixar Vínculos Conversa-Keyword (CSV)",
                data=csv_ck,
                file_name=f"conversa_keyword_{timestamp_arquivo}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    except Exception as e:
        st.error(f"Erro ao gerar arquivos CSV: {str(e)}")
