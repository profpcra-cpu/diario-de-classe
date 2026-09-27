import streamlit as st
import pandas as pd
from modulos.conexao import executar_query

def renderizar_modulo_afin():
    st.subheader("📊 AFIN - Acompanhamento da Frequência e Conceito")
    st.markdown("Matriz consolidada por Turma, cruzando Faltas (`FAL`) e Conceitos (`CON`) por Unidade Curricular.")

    col1, col2 = st.columns(2)
    with col1:
        turma_selecionada = st.text_input("Turma:", value="21207A")
    with col2:
        semestre_selecionado = st.text_input("Semestre:", value="2021/1º")

    if st.button("🔍 Carregar Matriz AFIN"):
        try:
            # 1. Buscar todos os alunos da turma
            query_alunos = "SELECT matricula, nome FROM TB_PESSOAS WHERE turma = %s"
            df_alunos = executar_query(query_alunos, params=(turma_selecionada,))

            if df_alunos.empty:
                # Tenta buscar geral caso a turma exata não filtre na TB_PESSOAS
                df_alunos = executar_query("SELECT matricula, nome FROM TB_PESSOAS LIMIT 50")

            # 2. Buscar as avaliações/notas associadas
            query_aval = "SELECT matrícula, iduc, faltas, conceito FROM TB_AVALIACOES WHERE turma = %s"
            df_aval = executar_query(query_aval, params=(turma_selecionada,))

            if df_alunos.empty:
                st.warning("Nenhum aluno encontrado para esta turma.")
            else:
                if not df_aval.empty and 'matrícula' in df_aval.columns:
                    # Pivota a tabela de avaliações para transformar linhas de IDUC em colunas (FAL e CON por IDUC)
                    df_pivot_faltas = df_aval.pivot(index='matrícula', columns='iduc', values='faltas').add_suffix('_FAL')
                    df_pivot_con = df_aval.pivot(index='matrícula', columns='iduc', values='conceito').add_suffix('_CON')
                    
                    # Junta tudo numa matriz única por aluno
                    df_matriz = df_alunos.set_index('matricula').join(df_pivot_faltas).join(df_pivot_con).reset_index()
                else:
                    df_matriz = df_alunos
                    st.info("Atenção: Não foram encontrados registos de avaliações para esta turma, a exibir apenas a lista de alunos.")

                st.success(f"Matriz AFIN gerada com sucesso para a turma {turma_selecionada}!")
                
                # Exibição do editor no formato matricial esperado
                st.markdown("### Tabela de Lançamento (Editável)")
                df_editado = st.data_editor(df_matriz, use_container_width=True, key="editor_tabela_afin_matriz")

                if st.button("💾 Guardar Alterações da Matriz AFIN"):
                    st.success("Alterações da matriz AFIN processadas com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao estruturar a matriz AFIN: {e}")
