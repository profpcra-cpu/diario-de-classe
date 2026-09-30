from datetime import datetime
import io
import os
import re
import pandas as pd

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from modulos.conexao import executar_query


# ============================================================
# 1. HISTÓRICO ESCOLAR
# ============================================================
# -*- coding: utf-8 -*-
"""
Gerador do Histórico Escolar Oficial — CEP ETP.

Layout (A4 retrato, 2 páginas):
  Página 1 — Identificação, Dados, Base Legal, Componentes Curriculares, Totais e Assinaturas
  Página 2 — Cabeçalho Institucional, Identificação do Estudante, Competências e Habilidades, Termo e Assinaturas
"""

import io
import os
from datetime import datetime

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from modulos.conexao import executar_query


# ======================================================================
# CONSTANTES
# ======================================================================
LARGURA_UTIL = 554.0
MARGEM_LAT   = 20.6

CINZA_TEXTO = colors.HexColor("#263238")
CINZA_MEDIO = colors.HexColor("#5F6B72")
CINZA_LINHA = colors.HexColor("#C8CED2")
CINZA_CAB   = colors.HexColor("#E7EAEC")
CINZA_ZEBRA = colors.HexColor("#FAFAFA")
PRETO       = colors.HexColor("#111111")

BASE_LEGAL_PADRAO = (
    "LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 02/2023 - CEDF"
)

# Termos indesejados que devem ser tratados como campos em branco
VALORES_INVALIDOS = {"", "nan", "none", "null", "não sei", "nao sei", "não informado", "nao informado"}

_COLUNAS_HISTORICO = {
    "componente": ("unidade_curricular", "componente", "disciplina"),
    "ch":         ("carga_horaria", "ch"),
    "resultado":  ("resultado", "conceito"),
}


# ======================================================================
# ESTILOS
# ======================================================================
def _build_styles():
    base = getSampleStyleSheet()

    def _p(name, parent, **kw):
        return ParagraphStyle(name, parent=parent, **kw)

    normal = base["Normal"]

    inst = _p("HistInst", normal,
              fontName="Helvetica", fontSize=7.3, leading=8.4,
              alignment=TA_CENTER, textColor=PRETO)

    return {
        "institucional": inst,
        "institucional_bold": _p("HistInstBold", inst,
                                 fontName="Helvetica-Bold", fontSize=7.5, leading=8.7),
        "titulo": _p("HistTitulo", base["Heading1"],
                     fontName="Helvetica-Bold", fontSize=14, leading=16,
                     alignment=TA_CENTER, textColor=PRETO,
                     spaceBefore=3, spaceAfter=4),
        "secao": _p("HistSecao", normal,
                    fontName="Helvetica-Bold", fontSize=7.4, leading=8.5,
                    alignment=TA_LEFT, textColor=PRETO),
        "label": _p("HistLabel", normal,
                    fontName="Helvetica-Bold", fontSize=6.2, leading=7,
                    textColor=CINZA_MEDIO),
        "valor": _p("HistValor", normal,
                    fontName="Helvetica", fontSize=7.4, leading=8.5,
                    textColor=CINZA_TEXTO),
        "valor_bold": _p("HistValorBold", normal,
                         fontName="Helvetica-Bold", fontSize=7.4, leading=8.5,
                         textColor=PRETO),
        "th": _p("HistTH", normal,
                 fontName="Helvetica-Bold", fontSize=6.8, leading=7.6,
                 alignment=TA_CENTER, textColor=PRETO),
        "td": _p("HistTD", normal,
                 fontName="Helvetica", fontSize=6.8, leading=7.5,
                 alignment=TA_CENTER, textColor=CINZA_TEXTO),
        "td_left": _p("HistTDLeft", normal,
                      fontName="Helvetica", fontSize=6.8, leading=7.5,
                      alignment=TA_LEFT, textColor=CINZA_TEXTO),
        "rodape": _p("HistRodape", normal,
                     fontName="Helvetica", fontSize=6.5, leading=7.7,
                     textColor=CINZA_MEDIO),
        "assinatura": _p("HistAssinatura", normal,
                         fontName="Helvetica", fontSize=7, leading=8,
                         alignment=TA_CENTER, textColor=PRETO),
        "comp_texto": _p("HistCompTexto", normal,
                         fontName="Helvetica", fontSize=6.9, leading=8.6,
                         alignment=TA_LEFT, textColor=CINZA_TEXTO),
        "totais": _p("HistTotais", normal,
                     fontName="Helvetica-Bold", fontSize=7, leading=8,
                     alignment=TA_CENTER, textColor=PRETO),
    }


STYLES = _build_styles()


# ======================================================================
# HELPERS
# ======================================================================
def _valor(d, *chaves, padrao=""):
    for chave in chaves:
        v = d.get(chave)
        if v is not None:
            texto = str(v).strip()
            if texto.lower() not in VALORES_INVALIDOS:
                return texto
    return padrao


def _row_get(row, chaves, padrao=""):
    for chave in chaves:
        v = row.get(chave)
        if v is not None:
            texto = str(v).strip()
            if texto.lower() not in VALORES_INVALIDOS:
                return v
    return padrao


def _carregar_logo(path, width=42, height=42):
    if os.path.exists(path):
        return Image(path, width=width, height=height)
    return Paragraph("", STYLES["valor"])


def _buscar_base_legal(sigla, turma):
    if not (sigla or turma):
        return BASE_LEGAL_PADRAO, ""

    try:
        df = executar_query(
            """SELECT base_legal, competencias_habilidades
               FROM TB_BASE_LEGAL
               WHERE sigla = %s OR turma = %s""",
            params=(sigla, turma),
        )
        if not df.empty:
            linha = df.iloc[0]
            bl = linha.get("base_legal")
            cp = linha.get("competencias_habilidades")
            bl = str(bl).strip() if pd.notnull(bl) and str(bl).strip() else BASE_LEGAL_PADRAO
            cp = str(cp).strip() if pd.notnull(cp) else ""
            return bl, cp
    except Exception as exc:
        print(f"[historico] Falha ao buscar base legal: {exc}")

    return BASE_LEGAL_PADRAO, ""


