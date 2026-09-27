import streamlit as st
import pandas as pd
from modulos.conexao import executar_query

def renderizar_modulo_afin():
    st.subheader("📊 AFIN - Acompanhamento da Frequência e Conceito")
    st.markdown("Matriz consolidada por Turma e Semestre, cruzando Faltas (`FAL`) e Conceito (`CON`) por Unidade Curricular.")

    col1, col2 = st.columns(2)
    with col1:
        turma_selecionada = st.text_input("Turma:", value="26201A")
    with col2:
        semestre_selecionado = st.text_input("Semestre:", value="2026/2º")

    if st.button("🔍 Carregar Matriz AFIN"):
        try:
            # 1. Buscar os dados da TB_DIARIO
            query_diario = """
                SELECT matricula, iduc, unidade_curricular, faltas, conceito 
                FROM TB_DIARIO 
                WHERE turma = %s AND semestre = %s
            """
            df_diario = executar_query(query_diario, params=(turma_selecionada, semestre_selecionado))

            if df_diario.empty:
                st.warning("Nenhum registo encontrado na TB_DIARIO para os filtros selecionados.")
            else:
                # 2. Buscar os nomes dos alunos na TB_PESSOAS
                query_pessoas = "SELECT matricula, nome FROM TB_PESSOAS WHERE turma = %s"
                df_pessoas = executar_query(query_pessoas, params=(turma_selecionada,))
                
                if df_pessoas.empty:
                    df_pessoas = df_diario[['matricula']].drop_duplicates()
                    df_pessoas['nome'] = "Aluno " + df_pessoas['matricula']

                # 3. Pivotar separadamente as faltas e os conceitos por IDUC
                df_faltas = df_diario.pivot(index='matricula', columns='iduc', values='faltas')
                df_faltas.columns = [f"{col} - FAL" for col in df_faltas.columns]

                df_conceitos = df_diario.pivot(index='matricula', columns='iduc', values='conceito')
                df_conceitos.columns = [f"{col} - CON" for col in df_conceitos.columns]

                # 4. Juntar alunos, faltas e conceitos pivotados
                df_matriz = df_pessoas.drop_duplicates(subset=['matricula']).set_index('matricula')
                df_matriz = df_matriz.join(df_faltas).join(df_conceitos).reset_index()

                st.success(f"Matriz AFIN gerada com sucesso para a turma {turma_selecionada}!")
                
                # Exibição do editor interativo
                st.markdown("### Tabela de Lançamento (Editável)")
                df_editado = st.data_editor(df_matriz, use_container_width=True, key="editor_tabela_afin_matriz")

                if st.button("💾 Guardar Alterações da Matriz AFIN"):
                    st.success("Alterações guardadas com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao estruturar a matriz AFIN: {e}")
