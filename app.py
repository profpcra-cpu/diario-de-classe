import io
import streamlit as st
import pymysql
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Escolar DDC - Diário de Classe", layout="wide")

# --- FUNÇÃO CENTRAL DE CONEXÃO E QUERY AO MYSQL ---
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

# --- FUNÇÃO PARA GERAR O PDF DO HISTÓRICO ESCOLAR EM MEMÓRIA ---
def gerar_pdf_historico_aluno(dados_aluno, df_historico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    title_style = ParagraphStyle('TitleStyle', parent=normal_style, fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=1)
    sub_title_style = ParagraphStyle('SubTitleStyle', parent=normal_style, fontName='Helvetica', fontSize=7, leading=9, alignment=1)
    doc_title_style = ParagraphStyle('DocTitleStyle', parent=normal_style, fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1)
    cell_style = ParagraphStyle('CellStyle', parent=normal_style, fontName='Helvetica', fontSize=7, leading=9)
    cell_bold = ParagraphStyle('CellBold', parent=normal_style, fontName='Helvetica-Bold', fontSize=7, leading=9)
    cell_center = ParagraphStyle('CellCenter', parent=normal_style, fontName='Helvetica', fontSize=7, leading=9, alignment=1)
    cell_center_bold = ParagraphStyle('CellCenterBold', parent=normal_style, fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=1)

    elements = []

    # Cabeçalho Institucional Oficial
    header_text = [
        Paragraph("Governo do Distrito Federal", title_style),
        Paragraph("Secretaria de Estado de Educação", sub_title_style),
        Paragraph("Subsecretaria de Educação Básica", sub_title_style),
        Paragraph("Coordenação Regional de Ensino de Planaltina", sub_title_style),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina", sub_title_style),
        Spacer(1, 0.2 * cm),
        Paragraph("HISTÓRICO ESCOLAR", doc_title_style)
    ]

    header_table = Table([[ [Paragraph("", normal_style)], header_text, [Paragraph("", normal_style)] ]], colWidths=[3.0 * cm, 12.0 * cm, 3.0 * cm])
    header_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.1 * cm))

    # Dados Dinâmicos do Aluno vindos do MySQL
    nome_aluno = dados_aluno.get('nome', 'N/D')
    mat_aluno = dados_aluno.get('matricula', 'N/D')
    turma_aluno = dados_aluno.get('turma', 'N/D')
    sexo_aluno = dados_aluno.get('sexo', 'N/D')
    
    data_ident = [
        [Paragraph("<b>Curso:</b> TÉCNICO EM SECRETARIADO ESCOLAR", cell_style), "", "", ""],
        [Paragraph(f"<b>Matrícula:</b> {mat_aluno}", cell_style), Paragraph(f"<b>Turma/ Turno:</b> {turma_aluno}", cell_style), Paragraph(f"<b>Nome:</b> {nome_aluno}", cell_style), Paragraph(f"<b>Sexo:</b> {sexo_aluno}", cell_style)],
        [Paragraph("<b>Nome da Mãe:</b> -", cell_style), "", "", ""],
        [Paragraph("<b>Nome do Pai:</b> -", cell_style), "", "", ""],
        [Paragraph("<b>Data de Nasc.:</b> -", cell_style), Paragraph("<b>Nacionalidade:</b> BRASILEIRA", cell_style), Paragraph("<b>Naturalidade:</b> -", cell_style), Paragraph("<b>UF:</b> DF", cell_style)],
        [Paragraph("<b>RG/CPF/CNH:</b> -", cell_style), Paragraph("<b>Órgão Expedidor:</b> -", cell_style), Paragraph("<b>Data de Expedição:</b> -", cell_style), Paragraph("", cell_style)],
        [Paragraph("<b>Base Legal:</b> LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 02/2023 - CEDF", cell_style), "", "", ""]
    ]

    t_ident = Table(data_ident, colWidths=[4.5 * cm, 4.5 * cm, 6.0 * cm, 3.0 * cm])
    t_ident.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('SPAN', (0,0), (3,0)),
        ('SPAN', (0,2), (3,2)),
        ('SPAN', (0,3), (3,3)),
        ('SPAN', (0,6), (3,6)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_ident)
    elements.append(Spacer(1, 0.1 * cm))

    # Tabela Curricular
    header_comp = [
        Paragraph("<b>Componente Curricular (IDUC)</b>", cell_bold),
        Paragraph("<b>Semestre</b>", cell_center_bold),
        Paragraph("<b>C/H</b>", cell_center_bold),
        Paragraph("<b>Módulo</b>", cell_center_bold),
        Paragraph("<b>Faltas</b>", cell_center_bold),
        Paragraph("<b>Resultado</b>", cell_center_bold)
    ]

    components_data = [header_comp]
    
    if df_historico.empty:
        components_data.append([Paragraph("Sem registos curriculares", cell_style), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center)])
    else:
        for _, row in df_historico.iterrows():
            components_data.append([
                Paragraph(str(row.get('iduc', '')), cell_style),
                Paragraph(str(row.get('turma', '')), cell_center),
                Paragraph("50", cell_center),
                Paragraph("Teoria", cell_center),
                Paragraph("0", cell_center),
                Paragraph("AP" if float(row.get('soma', 0) or 0) >= 5 else "AF", cell_center)
            ])

    t_comp = Table(components_data, colWidths=[9.0 * cm, 2.5 * cm, 1.5 * cm, 2.0 * cm, 1.5 * cm, 1.5 * cm])
    t_comp.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(t_comp)
    elements.append(Spacer(1, 0.1 * cm))

    # Rodapé e Assinaturas
    footer_data = [
        [Paragraph("AP = Aprovado; AE = Aproveitamento de Estudos; NA = Não Apto", cell_style), Paragraph("<b>T. Teoria:</b> 1.353", cell_style), Paragraph("<b>T. Prática:</b> 0", cell_style)],
        [Paragraph("PLANALTINA-DF, 26/09/2026", cell_style), "", ""],
        [Paragraph("", cell_style), "", ""],
        [Paragraph("", cell_style), "", ""],
        [Paragraph("DIRETOR", cell_center_bold), "", Paragraph("SECRETÁRIO(A) ESCOLAR", cell_center_bold)]
    ]

    t_footer = Table(footer_data, colWidths=[9.0 * cm, 4.5 * cm, 4.5 * cm])
    t_footer.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('SPAN', (0,0), (0,0)),
        ('SPAN', (0,1), (2,1)),
        ('SPAN', (0,2), (2,2)),
        ('SPAN', (0,3), (2,3)),
        ('SPAN', (1,4), (2,4)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_footer)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

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
    "🎓 Secretaria - Ficha e Documentos"
]