def _montar_cabecalho():
    textos = [
        Paragraph("GOVERNO DO DISTRITO FEDERAL", STYLES["institucional_bold"]),
        Paragraph("Secretaria de Estado de Educação", STYLES["institucional"]),
        Paragraph("Subsecretaria de Educação Básica", STYLES["institucional"]),
        Paragraph("Coordenação Regional de Ensino de Planaltina", STYLES["institucional"]),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina",
                  STYLES["institucional_bold"]),
    ]

    cabecalho = Table(
        [[_carregar_logo("logo_gdf.png"),
          textos,
          _carregar_logo("logo_escola.png")]],
        colWidths=[52, 450, 52],
        rowHeights=[48],
        hAlign="LEFT",
    )
    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return cabecalho


def _bloco_secao(titulo):
    t = Table([[Paragraph(titulo, STYLES["secao"])]],
              colWidths=[LARGURA_UTIL], rowHeights=[15], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_CAB),
        ("LINEBELOW",  (0, 0), (-1, -1), 0.5, CINZA_LINHA),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    return t


def _tabela_campos(linhas, larguras):
    t = Table(linhas, colWidths=larguras, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    return t


def _gerar_bloco_identificacao(curso, matricula, turma, nome, cpf, sexo, mae, pai, dt_nasc, nacionalidade, naturalidade, uf, rg, orgao, dt_exp):
    """Gera o bloco estruturado de identificação acadêmica e dados do estudante."""
    elementos = []
    
    # --- Identificação Acadêmica ---
    elementos.append(_bloco_secao("IDENTIFICAÇÃO ACADÊMICA"))
    elementos.append(_tabela_campos(
        [
            [Paragraph("CURSO", STYLES["label"]),
             Paragraph("MATRÍCULA", STYLES["label"]),
             Paragraph("TURMA / TURNO", STYLES["label"])],
            [Paragraph(curso or "—", STYLES["valor_bold"]),
             Paragraph(matricula or "—", STYLES["valor"]),
             Paragraph(turma or "—", STYLES["valor"])],
        ],
        [330, 110, 114],
    ))
    elementos.append(Spacer(1, 3))

    # --- Dados do Estudante ---
    elementos.append(_bloco_secao("DADOS DO ESTUDANTE"))
    elementos.append(_tabela_campos(
        [
            [Paragraph("NOME", STYLES["label"]),
             Paragraph("CPF", STYLES["label"]),
             Paragraph("SEXO", STYLES["label"])],
            [Paragraph(nome or "—", STYLES["valor_bold"]),
             Paragraph(cpf or "—", STYLES["valor"]),
             Paragraph(sexo or "—", STYLES["valor"])],

            [Paragraph("NOME DA MÃE", STYLES["label"]),
             Paragraph("NOME DO PAI", STYLES["label"]),
             Paragraph("DATA DE NASCIMENTO", STYLES["label"])],
            [Paragraph(mae or "—", STYLES["valor"]),
             Paragraph(pai or "—", STYLES["valor"]),
             Paragraph(dt_nasc or "—", STYLES["valor"])],

            [Paragraph("NACIONALIDADE", STYLES["label"]),
             Paragraph("NATURALIDADE / UF", STYLES["label"]),
             Paragraph("RG / ÓRGÃO / EXPEDIÇÃO", STYLES["label"])],
            [Paragraph(nacionalidade or "—", STYLES["valor"]),
             Paragraph(f"{naturalidade} / {uf}".strip(" /") or "—", STYLES["valor"]),
             Paragraph(" ".join(x for x in (rg, orgao, dt_exp) if x) or "—",
                       STYLES["valor"])],
        ],
        [300, 120, 134],
    ))
    return elementos


# ======================================================================
# FUNÇÃO PRINCIPAL
# ======================================================================
def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """Gera o Histórico Escolar Oficial (2 páginas com dados repetidos)."""

    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGEM_LAT,
        leftMargin=MARGEM_LAT,
        topMargin=18,
        bottomMargin=20,
        title="Histórico Escolar Oficial",
        author="Centro de Educação Profissional Escola Técnica de Planaltina",
    )

    if isinstance(dados_aluno, dict):
        d = dados_aluno
    elif hasattr(dados_aluno, "iloc") and not dados_aluno.empty:
        d = dados_aluno.iloc[0].to_dict()
    else:
        d = {}

    curso         = _valor(d, "curso", padrao="TÉCNICO EM ENFERMAGEM").upper()
    matricula     = _valor(d, "matricula", "matrícula")
    turma         = _valor(d, "turma")
    sigla         = _valor(d, "sigla")
    nome          = _valor(d, "nome", "nome_aluno").upper()
    cpf           = _valor(d, "cpf")
    sexo          = _valor(d, "sexo").upper()
    mae           = _valor(d, "mae", "nome_mae", "nome_da_mae").upper()
    pai           = _valor(d, "pai", "nome_pai", "nome_do_pai").upper()
    dt_nasc       = _valor(d, "data_nascimento", "dt_nascimento", "nascimento", "data_nasc")
    nacionalidade = _valor(d, "nacionalidade", "nacionalidade_aluno", padrao="BRASILEIRA").upper()
    naturalidade  = _valor(d, "naturalidade", "naturalidade_aluno").upper()
    uf            = _valor(d, "uf", "uf_naturalidade", "uf_nascimento", padrao="DF").upper()
    rg            = _valor(d, "rg", "registro_geral", "num_rg")
    orgao         = _valor(d, "orgao_expeditor", "orgao", "orgao_exp").upper()
    dt_exp        = _valor(d, "data_expedicao", "dt_expedicao", "data_exp")

    base_legal_texto, competencias_texto = _buscar_base_legal(sigla, turma)

    story = []

    # ============ PÁGINA 1 ============
    story.append(_montar_cabecalho())
    story.append(Paragraph("HISTÓRICO ESCOLAR", STYLES["titulo"]))

    # Insere dados de identificação na página 1
    story.extend(_gerar_bloco_identificacao(
        curso, matricula, turma, nome, cpf, sexo, mae, pai, dt_nasc,
        nacionalidade, naturalidade, uf, rg, orgao, dt_exp
    ))
    story.append(Spacer(1, 3))

    # --- Base Legal ---
    t_base = Table(
        [[Paragraph("BASE LEGAL", STYLES["label"])],
         [Paragraph(base_legal_texto, STYLES["valor"])]],
        colWidths=[LARGURA_UTIL], hAlign="LEFT",
    )
    t_base.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CAB),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    story.append(t_base)
    story.append(Spacer(1, 4))

    # --- Componentes Curriculares ---
    header = [
        Paragraph("COMPONENTE CURRICULAR", STYLES["th"]),
        Paragraph("SEM.",  STYLES["th"]),
        Paragraph("CH",    STYLES["th"]),
        Paragraph("MÓDULO", STYLES["th"]),
        Paragraph("FALTAS", STYLES["th"]),
        Paragraph("RESULTADO", STYLES["th"]),
    ]
    linhas_hist = [header]
    total_teoria = total_pratica = 0

    if df_historico is not None and not df_historico.empty:
        for _, row in df_historico.iterrows():
            comp = str(_row_get(row, _COLUNAS_HISTORICO["componente"], "---"))
            sem  = str(row.get("semestre", "")).strip()

            ch_val = row.get("carga_horaria", row.get("ch", 0))
            try:
                ch_num = int(ch_val) if pd.notnull(ch_val) and str(ch_val).isdigit() else 0
            except Exception:
                ch_num = 0

            mod = str(row.get("modulo", "Teoria"))
            if "prática" in mod.lower():
                total_pratica += ch_num
            else:
                total_teoria += ch_num

            if not sem or sem.lower() in VALORES_INVALIDOS:
                sem = ch = mod = faltas = res = ""
            else:
                ch     = str(ch_val)
                faltas = str(row.get("faltas", "0"))
                res    = str(_row_get(row, _COLUNAS_HISTORICO["resultado"], ""))

            linhas_hist.append([
                Paragraph(comp, STYLES["td_left"]),
                Paragraph(sem, STYLES["td"]),
                Paragraph(ch, STYLES["td"]),
                Paragraph(mod, STYLES["td"]),
                Paragraph(faltas, STYLES["td"]),
                Paragraph(res, STYLES["td"]),
            ])

    t_hist = Table(linhas_hist, repeatRows=1,
                   colWidths=[314, 40, 30, 65, 45, 60], hAlign="LEFT")
    estilo_hist = [
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CAB),
        ("LINEBELOW",  (0, 0), (-1, 0), 0.7, CINZA_LINHA),
        ("GRID",       (0, 0), (-1, -1), 0.3, CINZA_LINHA),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]
    estilo_hist.extend(
        ("BACKGROUND", (0, i), (-1, i), CINZA_ZEBRA)
        for i in range(2, len(linhas_hist), 2)
    )
    t_hist.setStyle(TableStyle(estilo_hist))
    story.append(t_hist)
    story.append(Spacer(1, 3))

    # --- Totais ---
    t_totais = Table([[
        Paragraph(f"T. Teoria: {total_teoria}", STYLES["totais"]),
        Paragraph(f"T. Prática: {total_pratica}", STYLES["totais"]),
    ]], colWidths=[277, 277], hAlign="LEFT")
    t_totais.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, PRETO),
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_CAB),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_totais)
    story.append(Spacer(1, 6))

    # --- Data + Assinaturas (Página 1) ---
    data_doc = f"PLANALTINA-DF, {datetime.now().strftime('%d/%m/%Y')}"
    t_data = Table([[Paragraph(data_doc, STYLES["assinatura"])]],
                   colWidths=[LARGURA_UTIL], hAlign="LEFT")
    t_data.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT")]))

    assinatura_p1 = Table([[
        Paragraph("____________________________________________<br/><b>DIRETOR(A)</b>",
                  STYLES["assinatura"]),
        Paragraph("____________________________________________<br/><b>SECRETÁRIO(A) ESCOLAR</b>",
                  STYLES["assinatura"]),
    ]], colWidths=[277, 277], rowHeights=[35], hAlign="LEFT")
    assinatura_p1.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
    ]))

    story.append(KeepTogether([t_data, Spacer(1, 8), assinatura_p1]))

    # ============ PÁGINA 2 ============
    story.append(PageBreak())
    story.append(_montar_cabecalho())
    story.append(Spacer(1, 4))

    # Repete a identificação acadêmica e dados do estudante na página 2
    story.extend(_gerar_bloco_identificacao(
        curso, matricula, turma, nome, cpf, sexo, mae, pai, dt_nasc,
        nacionalidade, naturalidade, uf, rg, orgao, dt_exp
    ))
    story.append(Spacer(1, 6))

    # --- Competências e Habilidades ---
    story.append(_bloco_secao("COMPETÊNCIAS E HABILIDADES"))

    if competencias_texto:
        comp_html = competencias_texto.replace("\n", "<br/>")
    else:
        comp_html = "Nenhuma competência cadastrada para esta turma/sigla."

    t_comp = Table([[Paragraph(comp_html, STYLES["comp_texto"])]],
                   colWidths=[LARGURA_UTIL], hAlign="LEFT")
    t_comp.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.6, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    # --- Termo de autenticidade ---
    t_autent = Table([[Paragraph(
        "<b>Centro de Educação Profissional - Escola Técnica de Planaltina</b><br/>"
        "Conferido o presente documento, declaramos sua autenticidade e regularidade, "
        "de acordo com os registros escolares e com a legislação vigente.",
        STYLES["rodape"])]], colWidths=[LARGURA_UTIL], hAlign="LEFT")
    t_autent.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, PRETO),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    t_data_p2 = Table([[Paragraph(data_doc, STYLES["assinatura"])]],
                      colWidths=[LARGURA_UTIL], hAlign="LEFT")
    t_data_p2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT")]))

    story.append(KeepTogether([
        t_autent,
        Spacer(1, 6),
        t_data_p2,
        Spacer(1, 15),
        assinatura_p1,
    ]))

    # ------------------------------------------------------------------
    # Rodapé de página (canvas)
    # ------------------------------------------------------------------
    def _rodape(canvas, doc_):
        canvas.saveState()
        largura, _ = A4
        canvas.setStrokeColor(CINZA_LINHA)
        canvas.setLineWidth(0.4)
        canvas.line(doc_.leftMargin, 16, largura - doc_.rightMargin, 16)
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(CINZA_MEDIO)
        canvas.drawString(doc_.leftMargin, 8,
                          "Centro de Educação Profissional Escola Técnica de Planaltina")
        canvas.drawRightString(largura - doc_.rightMargin, 8, f"Página {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_rodape, onLaterPages=_rodape)

    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# 2. MATRIZ AFIN
# ============================================================

COLUNAS_MATRIZ_POR_PAGINA = 21
MARGEM_ESQ = 10 * mm
MARGEM_DIR = 10 * mm
MARGEM_SUP = 8 * mm
MARGEM_INF = 9 * mm
LARGURA_MATRICULA = 24 * mm
LARGURA_ESTUDANTE = 49 * mm

AZUL_INSTITUCIONAL = colors.HexColor("#173B63")
AZUL_SECUNDARIO = colors.HexColor("#315D82")
AZUL_MUITO_CLARO = colors.HexColor("#F2F6FA")
CINZA_TEXTO_AFIN = colors.HexColor("#28343F")
CINZA_SECUNDARIO = colors.HexColor("#68737D")
CINZA_ZEBRA = colors.HexColor("#FAFBFC")

def _texto(valor):
    if valor is None: return ""
    try:
        if pd.isna(valor): return ""
    except Exception: pass
    texto = str(valor).strip()
    return "" if texto.lower() in {"nan", "nat", "none"} else texto

def _html(valor):
    return _texto(valor).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _normalizar(valor):
    return re.sub(r"\s+", " ", _texto(valor).upper()).strip()

def _tipo_coluna(nome):
    s = _normalizar(nome)
    if re.search(r"(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])", s): return "FAL"
    if re.search(r"(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])", s): return "CON"
    return None

def _nome_uc(nome):
    return re.sub(r"\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$", "", _texto(nome), flags=re.I).strip()

def _mapa_iduc(mapa):
    if not mapa: return {}
    resultado = {}
    for iduc, nome in mapa.items():
        nome = _texto(nome)
        if nome: resultado[_normalizar(nome)] = _texto(iduc)
    return resultado

def _estilos_afin():
    base = getSampleStyleSheet()
    return {
        "instituicao": ParagraphStyle("AFINInstituicao", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=9.2, alignment=TA_CENTER, textColor=AZUL_INSTITUCIONAL),
        "titulo": ParagraphStyle("AFINTitulo", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.2, leading=11, alignment=TA_CENTER, textColor=AZUL_INSTITUCIONAL),
        "subtitulo": ParagraphStyle("AFINSubtitulo", parent=base["Normal"], fontName="Helvetica", fontSize=6.5, leading=7.2, alignment=TA_CENTER, textColor=CINZA_SECUNDARIO),
        "label": ParagraphStyle("AFINLabel", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.9, leading=6.5, alignment=TA_LEFT, textColor=CINZA_SECUNDARIO),
        "valor": ParagraphStyle("AFINValor", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=8.5, alignment=TA_LEFT, textColor=CINZA_TEXTO_AFIN),
        "matricula_header": ParagraphStyle("AFINMatriculaHeader", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.7, leading=6.2, alignment=TA_CENTER, textColor=colors.white),
        "estudante_header": ParagraphStyle("AFINEstudanteHeader", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.7, leading=6.2, alignment=TA_LEFT, textColor=colors.white),
        "uc": ParagraphStyle("AFINUC", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.1, leading=5.5, alignment=TA_CENTER, textColor=AZUL_INSTITUCIONAL),
        "iduc": ParagraphStyle("AFINIDUC", parent=base["Normal"], fontName="Helvetica", fontSize=4.8, leading=5.1, alignment=TA_CENTER, textColor=CINZA_SECUNDARIO),
        "indicador": ParagraphStyle("AFINIndicador", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5, leading=5.2, alignment=TA_CENTER, textColor=colors.white),
        "matricula": ParagraphStyle("AFINMatricula", parent=base["Normal"], fontName="Helvetica", fontSize=6.4, leading=7, alignment=TA_CENTER, textColor=CINZA_TEXTO_AFIN),
        "nome": ParagraphStyle("AFINNome", parent=base["Normal"], fontName="Helvetica", fontSize=6.5, leading=7.1, alignment=TA_LEFT, textColor=CINZA_TEXTO_AFIN),
        "valor_celula": ParagraphStyle("AFINValorCelula", parent=base["Normal"], fontName="Helvetica", fontSize=6.3, leading=6.8, alignment=TA_CENTER, textColor=CINZA_TEXTO_AFIN),
    }

def _blocos(colunas):
    if not colunas: return [[None] * COLUNAS_MATRIZ_POR_PAGINA]
    saida = []
    for inicio in range(0, len(colunas), COLUNAS_MATRIZ_POR_PAGINA):
        bloco = list(colunas[inicio:inicio + COLUNAS_MATRIZ_POR_PAGINA])
        falta = COLUNAS_MATRIZ_POR_PAGINA - len(bloco)
        if falta > 0: bloco.extend([None] * falta)
        saida.append(bloco)
    return saida

def _topo(largura, st):
    dados = [
        [Paragraph("SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL", st["instituicao"])],
        [Paragraph("CEP – ESCOLA TÉCNICA DE PLANALTINA", st["titulo"])],
        [Paragraph("AFIN — ACOMPANHAMENTO DA FREQUÊNCIA E CONCEITO", st["subtitulo"])],
    ]
    tabela = Table(dados, colWidths=[largura], rowHeights=[4.2 * mm, 4.8 * mm, 3.8 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 2), (-1, 2), 0.8, AZUL_INSTITUCIONAL),
    ]))
    return tabela

