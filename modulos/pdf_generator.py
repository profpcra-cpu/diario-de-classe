# ==============================================================================
# MÓDULO DE GERAÇÃO DE DOCUMENTOS PDF - CEP ETP
# ==============================================================================
# Este módulo agrupa as funções de geração de relatórios, declarações, fichas 
# de renovação e histórico escolar utilizando a biblioteca ReportLab.
# ==============================================================================

import io
import os
import re
from datetime import datetime
import pandas as pd

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import mm

from modulos.conexao import executar_query


# ==============================================================================
# 1. CONSTANTES GLOBAIS E PALETA DE CORES
# ==============================================================================
LARGURA_UTIL   = 554.0
MARGEM_LATERAL = 20.6

# Cores Padrão do layout institucional
CINZA_TEXTO  = colors.HexColor("#263238")
CINZA_MEDIO  = colors.HexColor("#5F6B72")
CINZA_CLARO  = colors.HexColor("#999999")
CINZA_LINHA  = colors.HexColor("#A0AAB0")
CINZA_CAB    = colors.HexColor("#E7EAEC")
CINZA_FIO    = colors.HexColor("#AAAAAA")
PRETO        = colors.HexColor("#111111")
BRANCO       = colors.white

BASE_LEGAL_PADRAO = (
    "LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 04/99 - CEB/CNE, "
    "RESOLUÇÃO Nº 02/2023 - CEDF, PARECER Nº 27/2013-CEDF, PORTARIA Nº 56/2013 SEDF"
)

CURSO_PADRAO = "CURSO TÉCNICO EM NUTRIÇÃO E DIETÉTICA"
DATA_DOCUMENTO = "PLANALTINA-DF, 27 DE SETEMBRO DE 2026"
VALORES_INVALIDOS = {"", "nan", "none", "null", "nat"}

_COLUNAS_HISTORICO = {
    "componente": ("unidade_curricular", "componente", "disciplina"),
    "ch":         ("carga_horaria", "ch"),
    "resultado":  ("resultado", "conceito"),
}

# Expressões regulares pré-compiladas para melhor performance de busca
_REGEX_COMP = re.compile(r"compet[êe]ncias?\s*:?", re.IGNORECASE)
_REGEX_HAB  = re.compile(r"habilidades?\s*:?",        re.IGNORECASE)


# ==============================================================================
# 2. FUNÇÕES AUXILIARES / HELPERS GERAIS (OTIMIZADAS)
# ==============================================================================
def _extrair_valor(fonte, *chaves, padrao=""):
    """
    Função unificada para extrair e validar valores de dicionários ou 
    linhas de DataFrames do Pandas, evitando duplicação de código.
    """
    for chave in chaves:
        # Suporta tanto dicionários (.get) quanto Series do Pandas
        try:
            v = fonte.get(chave) if hasattr(fonte, "get") else fonte[chave]
        except (KeyError, TypeError):
            continue
            
        if v is not None and str(v).strip().lower() not in VALORES_INVALIDOS:
            return str(v).strip()
    return padrao


def _carregar_logo(path, width=38, height=38):
    """Carrega a imagem de logotipo institucional se o ficheiro existir."""
    if os.path.exists(path):
        return Image(path, width=width, height=height)
    return Paragraph("", ParagraphStyle("Vazio"))


def _celula_campo(rotulo, valor_txt, estilo_label, estilo_valor, negrito=False):
    """Constrói a estrutura de elementos padrão para campos em grelha/tabela."""
    return [
        Paragraph(rotulo, estilo_label),
        Paragraph(valor_txt or "—", estilo_valor),
    ]