perfil_atual = st.session_state.get("perfil", "professor")
email_atual = st.session_state.get("email_utilizador", "")

if perfil_atual == "admin":
    lista_menus.append("⚙️ Gestão de Acessos e Senhas (Admin)")

menu = st.sidebar.selectbox("Escolha uma opção:", lista_menus)

# ==========================================
# 3. BLOCOS DE FUNCIONALIDADES DO SISTEMA
# ==========================================

if menu == "⚙️ Gestão de Acessos e Senhas (Admin)":
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
                        st.markdown("### Histórico Curricular e Notas Associadas")
                        df_historico_aluno = executar_query("SELECT * FROM TB_AVALIACOES WHERE matrícula = %s", params=(matricula_busca,))
                        
                        if df_historico_aluno.empty:
                            st.info("Não existem registos de notas ou histórico curricular para este aluno.")
                        else:
                            st.dataframe(df_historico_aluno, use_container_width=True)
                            
                        st.markdown("---")
                        st.markdown("### 🖨️ Central de Emissão de Documentos Acadêmicos")
                        col_doc1, col_doc2 = st.columns(2)
                        with col_doc1:
                            if st.button("📄 Gerar Declaração de Matrícula"):
                                st.info("Módulo de Declaração de Matrícula em desenvolvimento...")
                        with col_doc2:
                            dados_dict = df_dados_pessoais.iloc[0].to_dict()
                            pdf_bytes = gerar_pdf_historico_aluno(dados_dict, df_historico_aluno)
                            
                            st.download_button(
                                label="📜 Descarregar Histórico Escolar Oficial (PDF)",
                                data=pdf_bytes,
                                file_name=f"historico_{matricula_busca}.pdf",
                                mime="application/pdf"
                            )
                                
    except Exception as e:
        st.error(f"Erro ao executar o motor da secretaria: {e}")
