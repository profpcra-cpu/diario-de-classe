import streamlit as st
import pandas as pd
from modulos.conexao import executar_query
# Supondo a existência da função de PDF para o Relatório Geral
from modulos.pdf_generator import gerar_pdf_relatorio_turma 

def renderizar_modulo_relatorio_turma():
    st.markdown("### CEP ESCOLA TÉCNICA DE PLANALTINA")
    st.markdown("#### 📊 Relatório Geral da Turma")
    st.markdown("---")

    # 1. Filtro Principal por Turma
    col_turma, col_sem = st.columns([2, 1])
    with col_turma:
        turma_selecionada = st.text_input("Código da Turma:", value="26201A", key="input_relatorio_turma")
    with col_sem:
        semestre_filtro = st.text_input("Semestre (Opcional):", value="Todos", key="input_relatorio_semestre")

    # Botão para consultar e carregar os dados
    if st.button("🔍 Gerar Relatório da Turma"):
        try:
            # Consulta 1: Dados Cadastrais dos Alunos da Turma
            query_pessoas = """
                SELECT * 
                FROM TB_PESSOAS 
                WHERE turma = %s
                ORDER BY nome
            """
            df_pessoas = executar_query(query_pessoas, params=(turma_selecionada,))

            if df_pessoas.empty:
                st.warning(f"Nenhum aluno encontrado na TB_PESSOAS para a turma '{turma_selecionada}'.")
                st.session_state['relatorio_turma_dados'] = None
            else:
                # Se a coluna 'situacao' não existir na tabela, cria uma coluna padronizada
                if 'situacao' not in df_pessoas.columns:
                    df_pessoas['situacao'] = 'N/A'

                # Consulta 2: Diário completo da Turma
                if semestre_filtro != "Todos" and semestre_filtro.strip() != "":
                    query_diario = """
                        SELECT matricula, iduc, unidade_curricular, faltas, conceito, semestre
                        FROM TB_DIARIO 
                        WHERE turma = %s AND semestre = %s
                    """
                    df_diario = executar_query(query_diario, params=(turma_selecionada, semestre_filtro))
                else:
                    query_diario = """
                        SELECT matricula, iduc, unidade_curricular, faltas, conceito, semestre
                        FROM TB_DIARIO 
                        WHERE turma = %s
                    """
                    df_diario = executar_query(query_diario, params=(turma_selecionada,))

                # Processamento da Matriz de Notas/Faltas (Pivot)
                df_matriz_turma = pd.DataFrame()
                if not df_diario.empty:
                    mapa_uc = df_diario.set_index('iduc')['unidade_curricular'].to_dict()

                    df_faltas = df_diario.pivot_table(index='matricula', columns='iduc', values='faltas', aggfunc='sum')
                    df_conceitos = df_diario.pivot_table(index='matricula', columns='iduc', values='conceito', aggfunc='first')

                    dfs_juntar = [df_pessoas.set_index('matricula')]

                    for iduc in df_faltas.columns:
                        nome_uc = mapa_uc.get(iduc, f"UC {iduc}")
                        df_f = df_faltas[[iduc]].rename(columns={iduc: f"{nome_uc} (Faltas)"})
                        df_c = df_conceitos[[iduc]].rename(columns={iduc: f"{nome_uc} (Conceito)"})
                        dfs_juntar.extend([df_f, df_c])

                    df_matriz_turma = pd.concat(dfs_juntar, axis=1).reset_index()

                    # REMOVE COLUNAS DUPLICADAS PARA EVITAR ERRO NO ST.DATAFRAME
                    df_matriz_turma = df_matriz_turma.loc[:, ~df_matriz_turma.columns.duplicated()].copy()

                # Guardar todos os DataFrames no Session State
                st.session_state['relatorio_turma_dados'] = {
                    'turma': turma_selecionada,
                    'semestre': semestre_filtro,
                    'df_pessoas': df_pessoas,
                    'df_diario': df_diario,
                    'df_matriz': df_matriz_turma
                }
                st.success(f"Relatório carregado com sucesso para a Turma {turma_selecionada}!")

        except Exception as e:
            st.error(f"Erro ao gerar relatório da turma: {e}")

    # 2. Renderização das Informações (se carregadas)
    dados = st.session_state.get('relatorio_turma_dados')
    if dados and dados['turma'] == turma_selecionada:
        
        df_pessoas = dados['df_pessoas']
        df_diario = dados['df_diario']
        df_matriz = dados['df_matriz']

        # Painel de Métricas Rápidas (KPIs)
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Alunos", len(df_pessoas))
        
        if 'situacao' in df_pessoas.columns:
            ativos = len(df_pessoas[df_pessoas['situacao'].astype(str).str.upper() == 'ATIVO']) if not df_pessoas.empty else 0
            m2.metric("Alunos Ativos", ativos)
        else:
            m2.metric("Alunos Ativos", "N/A")

        # Tratamento seguro para valores de faltas (evita erro com NaN / None)
        if not df_diario.empty and 'faltas' in df_diario.columns:
            faltas_numericas = pd.to_numeric(df_diario['faltas'], errors='coerce').fillna(0)
            total_faltas = int(faltas_numericas.sum())
            media_faltas = round(faltas_numericas.mean(), 1) if len(faltas_numericas) > 0 else 0
            
            m3.metric("Total de Faltas", total_faltas)
            m4.metric("Média de Faltas / UC", media_faltas)
        else:
            m3.metric("Total de Faltas", 0)
            m4.metric("Média de Faltas", 0)

        # Abas de Exibição
        tab_matriz, tab_alunos, tab_resumo = st.tabs([
            "📋 Matriz Consolidada", 
            "👥 Relação de Alunos", 
            "📈 Análise do Diário"
        ])

        with tab_matriz:
            st.markdown("#### Visão Matricial (Desempenho e Frequência por UC)")
            if not df_matriz.empty:
                # Garante que não existem colunas duplicadas antes da exibição
                df_matriz_exibir = df_matriz.loc[:, ~df_matriz.columns.duplicated()].copy()
                st.dataframe(df_matriz_exibir, use_container_width=True)
            else:
                st.info("Nenhum lançamento de diário encontrado para gerar a matriz.")

        with tab_alunos:
            st.markdown("#### Dados Cadastrais dos Estudantes da Turma")
            if not df_pessoas.empty:
                df_pessoas_exibir = df_pessoas.loc[:, ~df_pessoas.columns.duplicated()].copy()
                st.dataframe(df_pessoas_exibir, use_container_width=True)

        with tab_resumo:
            st.markdown("#### Registros Detalhados do Diário")
            if not df_diario.empty:
                df_diario_exibir = df_diario.loc[:, ~df_diario.columns.duplicated()].copy()
                st.dataframe(df_diario_exibir, use_container_width=True)
            else:
                st.info("Sem registros no diário.")

        # Ações do Relatório (Exportação)
        st.markdown("---")
        col_exp1, col_exp2 = st.columns([1, 1])
        
        with col_exp1:
            # Botão de Download em Excel/CSV
            if not df_matriz.empty:
                csv_data = df_matriz.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📊 Descarregar Tabela (CSV)",
                    data=csv_data,
                    file_name=f"Relatorio_Turma_{turma_selecionada}.csv",
                    mime="text/csv"
                )
            else:
                st.write("")

        with col_exp2:
            # Botão de Download do PDF do Relatório da Turma
            try:
                pdf_bytes = gerar_pdf_relatorio_turma(dados)
                st.download_button(
                    label="📄 Descarregar Relatório Completo (PDF)",
                    data=pdf_bytes,
                    file_name=f"Relatorio_Geral_Turma_{turma_selecionada}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.warning("Função de PDF geral pendente de configuração.")