def _identificacao(largura, turma, semestre, st):
    metade = largura / 2
    dados = [[Paragraph("TURMA", st["label"]), Paragraph(_html(turma), st["valor"]), Paragraph("SEMESTRE", st["label"]), Paragraph(_html(semestre), st["valor"])]]
    larguras = [15 * mm, metade - 15 * mm, 20 * mm, metade - 20 * mm]
    tabela = Table(dados, colWidths=larguras, rowHeights=[7 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), AZUL_MUITO_CLARO),
        ("BACKGROUND", (2, 0), (2, 0), AZUL_MUITO_CLARO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return tabela

def _cabecalho_afin(bloco, mapa, wm, wn, wc, st):
    linha_uc = [Paragraph("MATRÍCULA", st["matricula_header"]), Paragraph("ESTUDANTE", st["estudante_header"])]
    linha_iduc = [Paragraph("", st["matricula_header"]), Paragraph("", st["estudante_header"])]
    linha_indicador = [Paragraph("", st["matricula_header"]), Paragraph("", st["estudante_header"])]
    larguras = [wm, wn]

    for nome_coluna in bloco:
        larguras.append(wc)
        if nome_coluna is None:
            linha_uc.append(Paragraph("", st["uc"]))
            linha_iduc.append(Paragraph("", st["iduc"]))
            linha_indicador.append(Paragraph("", st["indicador"]))
            continue
        uc = _nome_uc(nome_coluna)
        iduc = mapa.get(_normalizar(uc), "")
        tipo = _tipo_coluna(nome_coluna)
        linha_uc.append(Paragraph(_html(uc), st["uc"]))
        linha_iduc.append(Paragraph(_html(iduc), st["iduc"]))
        indicador = "F" if tipo == "FAL" else ("C" if tipo == "CON" else "")
        linha_indicador.append(Paragraph(indicador, st["indicador"]))

    return [linha_uc, linha_iduc, linha_indicador], larguras

def _tabela_afin(df, bloco, mapa, wm, wn, wc, st):
    cabecalho, larguras = _cabecalho_afin(bloco, mapa, wm, wn, wc, st)
    posicoes = {coluna: indice for indice, coluna in enumerate(df.columns)}
    linhas = list(cabecalho)

    for _, row in df.iterrows():
        linha = [Paragraph(_html(row.iloc[0]), st["matricula"]), Paragraph(_html(row.iloc[1]), st["nome"])]
        for coluna in bloco:
            valor = "" if coluna is None else _texto(row.iloc[posicoes[coluna]])
            linha.append(Paragraph(_html(valor), st["valor_celula"]))
        linhas.append(linha)

    tabela = Table(linhas, colWidths=larguras, repeatRows=3, hAlign="LEFT")
    comandos = [
        ("BACKGROUND", (0, 0), (1, 2), AZUL_INSTITUCIONAL),
        ("BACKGROUND", (2, 0), (-1, 0), AZUL_MUITO_CLARO),
        ("BACKGROUND", (2, 1), (-1, 1), colors.white),
        ("BACKGROUND", (2, 2), (-1, 2), AZUL_SECUNDARIO),
        ("BACKGROUND", (0, 3), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 3), (1, -1), "LEFT"),
        ("LINEBELOW", (0, 2), (-1, 2), 0.65, AZUL_INSTITUCIONAL),
        ("LINEAFTER", (0, 0), (0, -1), 0.45, CINZA_LINHA),
        ("LINEAFTER", (1, 0), (1, -1), 0.8, AZUL_SECUNDARIO),
        ("TOPPADDING", (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.0),
    ]
    for indice in range(3, len(linhas)):
        if (indice - 3) % 2 == 1:
            comandos.append(("BACKGROUND", (0, indice), (-1, indice), CINZA_ZEBRA))
    tabela.setStyle(TableStyle(comandos))
    return tabela

def _rodape_afin(canvas, doc):
    canvas.saveState()
    largura_pagina, _ = landscape(A4)
    y = 5.0 * mm
    canvas.setStrokeColor(CINZA_LINHA)
    canvas.setLineWidth(0.3)
    canvas.line(MARGEM_ESQ, y + 3.2 * mm, largura_pagina - MARGEM_DIR, y + 3.2 * mm)
    canvas.setFont("Helvetica", 5.4)
    canvas.setFillColor(CINZA_SECUNDARIO)
    canvas.drawString(MARGEM_ESQ, y, "CEP ETP • AFIN")
    canvas.drawRightString(largura_pagina - MARGEM_DIR, y, f"Página {doc.page}")
    canvas.restoreState()

def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    df = df_matriz.copy() if df_matriz is not None else pd.DataFrame()
    if not df.empty and len(df.columns) >= 2:
        cols = list(df.columns)
        if not _texto(cols[0]): cols[0] = "Matrícula"
        if not _texto(cols[1]): cols[1] = "Estudante"
        df.columns = cols

    buffer = io.BytesIO()
    pagina = landscape(A4)
    largura_pagina, _ = pagina
    largura_util = largura_pagina - MARGEM_ESQ - MARGEM_DIR

    doc = SimpleDocTemplate(
        buffer, pagesize=pagina, leftMargin=MARGEM_ESQ, rightMargin=MARGEM_DIR,
        topMargin=MARGEM_SUP, bottomMargin=MARGEM_INF, title="Matriz AFIN"
    )
    st = _estilos_afin()
    mapa = _mapa_iduc(mapa_nomes_iduc)
    colunas = list(df.columns[2:]) if not df.empty else []
    blocos = _blocos(colunas)
    largura_restante = largura_util - LARGURA_MATRICULA - LARGURA_ESTUDANTE
    largura_coluna = largura_restante / COLUNAS_MATRIZ_POR_PAGINA

    story = []
    for numero_bloco, bloco in enumerate(blocos, start=1):
        if numero_bloco > 1: story.append(PageBreak())
        story.append(_topo(largura_util, st))
        story.append(Spacer(1, 1.6 * mm))
        story.append(_identificacao(largura_util, turma, semestre, st))
        story.append(Spacer(1, 1.7 * mm))
        if df.empty:
            story.append(Paragraph("Nenhum registro disponível.", st["nome"]))
        else:
            story.append(_tabela_afin(df, bloco, mapa, LARGURA_MATRICULA, LARGURA_ESTUDANTE, largura_coluna, st))

    doc.build(story, onFirstPage=_rodape_afin, onLaterPages=_rodape_afin)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 3. RELATÓRIO DE TURMA
# ============================================================

def gerar_pdf_relatorio_turma(dados):
    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n% Relatorio da Turma em desenvolvimento\n")
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 4. DECLARAÇÃO DE ESCOLARIDADE
# ============================================================

def gerar_pdf_declaracao_escolaridade(dados_aluno):
    def get_dado(dados, *chaves):
        if not isinstance(dados, dict): return ""
        for chave in chaves:
            if chave in dados and dados[chave] is not None:
                val = str(dados[chave]).strip()
                if val and val.lower() != "none": return val
            target = chave.lower().replace(" ", "_").replace(":", "")
            for k, v in dados.items():
                if k.lower().replace(" ", "_").replace(":", "") == target and v is not None:
                    val = str(v).strip()
                    if val and val.lower() != "none": return val
        return ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    style_header_title = ParagraphStyle("HeaderTitle", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=12)
    style_header_sub = ParagraphStyle("HeaderSub", fontName="Helvetica", fontSize=8, alignment=1, leading=10)
    style_doc_title = ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=11, alignment=1, leading=13)
    style_label = ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=colors.HexColor("#333333"))
    style_val = ParagraphStyle("Val", fontName="Helvetica", fontSize=8, leading=10)
    style_obs = ParagraphStyle("ObsText", fontName="Helvetica", fontSize=8, leading=12)

    PAGE_WIDTH = 523

    img_gdf = Image("logo_gdf.png", width=50, height=50) if os.path.exists("logo_gdf.png") else Paragraph("", styles["Normal"])
    img_escola = Image("logo_escola.png", width=50, height=50) if os.path.exists("logo_escola.png") else Paragraph("", styles["Normal"])

    header_text = [
        Paragraph("<b>Governo do Distrito Federal</b>", style_header_title),
        Paragraph("Secretaria de Estado de Educação", style_header_sub),
        Paragraph("Subsecretaria de Educação Básica", style_header_sub),
        Paragraph("Coordenação Regional de Ensino de Planaltina", style_header_sub),
        Paragraph("<b>Centro de Educação Profissional - Escola Técnica de Planaltina</b>", style_header_sub),
    ]

    tabela_cabecalho = Table([[img_gdf, header_text, img_escola]], colWidths=[60, PAGE_WIDTH - 120, 60])
    tabela_cabecalho.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(tabela_cabecalho)

    tabela_titulo = Table([[Paragraph("DECLARAÇÃO DE ESCOLARIDADE", style_doc_title)]], colWidths=[PAGE_WIDTH])
    tabela_titulo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(tabela_titulo)

    def celula(rotulo, valor):
        v = str(valor) if valor and str(valor).lower() != "none" else ""
        return [Paragraph(rotulo, style_label), Paragraph(f"<b>{v}</b>", style_val)]

    curso = get_dado(dados_aluno, "curso")
    matricula = get_dado(dados_aluno, "matricula", "matricula_aluno")
    turma = get_dado(dados_aluno, "turma", "turma_turno")
    nome = get_dado(dados_aluno, "nome", "nome_aluno")
    sexo = get_dado(dados_aluno, "sexo")
    data_nascimento = get_dado(dados_aluno, "data_nascimento", "dt_nascimento")
    nacionalidade = get_dado(dados_aluno, "nacionalidade") or "BRASILEIRA"
    naturalidade = get_dado(dados_aluno, "naturalidade", "cidade")
    uf = get_dado(dados_aluno, "uf") or "DF"
    rg = get_dado(dados_aluno, "rg", "identidade")
    orgao_expeditor = get_dado(dados_aluno, "org_expedidor", "orgao_expeditor")
    data_expedicao = get_dado(dados_aluno, "dta_expedicao", "data_expedicao")
    cpf = get_dado(dados_aluno, "cpf")
    nome_mae = get_dado(dados_aluno, "nome_mae", "mae")
    raw_pai = get_dado(dados_aluno, "nome_pai", "pai")
    nome_pai = "" if raw_pai.lower() in ["não sei", "nao sei", "não informado", "-"] else raw_pai
    endereco_final = f"{get_dado(dados_aluno, 'endereco')} {get_dado(dados_aluno, 'bairro')}".strip()
    cep = get_dado(dados_aluno, "cep")

    dados_grid = [
        [celula("Curso:", curso), "", "", "", "", "", "", ""],
        [celula("Matrícula:", matricula), "", celula("Turma/Turno:", turma), "", celula("Nome:", nome), "", "", celula("Sexo:", sexo)],
        [celula("Data de Nascimento:", data_nascimento), celula("Nacionalidade:", nacionalidade), celula("Naturalidade:", naturalidade), celula("UF:", uf), celula("Identidade:", rg), celula("Órg. Exp.:", orgao_expeditor), celula("Data de Expedição:", data_expedicao), ""],
        [celula("CPF:", cpf), "", celula("Nome da Mãe:", nome_mae), "", "", "", "", ""],
        [celula("", ""), "", celula("Nome do Pai:", nome_pai), "", "", "", "", ""],
        [celula("Endereço:", endereco_final), "", "", "", celula("CEP:", cep), "", celula("UF:", uf), ""],
    ]

    tabela_dados = Table(dados_grid, colWidths=[75, 75, 70, 35, 95, 55, 64, 54])
    tabela_dados.setStyle(TableStyle([
        ("SPAN", (0, 0), (7, 0)), ("SPAN", (0, 1), (1, 1)), ("SPAN", (2, 1), (3, 1)), ("SPAN", (4, 1), (6, 1)),
        ("SPAN", (2, 3), (7, 3)), ("SPAN", (2, 4), (7, 4)), ("SPAN", (0, 5), (3, 5)), ("SPAN", (4, 5), (5, 5)), ("SPAN", (6, 5), (7, 5)),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(tabela_dados)

    obs_content = [
        Paragraph("<b>Observações:</b>", style_label),
        Paragraph("• <b>Turno Matutino:</b> Aulas de 08h00min às 12h00min.", style_obs),
        Paragraph("• <b>Turno Vespertino:</b> Aulas de 13h30min às 17h30min.", style_obs),
        Paragraph("• <b>Turno Noturno:</b> Aulas de 19h00min às 23h00min.", style_obs),
        Paragraph("• Declaração válida somente sem emendas por 30 dias.", style_obs),
        Paragraph("• <b>Observação: O(a) aluno(a) está regularmente matriculado(a).</b>", style_obs),
    ]
    tabela_obs = Table([[obs_content]], colWidths=[PAGE_WIDTH])
    tabela_obs.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black), ("BOTTOMPADDING", (0, 0), (-1, -1), 120)]))
    story.append(tabela_obs)

    data_atual = datetime.now().strftime("%d/%m/%Y")
    tabela_rodape = Table([[Paragraph(f"<b>PLANALTINA-DF, {data_atual}</b>", style_obs), ""],
                           [Paragraph("_____________________________________________________<br/><b>Secretaria Escolar</b>", ParagraphStyle("Sig", fontName="Helvetica", fontSize=8, alignment=1)), ""]],
                          colWidths=[PAGE_WIDTH / 2, PAGE_WIDTH / 2])
    tabela_rodape.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("BOX", (0, 0), (-1, -1), 1, colors.black), ("ALIGN", (0, 1), (-1, -1), "CENTER")]))
    story.append(tabela_rodape)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 5. PASSE ESTUDANTIL