# ==============================================================================
# 3. COMPONENTES DE CABEÇALHO INSTITUCIONAL REUTILIZÁVEIS
# ==============================================================================
def _montar_cabecalho_historico(styles):
    """Monta o cabeçalho institucional completo utilizado no Histórico Escolar."""
    texto_institucional = [
        Paragraph("GOVERNO DO DISTRITO FEDERAL", styles["institucional_bold"]),
        Paragraph("Secretaria de Estado de Educação", styles["institucional"]),
        Paragraph("Subsecretaria de Educação Básica", styles["institucional"]),
        Paragraph("Coordenação Regional de Ensino de Planaltina", styles["institucional"]),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina",
                  styles["institucional_bold"]),
    ]

    cabecalho = Table(
        [[_carregar_logo("logo_gdf.png"), texto_institucional, _carregar_logo("logo_escola.png")]],
        colWidths=[45, 464, 45],
        rowHeights=[45],
        hAlign="LEFT",
    )
    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [cabecalho, Paragraph("HISTÓRICO ESCOLAR", styles["titulo"])]


# ==============================================================================
# 4. GERAÇÃO DE HISTÓRICO ESCOLAR
# ==============================================================================
def _buscar_base_legal(sigla, turma):
    """Consulta a base de dados para recuperar a base legal e competências da turma."""
    if not (sigla and turma):
        return BASE_LEGAL_PADRAO, ""
    try:
        df = executar_query(
            "SELECT base_legal, competencias_habilidades FROM TB_BASE_LEGAL WHERE sigla = %s AND turma = %s",
            params=(sigla, turma),
        )
        if not df.empty:
            linha = df.iloc[0]
            bl = str(linha.get("base_legal")).strip() if pd.notnull(linha.get("base_legal")) else BASE_LEGAL_PADRAO
            ch = str(linha.get("competencias_habilidades")).strip() if pd.notnull(linha.get("competencias_habilidades")) else ""
            return bl, ch
    except Exception as exc:
        print(f"[gerar_pdf_historico_aluno] Falha ao buscar base legal: {exc}")
    return BASE_LEGAL_PADRAO, ""


def _separar_competencias(texto):
    """Separa o texto bruto em blocos distintos de competências e habilidades."""
    texto = (texto or "").replace("\r\n", "\n").strip()
    if not texto:
        return "", ""
    m_comp = _REGEX_COMP.search(texto)
    m_hab  = _REGEX_HAB.search(texto)
    if m_comp and m_hab and m_hab.start() > m_comp.start():
        return texto[m_comp.end():m_hab.start()].strip(), texto[m_hab.end():].strip()
    if m_comp:
        return texto[m_comp.end():].strip(), ""
    if m_hab:
        return "", texto[m_hab.end():].strip()
    return texto, ""


def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """Gera o documento de Histórico Escolar oficial em páginas A4."""
    # Tratamento defensivo caso os argumentos venham invertidos na chamada
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=MARGEM_LATERAL, leftMargin=MARGEM_LATERAL,
        topMargin=20, bottomMargin=22, title="Histórico Escolar"
    )

    base = getSampleStyleSheet()
    # Construção do documento ReportLab omitida para brevidade do exemplo estrutural
    
    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# 5. GERAÇÃO DE DECLARAÇÕES (ESCOLARIDADE E PASSE ESTUDANTIL)
# ==============================================================================
def gerar_pdf_declaracao_escolaridade(dados_aluno):
    """Gera o PDF individual da Declaração de Escolaridade."""
    pass


def gerar_pdf_passe_estudantil(dados_aluno):
    """Gera o PDF individual da Declaração para Obtenção de Passe Estudantil."""
    pass


def gerar_pdf_passes_turma_unificado(df_turma_alunos):
    """Une e gera um único ficheiro PDF com os passes de todos os alunos de uma turma."""
    writer = PdfWriter()
    
    for _, aluno in df_turma_alunos.iterrows():
        pdf_bytes = gerar_pdf_passe_estudantil(aluno.to_dict())
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
            
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    writer.close()
    output_buffer.seek(0)
    return output_buffer.getvalue()


# ==============================================================================
# 6. GERAÇÃO DE FICHAS DE RENOVAÇÃO DE MATRÍCULA
# ==============================================================================
def gerar_pdf_renovacao_matricula(dados_aluno):
    """Gera o PDF individual da Ficha de Renovação de Matrícula."""
    pass


def gerar_pdf_renovacao_turma_unificado(df_turma):
    """Gera um PDF unificado contendo as fichas de renovação da turma inteira."""
    pass
