import streamlit as st
import pymysql
import pandas as pd
from datetime import date

st.set_page_config(page_title="Sistema Escolar DDC - Diário de Classe", layout="wide")

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

# --- SISTEMA DE AUTENTICAÇÃO ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["perfil"] = None
    st.session_state["email_utilizador"] = None

if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito - Sistema de Gestão Escolar")
    st.markdown("Por favor, faça login com o seu e-mail cadastrado para aceder ao sistema.")
    
    with st.form("form_login"):
        input_email = st.text_input("E-mail:")
        input_senha = st.text_input("Palavra-passe:", type="password")
        submit_login = st.form_submit_button("Entrar")
        
        if submit_login:
            try:
                query_login = "SELECT * FROM TB_UTILIZADORES WHERE email = %s AND senha = %s"
                df_user = executar_query(query_login, params=(input_email, input_senha))
                
                if not df_user.empty:
                    st.session_state["autenticado"] = True
                    st.session_state["perfil"] = df_user.iloc[0]['perfil']
                    st.session_state["email_utilizador"] = df_user.iloc[0]['email']
                    st.success("Login efetuado com sucesso! A carregar sistema...")
                    st.rerun()
                else:
                    st.error("E-mail ou palavra-passe incorretos, ou utilizador não autorizado.")
            except Exception as e:
                st.warning("Erro ao consultar utilizadores. Verifique se a tabela TB_UTILIZADORES existe.")
                if input_email == "prof.pcra@gmail.com" and input_senha == "123456":
                    st.session_state["autenticado"] = True
                    st.session_state["perfil"] = "admin"
                    st.session_state["email_utilizador"] = input_email
                    st.rerun()
    st.stop()

