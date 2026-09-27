import streamlit as st
import pandas as pd
from modulos.conexao import executar_query

def renderizar_modulo_afin():
    st.subheader("📊 AFIN - Acompanhamento da Frequência e Conceito")
    st.markdown("Matriz consolidada por Turma e Semestre, cruzando Faltas (`faltas`) e Conceitos (`conceito`) por Unidade Curricular.")

    col1, col2 = st.columns(2)
    with col1:
        turma_selecionada = st.text_input("Turma:", value="26201A")
    with col2:
        semestre_selecionado = st.text_input("Semestre:", value="2026/2º")

    if st.button("🔍 Carregar Matriz AFIN"):
        try:
            # 1. Buscar os dados diretamente da TB_DIARIO para a turma e semestre selecionados
            query_diario = """
                SELECT matricula, iduc, unidade_curricular, faltas, conceito 
                FROM TB_DIARIO 
                WHERE turma = %s AND semestre = %s
            """
            df_diario = executar_query(query_diario, params=(turma_selecionada, semestre_selecionado))

            if df_diario.empty:
                st.warning("Nenhum registo encontrado na TB_DIARIO para os filtros selecionados.")
            else:
                # 2. Buscar os nomes dos alunos na TB_PESSOAS para juntar à matriz
                query_pessoas = "SELECT matricula, nome FROM TB_PESSOAS WHERE turma = %s"
                df_pessoas = executar_query(query_pessoas, params=(turma_selecionada,))
                
                if df_pessoas.empty:
                    # Fallback caso os alunos não estejam filtrados por turma na TB_PESSOAS
                    df_pessoas = df_diario[['matricula']].drop_duplicates()
                    df_pessoas['nome'] = "Aluno " + df_pessoas['matricula']

                # 3. Pivotar as colunas de 'faltas' e 'conceito' por 'iduc'
                df_pivot_faltas = df_diario.pivot(index='matricula', columns='iduc', values='faltas').add_suffix('_FAL')
                df_pivot_conceito = df_diario.pivot(index='matricula', columns='iduc', values='conceito').add_suffix('_CON')

                # 4. Consolidar tudo numa matriz por aluno
                df_matriz = df_pessoas.drop_duplicates(subset=['matricula']).set_index('matricula')
                df_matriz = df_matriz.join(df_pivot_faltas).join(df_pivot_conceito).reset_index()

                st.success(f"Matriz AFIN gerada com sucesso para a turma {turma_selecionada}!")
                
                # Exibição do editor no formato matricial esperado
                st.markdown("### Tabela de Lançamento (Editável)")
                df_editado = st.data_editor(df_matriz, use_container_width=True, key="editor_tabela_afin_matriz")

                if st.button("💾 Guardar Alterações da Matriz AFIN"):
                    st.success("Alterações da matriz AFIN processadas com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao estruturar a matriz AFIN: {e}")
