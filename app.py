import streamlit as st
import os

# 1. Configuração da página e layout
st.set_page_config(
    page_title="DDC - Diário de Classe Eletrónico",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilização CSS Customizada (Modern Clean UI)
st.markdown("""
    <style>
    /* Estilo do container principal */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Estilo dos Cards do Dashboard */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #1E88E5;
        margin-bottom: 15px;
    }
    
    .metric-card h4 {
        margin: 0;
        color: #555555;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card h2 {
        margin: 5px 0 0 0;
        color: #1E88E5;
        font-size: 1.8rem;
    }
    
    /* Personalização da Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Botão de Terminar Sessão */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Importação dos Módulos Funcionais
from modulos.autenticacao import renderizar_login, verificar_sessao
from modulos.alunos import renderizar_consulta_pessoas, renderizar_editor_alunos
from modulos.diario import renderizar_modulo_notas, renderizar_modulo_diario_frequencia
from modulos.secretaria import renderizar_modulo_secretaria
from modulos.base_legal import renderizar_modulo_base_legal
from modulos.afin import renderizar_modulo_afin
from modulos.relatorio_turma import renderizar_modulo_relatorio_turma
from modulos.admin import renderizar_modulo_admin

# 4. Fluxo de Autenticação
if not verificar_sessao():
    renderizar_login()
    st.stop()

# --- SIDEBAR (BARRA LATERAL REORGANIZADA) ---
with st.sidebar:
    # Exibição dos Logotipos Institucionais
    col_logo1, col_logo2 = st.columns(2)
    with col_logo1:
        if os.path.exists("logo_escola.png"):
            st.image("logo_escola.png", use_container_width=True)
    with col_logo2:
        if os.path.exists("logo_gdf.png"):
            st.image("logo_gdf.png", use_container_width=True)
            
    st.markdown("---")
    
    # Perfil do Utilizador
    email_user = st.session_state.get("email_utilizador", "utilizador@escola.df.gov.br")
    perfil_user = st.session_state.get("perfil", "professor").upper()
    
    st.markdown(f"👤 **{email_user}**")
    st.caption(f"Nível de Acesso: `{perfil_user}`")
    
    if st.button("🚪 Encerrar Sessão", key="btn_logout"):
        st.session_state.clear()
        st.rerun()
        
    st.markdown("---")
    st.subheader("📌 Navegação Principal")
    
    # Menu reorganizado por Categorias Claras
    opcoes_menu = [
        "🏠 Painel Inicial",
        "👥 Alunos e Pessoas",
        "📖 Diário e Frequência",
        "📊 Matriz de Notas",
        "📄 Secretaria e Fichas",
        "⚖️ Base Legal",
        "📈 Acompanhamento AFIN",
        "🖨️ Relatório da Turma"
    ]
    
    # Se for Admin, adiciona o painel de gestão
    if perfil_user == "ADMIN":
        opcoes_menu.append("⚙️ Gestão de Acessos")
        
    menu_selecionado = st.radio("Selecione o Módulo:", opcoes_menu)

# --- ÁREA DE CONTEÚDO PRINCIPAL ---

# CABEÇALHO SUPERIOR DA PÁGINA
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("Sistema de Gestão Escolar — DDC")
    st.caption("Centro de Educação Profissional / Escola Técnica")
with col_head2:
    if os.path.exists("logo_escola.png"):
        st.image("logo_escola.png", width=90)

st.divider()

# ROTEAMENTO DOS MÓDULOS

if menu_selecionado == "🏠 Painel Inicial":
    st.subheader("👋 Bem-vindo ao Diário de Classe Eletrónico")
    st.markdown("Selecione um módulo no menu lateral para iniciar as suas atividades ou consulte os destaques rápidos abaixo:")
    
    # CARDS DE VISÃO GERAL (DASHBOARD MODERNIZADO)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="metric-card">
            <h4>Alunos Ativos</h4>
            <h2>837</h2>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card">
            <h4>Turmas Abertas</h4>
            <h2>24</h2>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
            <h4>Frequência Média</h4>
            <h2>91.8%</h2>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="metric-card">
            <h4>Aulas Registadas</h4>
            <h2>1,420</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Acesso Rápido / Destaques
    col_dash1, col_dash2 = st.columns(2)
    with col_dash1:
        st.info("💡 **Dica de Utilização:** Registe diariamente a frequência e o conteúdo programático na aba **Diário e Frequência** para manter os relatórios pedagógicos atualizados.")
    with col_dash2:
        st.warning("⚠️ **Aviso de Prazos:** O encerramento do lançamento de notas da AV2 referente ao quadrimestre em curso expira em breve.")

elif menu_selecionado == "👥 Alunos e Pessoas":
    tab_cons, tab_edit = st.tabs(["🔍 Consulta Geral de Alunos", "✏️ Edição de Registos"])
    with tab_cons:
        renderizar_consulta_pessoas()
    with tab_edit:
        renderizar_editor_alunos()

elif menu_selecionado == "📖 Diário e Frequência":
    renderizar_modulo_diario_frequencia()

elif menu_selecionado == "📊 Matriz de Notas":
    renderizar_modulo_notas()

elif menu_selecionado == "📄 Secretaria e Fichas":
    renderizar_modulo_secretaria()

elif menu_selecionado == "⚖️ Base Legal":
    renderizar_modulo_base_legal()

elif menu_selecionado == "📈 Acompanhamento AFIN":
    renderizar_modulo_afin()

elif menu_selecionado == "🖨️ Relatório da Turma":
    renderizar_modulo_relatorio_turma()

elif menu_selecionado == "⚙️ Gestão de Acessos":
    renderizar_modulo_admin()
