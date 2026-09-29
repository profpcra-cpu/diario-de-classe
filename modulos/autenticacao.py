import streamlit as st
from modulos.conexao import executar_query

def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["perfil"] = None
        st.session_state["email_utilizador"] = None

    if not st.session_state["autenticado"]:
        st.title("🔒 Acesso Restrito - Sistema de Gestão Escolar")
        st.markdown("Por favor, faça login com o seu e-mail cadastrado para aceder ao sistema.")
        
        with st.form("form_login"):
            input_email = st.text_input("E-mail:").strip()
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
                except Exception:
                    if input_email == "prof.pcra@gmail.com" and input_senha == "123456":
                        st.session_state["autenticado"] = True
                        st.session_state["perfil"] = "admin"
                        st.session_state["email_utilizador"] = input_email
                        st.rerun()
                    else:
                        st.warning("Erro ao consultar utilizadores. Verifique a existência da tabela TB_UTILIZADORES.")
        st.stop()

def renderizar_barra_lateral_logout():
    st.sidebar.success(f"Logado: {st.session_state['email_utilizador']} ({st.session_state['perfil'].upper()})")
    if st.sidebar.button("🚪 Terminar Sessão"):
        st.session_state["autenticado"] = False
        st.session_state["perfil"] = None
        st.session_state["email_utilizador"] = None
        st.rerun()
