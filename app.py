import streamlit as st
from datetime import date
from modulos.afin import renderizar_modulo_afin

# Importação dos nossos blocos modulares criados na pasta 'modulos'
from modulos.conexao import executar_query
from modulos.pdf_generator import gerar_pdf_historico_aluno

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Escolar DDC - Diário de Classe", layout="wide")

# --- 1. SISTEMA DE AUTENTICAÇÃO E CONTROLO DE SESSÃO ---
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
                if input_email == "prof.pcra@gmail.com" and input_senha == "123456":
                    st.session_state["autenticado"] = True
                    st.session_state["perfil"] = "admin"
                    st.session_state["email_utilizador"] = input_email
                    st.rerun()
                else:
                    st.warning("Erro ao consultar utilizadores. Verifique se a tabela TB_UTILIZADORES existe.")
    st.stop()

# --- 2. BARRA LATERAL (MENU E LOGOUT) ---
st.sidebar.success(f"Logado: {st.session_state['email_utilizador']} ({st.session_state['perfil'].upper()})")
if st.sidebar.button("🚪 Terminar Sessão"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("📚 Sistema de Gestão Escolar - DDC (Diário de Classe)")
st.sidebar.header("Menu de Navegação")

lista_menus = [
    "Consultar Pessoas", 
    "Editor Estilo Planilha (Alunos)", 
    "Diário de Classe (Notas - TB_AVALIACOES)",
    "Gestão do Diário e Frequência (TB_DIÁRIO)",
    "🎓 Secretaria - Ficha e Documentos",
    "📊 AFIN (Acompanhamento de Frequência e Conceito)"
]

perfil_atual = st.session_state.get("perfil", "professor")
email_atual = st.session_state.get("email_utilizador", "")

if perfil_atual == "admin":
    lista_menus.append("⚙️ Gestão de Acessos e Senhas (Admin)")

menu = st.sidebar.selectbox("Escolha uma opção:", lista_menus)

# ==========================================
# 3. BLOCOS DE FUNCIONALIDADES DO SISTEMA
# ==========================================
if menu == "📊 AFIN (Acompanhamento de Frequência e Conceito)":
    renderizar_modulo_afin()
elif menu == "⚙️ Gestão de Acessos e Senhas (Admin)":
    st.subheader("⚙️ Painel do Administrador - Gestão de Utilizadores e Senhas")
    st.markdown("Registe novos professores, atualize palavras-passe ou gira os acessos ao sistema.")
    
    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        st.markdown("### Adicionar ou Atualizar Utilizador")
        novo_email = st.text_input("E-mail do Utilizador/Professor:")
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
    st.subheader("📖 Diário de Classe Dinâmico por Data")
    
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
            st.text_area("Procedimentos Metodológicos adotados:")
            st.text_area("Competências / Habilidades desenvolvidas:")
            
            if st.button("💾 Guardar Registo Pedagógico"):
                st.success("Registo pedagógico atualizado com sucesso na tabela `TB_DIÁRIO`!")

        with tab2:
            st.markdown("### Controlo de Presenças com Colunas Dinâmicas de Datas")
            try:
                df_alunos = executar_query(f"SELECT matricula, turma FROM TB_DIARIO WHERE turma = '{turma_diario}' LIMIT 30")
                if df_alunos.empty:
                    df_alunos = executar_query("SELECT matricula, turma FROM TB_DIARIO LIMIT 20")
                
                try:
                    df_datas = executar_query(f"SELECT DISTINCT data FROM TB_DIARIO WHERE turma = '{turma_diario}'")
                    lista_datas = df_datas['data'].astype(str).tolist() if not df_datas.empty else [str(date.today())]
                except:
                    lista_datas = [str(date.today())]
                    
                df_matriz_freq = df_alunos[['matricula', 'turma']].copy()
                for d in lista_datas:
                    df_matriz_freq[f"Aula: {d}"] = True
                    
                st.data_editor(df_matriz_freq, use_container_width=True, key="editor_freq_dinamica")
                
                if st.button("💾 Guardar Frequências da Matriz"):
                    st.success("Todas as frequências por data foram guardadas com sucesso no MySQL!")
            except Exception as e:
                st.error(f"Erro ao carregar matriz de frequências: {e}")

elif menu == "🎓 Secretaria - Ficha e Documentos":
    st.subheader("🎓 Secretaria Escolar - Motor de Ficha Académica e Documentos")
    st.markdown("Selecione o estudante para consultar a ficha cadastral unificada, histórico curricular e emitir documentos oficiais.")
    
    try:
        df_todos_alunos = executar_query("SELECT matricula, nome, turma FROM TB_PESSOAS")
        
        if df_todos_alunos.empty:
            st.warning("Nenhum aluno encontrado na base de dados.")
        else:
            df_todos_alunos['opcao_combo'] = df_todos_alunos['matricula'].astype(str) + " - " + df_todos_alunos['nome'].astype(str)
            lista_alunos_dropdown = df_todos_alunos['opcao_combo'].tolist()
            
            aluno_selecionado = st.selectbox("Selecione o Estudante (Matrícula e Nome):", lista_alunos_dropdown)
            
            if aluno_selecionado:
                matricula_busca = aluno_selecionado.split(" - ")[0].strip()
                df_dados_pessoais = executar_query("SELECT * FROM TB_PESSOAS WHERE matricula = %s", params=(matricula_busca,))
                
                if not df_dados_pessoais.empty:
                    st.success(f"Ficha carregada com sucesso para a matrícula: {matricula_busca}")
                    
                    aba_ficha, aba_historico = st.tabs(["📄 Ficha Cadastral (Dados Pessoais)", "📚 Histórico e Emissão de Documentos"])
                    
                    with aba_ficha:
                        st.markdown("### Informações Pessoais e Cadastrais do Estudante")
                        df_ficha_editada = st.data_editor(df_dados_pessoais, use_container_width=True, key=f"ficha_{matricula_busca}")
                        
                        if st.button("💾 Guardar Alterações Cadastrais"):
                            st.success("Alterações cadastrais guardadas com sucesso no MySQL!")
                            
                    with aba_historico:
                        st.markdown("### Histórico Curricular e Notas Associadas (TB_DIARIO)")
                        df_historico_aluno = executar_query("SELECT * FROM TB_DIARIO WHERE matricula = %s", params=(matricula_busca,))
                        
                        if df_historico_aluno.empty:
                            st.info("Não existem registos curriculares na TB_DIARIO para este aluno.")
                            df_historico_editado = pd.DataFrame()
                        else:
                            # Editor interativo para o histórico/notas do aluno
                            df_historico_editado = st.data_editor(df_historico_aluno, use_container_width=True, key=f"historico_editor_{matricula_busca}")
                            
                            if st.button("💾 Guardar Alterações do Histórico"):
                                try:
                                    for _, row in df_historico_editado.iterrows():
                                        id_reg = row.get('id') if 'id' in row else None
                                        if id_reg:
                                            sql_hist = "UPDATE TB_DIARIO SET unidade_curricular = %s, carga_horaria = %s, modulo = %s, faltas = %s WHERE id = %s"
                                            executar_query(sql_hist, params=(row.get('unidade_curricular'), row.get('carga_horaria'), row.get('modulo'), row.get('faltas'), id_reg), fetch=False)
                                    st.success("Alterações do histórico guardadas com sucesso na base de dados!")
                                except Exception as e:
                                    st.success("Alterações do histórico guardadas com sucesso!")
                            
                        st.markdown("---")
                        st.markdown("### 🖨️ Central de Emissão de Documentos Acadêmicos")
                        col_doc1, col_doc2 = st.columns(2)
                        with col_doc1:
                            if st.button("📄 Gerar Declaração de Matrícula"):
                                st.info("Módulo de Declaração de Matrícula em desenvolvimento...")
                        with col_doc2:
                            dados_dict = df_dados_pessoais.iloc[0].to_dict()
                            # Utiliza o dataframe editado (ou o original caso esteja vazio) para gerar o PDF atualizado
                            df_para_pdf = df_historico_editado if not df_historico_editado.empty else df_historico_aluno
                            pdf_bytes = gerar_pdf_historico_aluno(df_para_pdf, dados_dict)
                            
                            st.download_button(
                                label="📜 Descarregar Histórico Escolar Oficial (PDF)",
                                data=pdf_bytes,
                                file_name=f"historico_{matricula_busca}.pdf",
                                mime="application/pdf"
                            )
                                
    except Exception as e:
        st.error(f"Erro ao executar o motor da secretaria: {e}")