# ============================================================

def gerar_pdf_passe_estudantil(dados_aluno):
    def get_dado(dados, *chaves):
        if not isinstance(dados, dict): return ""
        for chave in chaves:
            if chave in dados and dados[chave] is not None:
                val = str(dados[chave]).strip()
                if val and val.lower() != "none": return val
            target = chave.lower().replace(" ", "_").replace(":", "")
            for k, v in dados.items():
                if k.lower().replace(" ", "_").replace(":", "") == target and v is not None:
                    val = str(v).strip()
                    if val and val.lower() != "none": return val
        return ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    style_header_title = ParagraphStyle("HeaderTitle", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=12)
    style_header_sub = ParagraphStyle("HeaderSub", fontName="Helvetica", fontSize=8, alignment=1, leading=10)
    style_doc_title = ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=11, alignment=1, leading=13)
    style_label = ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=colors.HexColor("#333333"))
    style_val = ParagraphStyle("Val", fontName="Helvetica", fontSize=8, leading=10)
    style_obs = ParagraphStyle("ObsText", fontName="Helvetica", fontSize=8, leading=12)

    PAGE_WIDTH = 523

    img_gdf = Image("logo_gdf.png", width=50, height=50) if os.path.exists("logo_gdf.png") else Paragraph("", styles["Normal"])
    img_escola = Image("logo_escola.png", width=50, height=50) if os.path.exists("logo_escola.png") else Paragraph("", styles["Normal"])

    header_text = [
        Paragraph("<b>Governo do Distrito Federal</b>", style_header_title),
        Paragraph("Secretaria de Estado de Educação", style_header_sub),
        Paragraph("Subsecretaria de Educação Básica", style_header_sub),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina", style_header_sub),
    ]

    tabela_cabecalho = Table([[img_gdf, header_text, img_escola]], colWidths=[60, PAGE_WIDTH - 120, 60])
    tabela_cabecalho.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(tabela_cabecalho)

    tabela_titulo = Table([[Paragraph("DECLARAÇÃO PARA OBTENÇÃO DE PASSE ESTUDANTIL", style_doc_title)]], colWidths=[PAGE_WIDTH])
    tabela_titulo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(tabela_titulo)

    def celula(rotulo, valor):
        v = str(valor) if valor and str(valor).lower() != "none" else ""
        return [Paragraph(rotulo, style_label), Paragraph(f"<b>{v}</b>", style_val)]

    curso = get_dado(dados_aluno, "curso")
    matricula = get_dado(dados_aluno, "matricula", "matricula_aluno")
    turma = get_dado(dados_aluno, "turma", "turma_turno")
    nome = get_dado(dados_aluno, "nome", "nome_aluno")
    sexo = get_dado(dados_aluno, "sexo")
    data_nascimento = get_dado(dados_aluno, "data_nascimento", "dt_nascimento")
    nacionalidade = get_dado(dados_aluno, "nacionalidade") or "BRASILEIRA"
    naturalidade = get_dado(dados_aluno, "naturalidade", "cidade")
    uf = get_dado(dados_aluno, "uf") or "DF"
    rg = get_dado(dados_aluno, "rg", "identidade")
    orgao_expeditor = get_dado(dados_aluno, "org_expedidor", "orgao_expeditor")
    data_expedicao = get_dado(dados_aluno, "dta_expedicao", "data_expedicao")
    cpf = get_dado(dados_aluno, "cpf")
    nome_mae = get_dado(dados_aluno, "nome_mae", "mae")
    raw_pai = get_dado(dados_aluno, "nome_pai", "pai")
    nome_pai = "" if raw_pai.lower() in ["não sei", "nao sei", "não informado", "-"] else raw_pai
    nome_responsavel = get_dado(dados_aluno, "nome_responsavel")
    endereco = get_dado(dados_aluno, "endereco")
    bairro = get_dado(dados_aluno, "bairro")
    cidade = get_dado(dados_aluno, "cidade") or "PLANALTINA"
    uf_federacao = get_dado(dados_aluno, "uf_federacao", "uf") or "DF"
    cep = get_dado(dados_aluno, "cep")

    dados_grid = [
        [celula("Curso:", curso), "", "", "", "", "", "", ""],
        [celula("Matrícula:", matricula), "", celula("Turma/ Turno:", turma), "", celula("Nome:", nome), "", "", celula("Sexo:", sexo)],
        [celula("Data de Nascimento:", data_nascimento), celula("Nacionalidade:", nacionalidade), celula("Naturalidade:", naturalidade), celula("UF:", uf), celula("Identidade:", rg), celula("Org. Exp.:", orgao_expeditor), celula("Data de Expedição:", data_expedicao), ""],
        [celula("CPF:", cpf), "", celula("Nome da Mãe:", nome_mae), "", "", "", "", ""],
        [celula("", ""), "", celula("Nome do Pai:", nome_pai), "", "", "", "", ""],
        [celula("", ""), "", celula("Nome do Responsável:", nome_responsavel), "", "", "", "", ""],
        [celula("Endereço:", endereco), "", "", "", celula("Bairro:", bairro), "", "", ""],
        [celula("Cidade:", cidade), "", celula("Unidade da Federação:", uf_federacao), "", "", celula("CEP:", cep), "", ""]
    ]

    tabela_dados = Table(dados_grid, colWidths=[75, 75, 70, 35, 95, 55, 64, 54])
    tabela_dados.setStyle(TableStyle([
        ("SPAN", (0, 0), (7, 0)), ("SPAN", (0, 1), (1, 1)), ("SPAN", (2, 1), (3, 1)), ("SPAN", (4, 1), (6, 1)),
        ("SPAN", (2, 3), (7, 3)), ("SPAN", (2, 4), (7, 4)), ("SPAN", (2, 5), (7, 5)), ("SPAN", (0, 6), (3, 6)),
        ("SPAN", (4, 6), (7, 6)), ("SPAN", (0, 7), (1, 7)), ("SPAN", (2, 7), (4, 7)), ("SPAN", (5, 7), (7, 7)),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(tabela_dados)

    obs_content = [
        Paragraph("<b>Observações:</b>", style_label),
        Paragraph("• Turno Matutino: Aulas de 8h00min às 12h00min.", style_obs),
        Paragraph("• Turno Vespertino: Aulas de 13h30min às 17h30min.", style_obs),
        Paragraph("• Turno Noturno: Aulas de 19h00min às 23h00min.", style_obs),
        Paragraph("• Declaração válida por 30 dias.", style_obs),
        Paragraph("• Início do 1º Semestre: 12/02/2026 – Término: 10/07/2026.", style_obs),
        Paragraph("• Início do 2º Semestre: 28/07/2026 – Término: 22/12/2026.", style_obs),
        Paragraph("• <b>Observação: O(a) aluno(a) está regularmente matriculado(a).</b>", style_obs),
    ]
    tabela_obs = Table([[obs_content]], colWidths=[PAGE_WIDTH])
    tabela_obs.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black), ("BOTTOMPADDING", (0, 0), (-1, -1), 80)]))
    story.append(tabela_obs)

    data_atual = datetime.now().strftime("%d/%m/%Y")
    tabela_rodape = Table([[Paragraph(f"<b>PLANALTINA-DF,</b> {data_atual}", style_obs), ""],
                           [Paragraph("_____________________________________________________<br/><b>Secretário(a) Escolar</b>", ParagraphStyle("Sig", fontName="Helvetica", fontSize=8, alignment=1)), ""]],
                          colWidths=[PAGE_WIDTH / 2, PAGE_WIDTH / 2])
    tabela_rodape.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("BOX", (0, 0), (-1, -1), 1, colors.black), ("ALIGN", (0, 1), (-1, -1), "CENTER")]))
    story.append(tabela_rodape)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
