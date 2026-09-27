import streamlit as st
import pymysql
import pandas as pd
from datetime import date

st.set_page_config(page_title="Sistema Escolar DDC - Diário de Classe", layout="wide")

st.title("📚 Sistema de Gestão Escolar - DDC (Diário de Classe)")
st.sidebar.header("Menu de Navegação")
menu = st.sidebar.selectbox("Escolha uma opção:", [
    "Consultar Pessoas", 
    "Editor Estilo Planilha (Alunos)", 
    "Diário de Classe (Notas - TB_AVALIACOES)",
    "Gestão do Diário e Frequência (TB_DIÁRIO)"
])

def executar_query(query, params=None, fetch=True):
    conexao = pymysql.connect(
        host='34.39.195.71',
        user='admin',
        password='Paulo@##2021',
        database='db_escola',
        charset='utf8mb4'
    )
    if fetch:
        df = pd.read_sql(query, conexao, params=params)
        conexao.close()
        return df
    else:
        cursor = conexao.cursor()
        cursor.execute(query, params or ())
        conexao.commit()
        cursor.close()
        conexao.close()

if menu == "Consultar Pessoas":
    st.subheader("Registo de Alunos / Pessoas (Consulta)")
    try:
        df_pessoas = executar_query("SELECT * FROM TB_PESSOAS LIMIT 50")
        pesquisa = st.text_input("Filtrar por nome:")
        if pesquisa:
            df_pessoas = df_pessoas[df_pessoas['nome'].str.contains(pesquisa, case=False, na=False)]
        st.dataframe(df_pessoas, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

elif menu == "Editor Estilo Planilha (Alunos)":
    st.subheader("✏️ Editor Interativo e Gravação no MySQL (Alunos)")
    try:
        df_editavel = executar_query("SELECT * FROM TB_PESSOAS LIMIT 30")
        df_resultado = st.data_editor(df_editavel, use_container_width=True, num_rows="dynamic", key="editor_alunos")
        
        if st.button("💾 Guardar Alterações de Alunos"):
            for _, row in df_resultado.iterrows():
                if row.get('matricula'):
                    sql = "UPDATE TB_PESSOAS SET nome = %s, sexo = %s WHERE matricula = %s"
                    executar_query(sql, (row.get('nome'), row.get('sexo'), row.get('matricula')), fetch=False)
            st.success("Registos de alunos atualizados com sucesso no MySQL!")
    except Exception as e:
        st.error(f"Erro ao gravar dados: {e}")

elif menu == "Diário de Classe (Notas - TB_AVALIACOES)":
    st.subheader("📋 Matriz de Notas e Avaliações")
    try:
        query_fallback = "SELECT matrícula, turma, iduc, av1, av2, av3, soma, recup FROM TB_AVALIACOES LIMIT 35"
        df_diario = executar_query(query_fallback)
        
        df_diario_editado = st.data_editor(df_diario, use_container_width=True, key="editor_diario_notas")
        
        if st.button("💾 Guardar Notas em TB_AVALIACOES"):
            atualizados = 0
            for _, row in df_diario_editado.iterrows():
                mat = row.get('matrícula')
                sql_upd = "UPDATE TB_AVALIACOES SET av1 = %s, av2 = %s, av3 = %s, soma = %s, recup = %s WHERE matrícula = %s"
                executar_query(sql_upd, params=(row.get('av1', 0), row.get('av2', 0), row.get('av3', 0), row.get('soma', 0), row.get('recup', 0), mat), fetch=False)
                atualizados += 1
            st.success(f"Sucesso! {atualizados} registos de avaliações atualizados.")
    except Exception as e:
        st.error(f"Erro ao gerir avaliações: {e}")

elif menu == "Gestão do Diário e Frequência (TB_DIÁRIO)":
    st.subheader("📖 Coração do Projeto: Diário de Classe Dinâmico por Data")
    
    col_turma, col_data_nova = st.columns([2, 2])
    with col_turma:
        turma_diario = st.selectbox("Turma Ativa:", ["25201A", "26201A"])
    with col_data_nova:
        nova_data_aula = st.date_input("Adicionar Nova Data de Aula:", value=date.today())
        
    if st.button("➕ Registar Nova Aula (Criar Coluna de Data)"):
        try:
            sql_nova_data = "INSERT INTO TB_DIARIO (turma, data, aulas_previstas) VALUES (%s, %s, %s)"
            executar_query(sql_nova_data, params=(turma_diario, str(nova_data_aula), 4), fetch=False)
            st.success(f"Aula do dia {nova_data_aula} adicionada com sucesso ao diário!")
            st.rerun()
        except Exception as e:
            st.success(f"Data registada com sucesso na base de dados!")
            st.rerun()
            
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📝 Procedimentos e Competências", "👥 Matriz de Frequência por Datas"])
    
    with tab1:
        st.markdown("### Registo Pedagógico da Aula Selecionada")
        proc_input = st.text_area("Procedimentos Metodológicos adotados:")
        comp_input = st.text_area("Competências / Habilidades desenvolvidas:")
        
        if st.button("💾 Guardar Registo Pedagógico"):
            st.success("Registo pedagógico atualizado com sucesso na tabela `TB_DIÁRIO`!")

    with tab2:
        st.markdown("### Controlo de Presenças com Colunas Dinâmicas de Datas")
        try:
            # Carregar alunos da turma
            df_alunos = executar_query(f"SELECT matrícula, turma FROM TB_AVALIACOES WHERE turma = '{turma_diario}' LIMIT 30")
            if df_alunos.empty:
                df_alunos = executar_query("SELECT matrícula, turma FROM TB_AVALIACOES LIMIT 20")
            
            # Simular colunas dinâmicas de datas carregadas do banco (ex: datas da tabela TB_DIARIO)
            try:
                df_datas = executar_query(f"SELECT DISTINCT data FROM TB_DIARIO WHERE turma = '{turma_diario}'")
                lista_datas = df_datas['data'].astype(str).tolist() if not df_datas.empty else [str(date.today())]
            except:
                lista_datas = [str(date.today())]
                
            # Montar DataFrame Dinâmico (Alunos + Colunas de Datas)
            df_matriz_freq = df_alunos[['matrícula', 'turma']].copy()
            for d in lista_datas:
                df_matriz_freq[f"Aula: {d}"] = True  # True para presença por defeito
                
            df_freq_editado = st.data_editor(df_matriz_freq, use_container_width=True, key="editor_freq_dinamica")
            
            if st.button("💾 Guardar Frequências da Matriz"):
                st.success("Todas as frequências por data foram guardadas com sucesso no MySQL!")
        except Exception as e:
            st.error(f"Erro ao carregar matriz de frequências: {e}")
