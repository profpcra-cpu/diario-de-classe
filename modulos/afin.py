import streamlit as st
import pandas as pd
from modulos.conexao import executar_query

def renderizar_modulo_afin():
    st.subheader("📊 AFIN - Acompanhamento da Frequência e Conceito")
    st.markdown("Matriz consolidada por Turma e Semestre, cruzando Faltas (`FAL`) e Conceitos/Resultados (`CON`) por Unidade Curricular.")

    # Filtros de Seleção (Turma e Semestre)
    col1, col2 = st.columns(2)
    with col1:
        turma_selecionada = st.text_input("Turma:", value="21207A")
    with col2:
        semestre_selecionado = st.text_input("Semestre:", value="2021/1º")

    if st.button("🔍 Carregar Matriz AFIN"):
        try:
            # Query para buscar os dados dos alunos e respetivas avaliações/frequências da turma
            query_afin = """
                SELECT P.matricula, P.nome, A.iduc, A.av1, A.av2, A.av3, A.soma, A.recup, A.conceito
                FROM TB_PESSOAS P
                LEFT JOIN TB_AVALIACOES A ON P.matricula = A.matrícula
                WHERE P.turma = %s OR A.turma = %s
                LIMIT 50
            """
            df_afin = executar_query(query_afin, params=(turma_selecionada, turma_selecionada))

            if df_afin.empty:
                st.warning("Nenhum registo encontrado para os filtros selecionados.")
            else:
                st.success(f"Matriz carregada com sucesso para a turma {turma_selecionada}!")
                
                # Exibição do editor interativo no formato tabela cruzada da AFIN
                st.markdown("### Tabela de Lançamento (Editável)")
                df_editado = st.data_editor(df_afin, use_container_width=True, key="editor_tabela_afin")

                if st.button("💾 Guardar Alterações da Matriz AFIN"):
                    # Lógica de atualização em lote no MySQL
                    atualizacoes = 0
                    for _, row in df_editado.iterrows():
                        mat = row.get('matricula')
                        iduc = row.get('iduc')
                        if mat and iduc:
                            sql_upd = """
                                UPDATE TB_AVALIACOES 
                                SET av1 = %s, av2 = %s, av3 = %s, soma = %s, recup = %s, conceito = %s 
                                WHERE matrícula = %s AND iduc = %s
                            """
                            executar_query(
                                sql_upd, 
                                params=(
                                    row.get('av1', 0), 
                                    row.get('av2', 0), 
                                    row.get('av3', 0), 
                                    row.get('soma', 0), 
                                    row.get('recup', 0), 
                                    row.get('conceito', ''), 
                                    mat, 
                                    iduc
                                ), 
                                fetch=False
                            )
                            atualizacoes += 1
                    st.success(f"Sucesso! {atualizacoes} registos atualizados na base de dados.")
        
        except Exception as e:
            st.error(f"Erro ao carregar a matriz AFIN: {e}")
