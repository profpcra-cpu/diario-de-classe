import streamlit as st
from modulos.conexao import executar_query

def renderizar_modulo_admin():
    st.subheader("⚙️ Painel do Administrador - Gestão de Utilizadores e Senhas")
    st.markdown("Registe novos professores, atualize palavras-passe ou gira os acessos ao sistema.")
    
    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        st.markdown("### Adicionar ou Atualizar Utilizador")
        novo_email = st.text_input("E-mail do Utilizador/Professor:").strip()
        nova_senha = st.text_input("Palavra-passe:", type="password")
        novo_perfil = st.selectbox("Perfil de Acesso:", ["professor", "admin"])
        
        if st.button("💾 Guardar / Atualizar Credenciais"):
            if novo_email and nova_senha:
                try:
                    check_sql = "SELECT * FROM TB_UTILIZADORES WHERE email = %s"
                    df_existe = executar_query(check_sql, params=(novo_email,))
                    
                    if not df_existe.empty:
                        upd_sql = "UPDATE TB_UTILIZADORES SET senha = %s, perfil = %s WHERE email = %s"
                        executar_query(upd_sql, params=(nova_senha, novo_perfil, novo_email), fetch=False)
                        st.success(f"Palavra-passe de {novo_email} atualizada com sucesso!")
                    else:
                        ins_sql = "INSERT INTO TB_UTILIZADORES (email, senha, perfil) VALUES (%s, %s, %s)"
                        executar_query(ins_sql, params=(novo_senha, nova_senha, novo_perfil), fetch=False)
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
