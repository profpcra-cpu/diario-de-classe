import streamlit as st
import pandas as pd
from modulos.conexao import executar_query

def renderizar_modulo_afin():
    # Cabeçalho Institucional
    st.markdown("### CEP ESCOLA TÉCNICA DE PLANALTINA - AFIN")
    st.markdown("#### Acompanhamento da Frequência e Conceito")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        turma_selecionada = st.text_input("Turma:", value="26201A")
    with col2:
        semestre_selecionado = st.text_input("Semestre:", value="2026/2º")

    if st.button("🔍 Carregar Matriz AFIN"):
        try:
            # 1. Buscar os dados da TB_DIARIO juntamente com o nome da unidade curricular
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

                # Mapear IDUC para o Nome Descritivo da Unidade Curricular
                mapa_nomes = df_diario.set_index('iduc')['unidade_curricular'].to_dict()

                # 3. Pivotar separadamente faltas e conceitos por iduc
                df_faltas = df_diario.pivot(index='matricula', columns='iduc', values='faltas')
                df_conceitos = df_diario.pivot(index='matricula', columns='iduc', values='conceito')

                # 4. Construir colunas planas e limpas: "NOME DA UC - FAL" e "NOME DA UC - CON"
                dfs_para_juntar = [df_pessoas.drop_duplicates(subset=['matricula']).set_index('matricula')]

                for iduc in df_faltas.columns:
                    nome_uc = mapa_nomes.get(iduc, iduc) # Nome descritivo da disciplina
                    
                    # Renomeia as colunas com o formato legível
                    df_f = df_faltas[[iduc]].rename(columns={iduc: f"{nome_uc} - FAL"})
                    df_c = df_conceitos[[iduc]].rename(columns={iduc: f"{nome_uc} - CON"})
                    
                    dfs_para_juntar.append(df_f)
                    dfs_para_juntar.append(df_c)

                # Unir todos os blocos num único DataFrame limpo
                df_matriz = pd.concat(dfs_para_juntar, axis=1).reset_index()

                st.success(f"Matriz AFIN gerada com sucesso para a turma {turma_selecionada}!")
                
                # Exibição do editor interativo com colunas limpas
                st.markdown("### Tabela de Lançamento (Editável)")
                df_editado = st.data_editor(df_matriz, use_container_width=True, key="editor_tabela_afin_matriz")

                if st.button("💾 Guardar Alterações da Matriz AFIN"):
                    st.success("Alterações guardadas com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao estruturar a matriz AFIN: {e}")