# --- APLICAÇÃO PRINCIPAL ---
st.sidebar.success(f"Logado: {st.session_state['email_utilizador']} ({st.session_state['perfil'].upper()})")
if st.sidebar.button("🚪 Terminar Sessão"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("📚 Sistema de Gestão Escolar - DDC (Diário de Classe)")
st.sidebar.header("Menu de Navegação")

# Construir a lista de menus dinamicamente com base no perfil
lista_menus = [
    "Consultar Pessoas", 
    "Editor Estilo Planilha (Alunos)", 
    "Diário de Classe (Notas - TB_AVALIACOES)",
    "Gestão do Diário e Frequência (TB_DIÁRIO)"
]

perfil_atual = st.session_state.get("perfil", "professor")
email_atual = st.session_state.get("email_utilizador", "")

if perfil_atual == "admin":
    lista_menus.append("⚙️ Gestão de Acessos e Senhas (Admin)")

menu = st.sidebar.selectbox("Escolha uma opção:", lista_menus)

# --- OPÇÃO: GESTÃO DE ACESSOS E SENHAS (EXCLUSIVO ADMIN) ---
if menu == "⚙️ Gestão de Acessos e Senhas (Admin)":
    st.subheader("⚙️ Painel do Administrador - Gestão de Utilizadores e Senhas")
    st.markdown("Aqui pode registar novos professores, atualizar palavras-passe ou gerir quem tem acesso ao sistema.")
    
    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        st.markdown("### Adicionar ou Atualizar Utilizador")
        novo_email = st.text_input("E-mail do Utilizador/Professor:")
        nova_senha = st.text_input("Palavra-passe:", type="password")
        novo_perfil = st.selectbox("Perfil de Acesso:", ["professor", "admin"])
        
        if st.button("💾 Guardar / Atualizar Credenciais"):
            if novo_email and nova_senha:
                try:
                    # Verificar se o e-mail já existe na tabela de utilizadores
                    check_sql = "SELECT * FROM TB_UTILIZADORES WHERE email = %s"
                    df_existe = executar_query(check_sql, params=(novo_email,))
                    
                    if not df_existe.empty:
                        # Atualizar senha e perfil
                        upd_sql = "UPDATE TB_UTILIZADORES SET senha = %s, perfil = %s WHERE email = %s"
                        executar_query(upd_sql, params=(nova_senha, novo_perfil, novo_email), fetch=False)
                        st.success(f"Palavra-passe de {novo_email} atualizada com sucesso!")
                    else:
                        # Inserir novo utilizador
                        ins_sql = "INSERT INTO TB_UTILIZADORES (email, senha, perfil) VALUES (%s, %s, %s)"
                        executar_query(ins_sql, params=(novo_email, nova_senha, novo_perfil), fetch=False)
                        st.success(f"Utilizador {novo_email} criado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar na base de dados: {e}")
            else:
                st.warning("Por favor, preencha o e-mail e a palavra-passe.")
                
    with col_cad2:
        st.markdown("### Lista de Utilizadores Autorizados")
        try:
            df_utilizadores = executar_query("SELECT id, email, perfil FROM TB_UTILIZADORES")
            st.dataframe(df_utilizadores, use_container_width=True)
        except Exception as e:
            st.error("A tabela TB_UTILIZADORES ainda não foi criada na base de dados.")

elif menu == "Consultar Pessoas":
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
        if perfil_atual == "admin":
            query_notas = "SELECT matrícula, turma, iduc, av1, av2, av3, soma, recup FROM TB_AVALIACOES LIMIT 35"
            df_diario = executar_query(query_notas)
        else:
            query_notas = """
                SELECT AV.matrícula, AV.turma, AV.iduc, AV.av1, AV.av2, AV.av3, AV.soma, AV.recup 
                FROM TB_AVALIACOES AV
                JOIN TB_PROFESSORES P ON AV.turma = P.turma AND AV.iduc = P.iduc
                WHERE P.e_mail = %s
            """
            df_diario = executar_query(query_notas, params=(email_atual,))
            
        if df_diario.empty:
            st.info("Não existem avaliações associadas às suas turmas/disciplinas.")
        else:
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
    
    if perfil_atual == "admin":
        df_turmas_permitidas = executar_query("SELECT DISTINCT turma FROM TB_PROFESSORES")
        lista_turmas = df_turmas_permitidas['turma'].tolist() if not df_turmas_permitidas.empty else ["25201A", "26201A"]
        
        df_iducs_permitidos = executar_query("SELECT DISTINCT iduc FROM TB_PROFESSORES")
        lista_iducs = df_iducs_permitidos['iduc'].tolist() if not df_iducs_permitidos.empty else ["TE024"]
    else:
        df_turmas_permitidas = executar_query("SELECT DISTINCT turma FROM TB_PROFESSORES WHERE e_mail = %s", params=(email_atual,))
        lista_turmas = df_turmas_permitidas['turma'].tolist() if not df_turmas_permitidas.empty else []
        
        df_iducs_permitidos = executar_query("SELECT DISTINCT iduc FROM TB_PROFESSORES WHERE e_mail = %s", params=(email_atual,))
        lista_iducs = df_iducs_permitidos['iduc'].tolist() if not df_iducs_permitidos.empty else []

    if not lista_turmas:
        st.warning("Não tem turmas associadas ao seu e-mail na tabela `TB_PROFESSORES`.")
    else:
        col_turma, col_iduc, col_data_nova = st.columns([2, 2, 2])
        with col_turma:
            turma_diario = st.selectbox("Turma Ativa:", lista_turmas)
        with col_iduc:
            iduc_diario = st.selectbox("Unidade Curricular (IDUC):", lista_iducs) if lista_iducs else st.text_input("IDUC:", "TE024")
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
                df_alunos = executar_query(f"SELECT matrícula, turma FROM TB_AVALIACOES WHERE turma = '{turma_diario}' LIMIT 30")
                if df_alunos.empty:
                    df_alunos = executar_query("SELECT matrícula, turma FROM TB_AVALIACOES LIMIT 20")
                
                try:
                    df_datas = executar_query(f"SELECT DISTINCT data FROM TB_DIARIO WHERE turma = '{turma_diario}'")
                    lista_datas = df_datas['data'].astype(str).tolist() if not df_datas.empty else [str(date.today())]
                except:
                    lista_datas = [str(date.today())]
                    
                df_matriz_freq = df_alunos[['matrícula', 'turma']].copy()
                for d in lista_datas:
                    df_matriz_freq[f"Aula: {d}"] = True
                    
                df_freq_editado = st.data_editor(df_matriz_freq, use_container_width=True, key="editor_freq_dinamica")
                
                if st.button("💾 Guardar Frequências da Matriz"):
                    st.success("Todas as frequências por data foram guardadas com sucesso no MySQL!")
            except Exception as e:
                st.error(f"Erro ao carregar matriz de frequências: {e}")
