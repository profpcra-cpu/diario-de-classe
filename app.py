import streamlit as st

# Importações dos módulos da aplicação
from modulos.autenticacao import verificar_autenticacao, renderizar_barra_lateral_logout
from modulos.afin import renderizar_modulo_afin
from modulos.relatorio_turma import renderizar_modulo_relatorio_turma
from modulos.admin import renderizar_modulo_admin
from modulos.base_legal import renderizar_modulo_base_legal
from modulos.alunos import renderizar_consulta_pessoas, renderizar_editor_alunos
from modulos.diario import renderizar_modulo_notas, renderizar_modulo_diario_frequencia
from modulos.secretaria import renderizar_modulo_secretaria

# Configuração global da página
st.set_page_config(page_title="Sistema Escolar DDC - Diário de Classe", layout="wide")

# 1. Sistema de Autenticação
verificar_autenticacao()

# 2. Barra Lateral e Roteamento
renderizar_barra_lateral_logout()

st.title("📚 Sistema de Gestão Escolar - DDC (Diário de Classe)")
st.sidebar.header("Menu de Navegação")

lista_menus = [
    "Consultar Pessoas", 
    "Editor Estilo Planilha (Alunos)", 
    "Diário de Classe (Notas - TB_AVALIACOES)",
    "Gestão do Diário e Frequência (TB_DIÁRIO)",
    "🎓 Secretaria - Ficha e Documentos",
    "⚖️ Gestão de Base Legal",
    "📊 AFIN (Acompanhamento de Frequência e Conceito)",
    "📊 Relatório da Turma"
]

perfil_atual = st.session_state.get("perfil", "professor")
if perfil_atual == "admin":
    lista_menus.append("⚙️ Gestão de Acessos e Senhas (Admin)")

menu = st.sidebar.selectbox("Escolha uma opção:", lista_menus)

# 3. Roteamento Simplificado
if menu == "📊 AFIN (Acompanhamento de Frequência e Conceito)":
    renderizar_modulo_afin()

elif menu == "📊 Relatório da Turma":
    renderizar_modulo_relatorio_turma()

elif menu == "⚙️ Gestão de Acessos e Senhas (Admin)":
    renderizar_modulo_admin()

elif menu == "⚖️ Gestão de Base Legal":
    renderizar_modulo_base_legal()

elif menu == "Consultar Pessoas":
    renderizar_consulta_pessoas()

elif menu == "Editor Estilo Planilha (Alunos)":
    renderizar_editor_alunos()

elif menu == "Diário de Classe (Notas - TB_AVALIACOES)":
    renderizar_modulo_notas()

elif menu == "Gestão do Diário e Frequência (TB_DIÁRIO)":
    renderizar_modulo_diario_frequencia()

elif menu == "🎓 Secretaria - Ficha e Documentos":
    renderizar_modulo_secretaria()
