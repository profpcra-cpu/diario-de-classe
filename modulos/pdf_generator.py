import io
import os
import re
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from modulos.conexao import executar_query


# ======================================================================
# CONSTANTES GLOBAIS
# ======================================================================
LARGURA_UTIL   = 554.0
MARGEM_LATERAL = 20.6

CINZA_TEXTO  = colors.HexColor("#263238")
CINZA_MEDIO  = colors.HexColor("#5F6B72")
CINZA_LINHA  = colors.HexColor("#A0AAB0")
CINZA_CAB    = colors.HexColor("#E7EAEC")
PRETO        = colors.HexColor("#111111")

# Fundos agora em BRANCO puro (antes #FAFAFA / #F7F8F8 com tom rosado)
BRANCO       = colors.white

BASE_LEGAL_PADRAO = (
    "LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 04/99 - CEB/CNE, "
    "RESOLUÇÃO Nº 02/2023 - CEDF, PARECER Nº 27/2013-CEDF, PORTARIA Nº 56/2013 SEDF"
)

CURSO_PADRAO = "CURSO TÉCNICO EM NUTRIÇÃO E DIETÉTICA"

DATA_DOCUMENTO = "PLANALTINA-DF, 27 DE SETEMBRO DE 2026"

VALORES_INVALIDOS = {"", "nan", "none", "null"}

_COLUNAS_HISTORICO = {
    "componente": ("unidade_curricular", "componente", "disciplina"),
    "ch":         ("carga_horaria", "ch"),
    "resultado":  ("resultado", "conceito"),
}

_REGEX_COMP = re.compile(r"compet[êe]ncias?\s*:?", re.IGNORECASE)
_REGEX_HAB  = re.compile(r"habilidades?\s*:?",        re.IGNORECASE)


# ======================================================================
# ESTILOS (criados UMA vez no import)
# ======================================================================
def _build_styles():
    base = getSampleStyleSheet()

    def _p(name, parent, **kw):
        return ParagraphStyle(name, parent=parent, **kw)

    inst = _p("Institucional", base["Normal"],
              fontName="Helvetica", fontSize=7.5, leading=8.5,
              alignment=TA_CENTER, textColor=PRETO)

    return {
        "institucional": inst,
        "institucional_bold": _p("InstitucionalBold", inst,
                                 fontName="Helvetica-Bold", fontSize=7.8, leading=8.8),
        "titulo": _p("TituloHistorico", base["Heading1"],
                     fontName="Helvetica-Bold", fontSize=12, leading=14,
                     alignment=TA_CENTER, textColor=PRETO,
                     spaceBefore=3, spaceAfter=3),
        "label": _p("Label", base["Normal"],
                    fontName="Helvetica-Bold", fontSize=6.0, leading=6.8,
                    textColor=CINZA_MEDIO, spaceAfter=1),
        "valor": _p("Valor", base["Normal"],
                    fontName="Helvetica", fontSize=7.2, leading=8.2,
                    textColor=CINZA_TEXTO),
        "valor_bold": _p("ValorBold", base["Normal"],
                         fontName="Helvetica-Bold", fontSize=7.2, leading=8.2,
                         textColor=PRETO),
        "th": _p("TH", base["Normal"],
                 fontName="Helvetica-Bold", fontSize=6.8, leading=7.6,
                 alignment=TA_CENTER, textColor=PRETO),
        "td": _p("TD", base["Normal"],
                 fontName="Helvetica", fontSize=6.8, leading=7.6,
                 alignment=TA_CENTER, textColor=CINZA_TEXTO),
        "td_left": _p("TDLeft", base["Normal"],
                      fontName="Helvetica", fontSize=6.8, leading=7.6,
                      alignment=TA_LEFT, textColor=CINZA_TEXTO),
        "rodape": _p("Rodape", base["Normal"],
                     fontName="Helvetica", fontSize=6.5, leading=7.5,
                     textColor=CINZA_MEDIO),
        "assinatura": _p("Assinatura", base["Normal"],
                         fontName="Helvetica", fontSize=7, leading=8,
                         alignment=TA_CENTER, textColor=PRETO),
        # --- página 2 ---
        "secao_titulo": _p("SecaoTitulo", base["Normal"],
                           fontName="Helvetica-Bold", fontSize=8, leading=10,
                           alignment=TA_LEFT, textColor=PRETO,
                           spaceBefore=2, spaceAfter=3),
        "secao_texto": _p("SecaoTexto", base["Normal"],
                          fontName="Helvetica", fontSize=7, leading=9,
                          alignment=TA_LEFT, textColor=CINZA_TEXTO,
                          leftIndent=6, spaceAfter=1),
        "certificacao": _p("Certificacao", base["Normal"],
                           fontName="Helvetica", fontSize=7.2, leading=9.5,
                           alignment=TA_LEFT, textColor=PRETO),
    }


STYLES = _build_styles()


# ======================================================================
# HELPERS
# ======================================================================
def _valor(d, *chaves, padrao=""):
    for chave in chaves:
        v = d.get(chave)
        if v is not None and str(v).strip().lower() not in VALORES_INVALIDOS:
            return str(v).strip()
    return padrao


def _row_get(row, chaves, padrao=""):
    for chave in chaves:
        v = row.get(chave)
        if v is not None and str(v).strip().lower() not in VALORES_INVALIDOS:
            return v
    return padrao


def _buscar_base_legal(sigla, turma):
    """
    Retorna (base_legal, competencias_habilidades).
    Faz fallback para BASE_LEGAL_PADRAO / '' em caso de erro.
    """
    if not (sigla and turma):
        return BASE_LEGAL_PADRAO, ""

    try:
        df = executar_query(
            """SELECT base_legal, competencias_habilidades
               FROM TB_BASE_LEGAL
               WHERE sigla = %s AND turma = %s""",
            params=(sigla, turma),
        )
        if not df.empty:
            linha = df.iloc[0]
            bl  = linha.get("base_legal")
            ch  = linha.get("competencias_habilidades")

            bl = str(bl).strip() if pd.notnull(bl) and str(bl).strip() else BASE_LEGAL_PADRAO
            ch = str(ch).strip() if pd.notnull(ch) else ""
            return bl, ch
    except Exception as exc:
        print(f"[gerar_pdf_historico_aluno] Falha ao buscar base legal: {exc}")

    return BASE_LEGAL_PADRAO, ""


def _carregar_logo(path, width=38, height=38):
    if os.path.exists(path):
        return Image(path, width=width, height=height)
    return Paragraph("", STYLES["valor"])


def _celula_campo(rotulo, valor_txt, negrito=False):
    return [
        Paragraph(rotulo, STYLES["label"]),
        Paragraph(valor_txt or "—", STYLES["valor_bold" if negrito else "valor"]),
    ]


def _separar_competencias(texto):
    """
    Divide o texto bruto em (bloco_competencias, bloco_habilidades).
    Detecta marcadores 'COMPETÊNCIAS:' e 'HABILIDADES:' com ou sem acento.
    """
    texto = (texto or "").replace("\r\n", "\n").strip()
    if not texto:
        return "", ""

    m_comp = _REGEX_COMP.search(texto)
    m_hab  = _REGEX_HAB.search(texto)

    if m_comp and m_hab and m_hab.start() > m_comp.start():
        return (texto[m_comp.end():m_hab.start()].strip(),
                texto[m_hab.end():].strip())
    if m_comp:
        return texto[m_comp.end():].strip(), ""
    if m_hab:
        return "", texto[m_hab.end():].strip()

    return texto, ""


# ======================================================================
# CABEÇALHO INSTITUCIONAL (reutilizado em todas as páginas)
# ======================================================================
def _montar_cabecalho():
    texto_institucional = [
        Paragraph("GOVERNO DO DISTRITO FEDERAL", STYLES["institucional_bold"]),
        Paragraph("Secretaria de Estado de Educação", STYLES["institucional"]),
        Paragraph("Subsecretaria de Educação Básica", STYLES["institucional"]),
        Paragraph("Coordenação Regional de Ensino de Planaltina", STYLES["institucional"]),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina",
                  STYLES["institucional_bold"]),
    ]

    cabecalho = Table(
        [[_carregar_logo("logo_gdf.png"),
          texto_institucional,
          _carregar_logo("logo_escola.png")]],
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

    return [cabecalho, Paragraph("HISTÓRICO ESCOLAR", STYLES["titulo"])]


# ======================================================================
# MONTAGEM — PÁGINA 2
# ======================================================================
def _montar_segunda_pagina(competencias_txt, nome, curso, matricula, data_doc):
    story = []
    bloco_comp, bloco_hab = _separar_competencias(competencias_txt)

    # --- COMPETÊNCIAS ---
    story.append(Paragraph("<b>COMPETÊNCIAS:</b>", STYLES["secao_titulo"]))
    if bloco_comp:
        for linha in filter(None, (l.strip() for l in bloco_comp.split("\n"))):
            story.append(Paragraph(f"• {linha}", STYLES["secao_texto"]))
    else:
        story.append(Paragraph("—", STYLES["secao_texto"]))
    story.append(Spacer(1, 6))

    # --- HABILIDADES ---
    story.append(Paragraph("<b>HABILIDADES:</b>", STYLES["secao_titulo"]))
    if bloco_hab:
        for linha in filter(None, (l.strip() for l in bloco_hab.split("\n"))):
            story.append(Paragraph(f"• {linha}", STYLES["secao_texto"]))
    else:
        story.append(Paragraph("—", STYLES["secao_texto"]))
    story.append(Spacer(1, 14))

    # --- Caixa de certificação (fundo branco) ---
    texto_cert = (
        f"O <b>Centro de Educação Profissional – Escola Técnica de Planaltina</b>, "
        f"no uso de suas atribuições, certifica que o(a) aluno(a) "
        f"<b>{nome or '—'}</b>, matrícula nº <b>{matricula or '—'}</b>, "
        f"concluiu o <b>{curso or '—'}</b>, com carga horária total de "
        f"<b>1.366 horas</b> (T. Teoria: 1.366 h / T. Prática: 0 h), "
        f"tendo sido considerado(a) <b>APTO(A)</b> em todos os componentes "
        f"curriculares, conforme a legislação vigente."
    )

    tabela_cert = Table(
        [[Paragraph(texto_cert, STYLES["certificacao"])]],
        colWidths=[LARGURA_UTIL],
        hAlign="LEFT",
    )
    tabela_cert.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, -1), BRANCO),   # ← sem fundo rosado
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))

    story.append(tabela_cert)
    story.append(Spacer(1, 10))

    # --- Cidade / Data ---
    data_tabela = Table(
        [[Paragraph(data_doc, STYLES["assinatura"])]],
        colWidths=[LARGURA_UTIL],
        hAlign="LEFT",
    )
    data_tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(data_tabela)

    # --- Assinaturas (Diretor / Secretária Escolar) ---
    story.append(Spacer(1, 40))
    assinatura2 = Table(
        [[
            Paragraph("____________________________________________<br/><b>DIRETOR</b>",
                      STYLES["assinatura"]),
            Paragraph("____________________________________________<br/><b>SECRETÁRIA ESCOLAR</b>",
                      STYLES["assinatura"]),
        ]],
        colWidths=[277, 277],
        rowHeights=[43],
        hAlign="LEFT",
    )
    assinatura2.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))

    story.append(assinatura2)
    return story


# ======================================================================
# FUNÇÃO PRINCIPAL
# ======================================================================
def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """Gera o Histórico Escolar em 2 páginas A4, com cabeçalho repetido."""

    # Compatibilidade com chamada invertida
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGEM_LATERAL,
        leftMargin=MARGEM_LATERAL,
        topMargin=20,
        bottomMargin=22,
        title="Histórico Escolar",
        author="Centro de Educação Profissional Escola Técnica de Planaltina",
    )

    # ------------------------------------------------------------------
    # Dados do aluno
    # ------------------------------------------------------------------
    if isinstance(dados_aluno, dict):
        d = dados_aluno
    elif hasattr(dados_aluno, "iloc") and not dados_aluno.empty:
        d = dados_aluno.iloc[0].to_dict()
    else:
        d = {}

    sigla     = _valor(d, "sigla")
    turma     = _valor(d, "turma")
    curso     = _valor(d, "curso", padrao=CURSO_PADRAO).upper()
    nome      = _valor(d, "nome").upper()
    cpf       = _valor(d, "cpf")
    sexo      = _valor(d, "sexo").upper()
    mae       = _valor(d, "mae", "nome_mae").upper()
    pai       = _valor(d, "pai", "nome_pai").upper()
    dt_nasc   = _valor(d, "data_nascimento")
    matricula = _valor(d, "matricula", "matrícula")

    nacionalidade = (_valor(d, "nacionalidade", padrao="BRASILEIRA")
                     .upper().replace(" ", "")) or "BRASILEIRA"

    naturalidade = _valor(d, "naturalidade").upper()
    uf           = _valor(d, "uf", padrao="DF").upper()

    rg     = _valor(d, "rg")
    orgao  = _valor(d, "orgao_expeditor", "orgao").upper()
    dt_exp = _valor(d, "data_expedicao")
    doc_rg_str = " - ".join(x for x in (rg, orgao, dt_exp) if x) or "—"

    base_legal_texto, competencias_habilidades = _buscar_base_legal(sigla, turma)

    # ------------------------------------------------------------------
    # PÁGINA 1 — Cabeçalho
    # ------------------------------------------------------------------
    story = _montar_cabecalho()

    # ------------------------------------------------------------------
    # Grade de dados do estudante
    # ------------------------------------------------------------------
    dados_estudante_grid = [
        [
            _celula_campo("Curso", curso, True),
            _celula_campo("Nome", nome, True),
            _celula_campo("CPF", cpf),
            _celula_campo("Sexo", sexo),
        ],
        [
            _celula_campo("Matrícula", matricula, True),
            _celula_campo("Turma", turma, True),
            _celula_campo("Nome da Mãe", mae),
            _celula_campo("Nome do Pai", pai),
        ],
        [
            _celula_campo("Data de Nascimento", dt_nasc),
            _celula_campo("Nacionalidade", nacionalidade),
            _celula_campo("Naturalidade / UF", f"{naturalidade} / {uf}".strip(" /")),
            _celula_campo("RG / Órgão / Expedição", doc_rg_str),
        ],
    ]

    tabela_dados = Table(dados_estudante_grid,
                         colWidths=[130, 184, 140, 100], hAlign="LEFT")
    tabela_dados.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(tabela_dados)

    # ------------------------------------------------------------------
    # Base legal (fundo branco)
    # ------------------------------------------------------------------
    tabela_base_legal = Table(
        [[[Paragraph("Base Legal", STYLES["label"]),
           Paragraph(base_legal_texto, STYLES["valor"])]]],
        colWidths=[LARGURA_UTIL],
        hAlign="LEFT",
    )
    tabela_base_legal.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, -1), BRANCO),   # ← sem fundo rosado
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    story.append(tabela_base_legal)
    story.append(Spacer(1, 4))

    # ------------------------------------------------------------------
    # Histórico acadêmico (sem zebra; só linhas de grade)
    # ------------------------------------------------------------------
    tabela_hist_dados = [[
        Paragraph("Componente Curricular", STYLES["th"]),
        Paragraph("Semestre", STYLES["th"]),
        Paragraph("CH", STYLES["th"]),
        Paragraph("Módulo", STYLES["th"]),
        Paragraph("Faltas", STYLES["th"]),
        Paragraph("Resultado", STYLES["th"]),
    ]]

    if df_historico is not None and not df_historico.empty:
        for _, row in df_historico.iterrows():
            sem = str(row.get("semestre", "")).strip()
            comp = _row_get(row, _COLUNAS_HISTORICO["componente"], "---")

            if not sem or sem.lower() in VALORES_INVALIDOS:
                tabela_hist_dados.append([
                    Paragraph(str(comp), STYLES["td_left"]),
                    *[Paragraph("", STYLES["td"]) for _ in range(5)],
                ])
                continue

            ch     = _row_get(row, _COLUNAS_HISTORICO["ch"], "")
            modulo = row.get("modulo", "")
            faltas = row.get("faltas", "0")
            res    = _row_get(row, _COLUNAS_HISTORICO["resultado"], "")

            tabela_hist_dados.append([
                Paragraph(str(comp), STYLES["td_left"]),
                Paragraph(sem, STYLES["td"]),
                Paragraph(str(ch), STYLES["td"]),
                Paragraph(str(modulo), STYLES["td"]),
                Paragraph(str(faltas), STYLES["td"]),
                Paragraph(str(res), STYLES["td"]),
            ])

    t_hist = Table(tabela_hist_dados, repeatRows=1,
                   colWidths=[314, 50, 35, 55, 40, 60], hAlign="LEFT")

    estilo_hist = [
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CAB),
        ("LINEBELOW",  (0, 0), (-1, 0), 0.7, CINZA_LINHA),
        ("GRID",       (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2.5),
    ]
    # Sem zebra: nenhum BACKGROUND nas linhas de dados (fundo branco natural)

    t_hist.setStyle(TableStyle(estilo_hist))
    story.append(t_hist)
    story.append(Spacer(1, 5))

    # ------------------------------------------------------------------
    # Bloco final da página 1 (sem fundo rosado)
    # ------------------------------------------------------------------
    rodape_legenda = Table(
        [[
            Paragraph(
                "<b>Legenda:</b> AP = Apto; AE = Aproveitamento de Estudos; "
                "NA = Não Apto; TR = Trancamento de Curso; D = Desistente",
                STYLES["rodape"]),
            Paragraph("<b>T. Teoria:</b> 1.366 h", STYLES["rodape"]),
            Paragraph("<b>T. Prática:</b> 0 h", STYLES["rodape"]),
        ]],
        colWidths=[350, 102, 102],
        hAlign="LEFT",
    )
    rodape_legenda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRANCO),   # ← sem fundo rosado
        ("BOX",        (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))

    data_tabela = Table(
        [[Paragraph(DATA_DOCUMENTO, STYLES["assinatura"])]],
        colWidths=[LARGURA_UTIL],
        hAlign="LEFT",
    )
    data_tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    assinatura = Table(
        [[
            Paragraph("____________________________________________<br/><b>Diretor(a)</b>",
                      STYLES["assinatura"]),
            Paragraph("____________________________________________<br/><b>Chefe de Secretaria Escolar</b>",
                      STYLES["assinatura"]),
        ]],
        colWidths=[277, 277],
        rowHeights=[43],
        hAlign="LEFT",
    )
    assinatura.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))

    story.append(KeepTogether([
        rodape_legenda,
        Spacer(1, 8),
        data_tabela,
        Spacer(1, 20),
        assinatura,
    ]))

    # ------------------------------------------------------------------
    # PÁGINA 2 — Cabeçalho repetido + Competências/Habilidades
    # ------------------------------------------------------------------
    story.append(PageBreak())
    story.extend(_montar_cabecalho())   # ← cabeçalho institucional repetido
    story.extend(
        _montar_segunda_pagina(
            competencias_txt=competencias_habilidades,
            nome=nome,
            curso=curso,
            matricula=matricula,
            data_doc=DATA_DOCUMENTO,
        )
    )

    # ------------------------------------------------------------------
    # Rodapé de página (canvas) — aplica-se a TODAS as páginas
    # ------------------------------------------------------------------
    def desenhar_rodape(canvas, doc_):
        canvas.saveState()
        largura, _ = A4
        canvas.setStrokeColor(CINZA_LINHA)
        canvas.setLineWidth(0.4)
        canvas.line(doc_.leftMargin, 18, largura - doc_.rightMargin, 18)

        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(CINZA_MEDIO)
        canvas.drawString(doc_.leftMargin, 9,
                          "Centro de Educação Profissional Escola Técnica de Planaltina")
        canvas.drawRightString(largura - doc_.rightMargin, 9, f"Página {doc_.page}")
        canvas.restoreState()

    # ------------------------------------------------------------------
    # Geração do PDF
    # ------------------------------------------------------------------
    doc.build(story, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)

    buffer.seek(0)
    return buffer.getvalue()






# -*- coding: utf-8 -*-
"""
Gerador da Matriz AFIN - CEP ETP (Modelo Tradicional P&B).

Características:
- A4 paisagem
- Estética tradicional: linhas finas, sem preenchimentos coloridos
- Preto sobre branco, com cinzas leves apenas para hierarquia
- 21 colunas acadêmicas por página
- Matrícula e Estudante repetidos em todas as páginas
- Cabeçalho institucional sóbrio com fio inferior forte
- Unidades Curriculares mescladas horizontalmente (pares FAL/CON)
- Inclusão do nome do Curso na seção de identificação
- Indicadores F/C diferenciados apenas por peso e filete
- Cabeçalho da tabela repetido automaticamente
- Último bloco completado com colunas vazias para preservar geometria
- Rodapé minimalista com numeração
"""

import io
import re
from datetime import datetime

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, PageBreak,
)


# ============================================================
# CONFIGURAÇÕES GERAIS (constantes)
# ============================================================
COLUNAS_MATRIZ_POR_PAGINA = 21

MARGEM_ESQ = 12 * mm
MARGEM_DIR = 12 * mm
MARGEM_SUP = 12 * mm
MARGEM_INF = 12 * mm

LARGURA_MATRICULA = 24 * mm
LARGURA_ESTUDANTE = 52 * mm


# ============================================================
# PALETA — PRETO, BRANCO E CINZAS (sem preenchimento colorido)
# ============================================================
PRETO            = colors.HexColor("#000000")
CINZA_ESCURO     = colors.HexColor("#333333")
CINZA_MEDIO      = colors.HexColor("#666666")
CINZA_CLARO      = colors.HexColor("#999999")
CINZA_FIO        = colors.HexColor("#AAAAAA")
CINZA_FIO_SUAVE  = colors.HexColor("#CCCCCC")
BRANCO           = colors.white


# ============================================================
# REGEX PRÉ-COMPILADAS (ganho real em loops grandes)
# ============================================================
_RE_ESPACOS     = re.compile(r"\s+")
_RE_FAL         = re.compile(r"(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])")
_RE_CON         = re.compile(r"(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])")
_RE_SUFIXO_FC   = re.compile(r"\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$", re.I)

_INVALIDOS_TXT  = frozenset({"nan", "nat", "none"})


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================
def _texto(valor):
    """Converte qualquer valor em texto seguro para o PDF."""
    if valor is None:
        return ""
    # Evita chamar pd.isna em tipos que não suportam
    if isinstance(valor, float):
        if pd.isna(valor):
            return ""
    try:
        texto = str(valor).strip()
    except Exception:
        return ""
    return "" if texto.lower() in _INVALIDOS_TXT else texto


def _html(valor):
    """Escapa caracteres especiais para uso dentro de Paragraph."""
    return (
        _texto(valor)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _normalizar(valor):
    """Normalização usada para comparação de nomes de UCs."""
    return _RE_ESPACOS.sub(" ", _texto(valor).upper()).strip()


# ============================================================
# IDENTIFICAÇÃO DE COLUNAS
# ============================================================
def _tipo_coluna(nome):
    """Identifica FAL (Faltas) ou CON (Conceito)."""
    s = _normalizar(nome)
    if _RE_FAL.search(s):
        return "FAL"
    if _RE_CON.search(s):
        return "CON"
    return None


def _nome_uc(nome):
    """Remove o sufixo FAL/CON do nome da coluna."""
    return _RE_SUFIXO_FC.sub("", _texto(nome)).strip()


def _mapa_iduc(mapa):
    """Normaliza o mapa {iduc: nome_uc}."""
    if not mapa:
        return {}
    resultado = {}
    for iduc, nome in mapa.items():
        nome = _texto(nome)
        if nome:
            resultado[_normalizar(nome)] = _texto(iduc)
    return resultado


# ============================================================
# ESTILOS TIPOGRÁFICOS (criados UMA vez por processo)
# ============================================================
def _build_estilos():
    base = getSampleStyleSheet()

    def _p(name, parent, **kw):
        return ParagraphStyle(name, parent=parent, **kw)

    normal = base["Normal"]

    return {
        # --- Cabeçalho institucional ---
        "instituicao": _p("AFINInstituicao", normal,
                          fontName="Helvetica-Bold", fontSize=8, leading=9,
                          alignment=TA_CENTER, textColor=PRETO),
        "titulo": _p("AFINTitulo", normal,
                     fontName="Helvetica-Bold", fontSize=11, leading=12,
                     alignment=TA_CENTER, textColor=PRETO),
        "subtitulo": _p("AFINSubtitulo", normal,
                        fontName="Helvetica", fontSize=7.5, leading=8.5,
                        alignment=TA_CENTER, textColor=CINZA_ESCURO),
        # --- Identificação do curso/turma ---
        "label": _p("AFINLabel", normal,
                    fontName="Helvetica-Bold", fontSize=6, leading=6.5,
                    alignment=TA_LEFT, textColor=CINZA_MEDIO),
        "valor": _p("AFINValor", normal,
                    fontName="Helvetica-Bold", fontSize=8.5, leading=9,
                    alignment=TA_LEFT, textColor=PRETO),
        # --- Cabeçalho da matriz ---
        "matricula_header": _p("AFINMatriculaHeader", normal,
                               fontName="Helvetica-Bold", fontSize=5.8, leading=6.2,
                               alignment=TA_CENTER, textColor=PRETO),
        "estudante_header": _p("AFINEstudanteHeader", normal,
                               fontName="Helvetica-Bold", fontSize=5.8, leading=6.2,
                               alignment=TA_LEFT, textColor=PRETO),
        "uc": _p("AFINUC", normal,
                 fontName="Helvetica-Bold", fontSize=5.4, leading=5.8,
                 alignment=TA_CENTER, textColor=PRETO),
        "iduc": _p("AFINIDUC", normal,
                   fontName="Helvetica-Oblique", fontSize=4.6, leading=4.9,
                   alignment=TA_CENTER, textColor=CINZA_MEDIO),
        "indicador": _p("AFINIndicador", normal,
                        fontName="Helvetica-Bold", fontSize=5.5, leading=5.7,
                        alignment=TA_CENTER, textColor=PRETO),
        "indicador_vazio": _p("AFINIndicadorVazio", normal,
                              fontName="Helvetica", fontSize=5.5, leading=5.7,
                              alignment=TA_CENTER, textColor=CINZA_CLARO),
        # --- Corpo ---
        "matricula": _p("AFINMatricula", normal,
                        fontName="Courier", fontSize=6.2, leading=6.8,
                        alignment=TA_CENTER, textColor=PRETO),
        "nome": _p("AFINNome", normal,
                   fontName="Helvetica", fontSize=6.5, leading=7.1,
                   alignment=TA_LEFT, textColor=PRETO),
        "valor_celula": _p("AFINValorCelula", normal,
                           fontName="Helvetica", fontSize=6.3, leading=6.8,
                           alignment=TA_CENTER, textColor=PRETO),
    }


ST = _build_estilos()


# ============================================================
# DIVISÃO DOS BLOCOS
# ============================================================
def _blocos(colunas):
    """Divide as colunas acadêmicas em blocos de 21."""
    if not colunas:
        return [[None] * COLUNAS_MATRIZ_POR_PAGINA]
    saida = []
    for inicio in range(0, len(colunas), COLUNAS_MATRIZ_POR_PAGINA):
        bloco = list(colunas[inicio:inicio + COLUNAS_MATRIZ_POR_PAGINA])
        faltam = COLUNAS_MATRIZ_POR_PAGINA - len(bloco)
        if faltam > 0:
            bloco.extend([None] * faltam)
        saida.append(bloco)
    return saida


# ============================================================
# CABEÇALHO INSTITUCIONAL
# ============================================================
def _topo(largura):
    dados = [
        [Paragraph("SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL", ST["instituicao"])],
        [Paragraph("CEP – ESCOLA TÉCNICA DE PLANALTINA", ST["titulo"])],
        [Paragraph("AFIN — ACOMPANHAMENTO DA FREQUÊNCIA E CONCEITO", ST["subtitulo"])],
    ]
    tabela = Table(
        dados,
        colWidths=[largura],
        rowHeights=[4.5 * mm, 5.5 * mm, 4.0 * mm],
        hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, PRETO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, CINZA_FIO),
        ("LINEBELOW", (0, 1), (-1, 1), 0.4, CINZA_FIO),
        ("LINEBELOW", (0, 2), (-1, 2), 1.2, PRETO),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    return tabela


# ============================================================
# IDENTIFICAÇÃO DA TURMA E CURSO
# ============================================================
def _identificacao(largura, curso, turma, semestre):
    larg_curso_lbl, larg_curso_val = 14 * mm, (largura * 0.45) - 14 * mm
    larg_turma_lbl, larg_turma_val = 14 * mm, (largura * 0.30) - 14 * mm
    larg_sem_lbl,   larg_sem_val   = 18 * mm, (largura * 0.25) - 18 * mm

    dados = [[
        Paragraph("CURSO",   ST["label"]),
        Paragraph(_html(curso or "—"), ST["valor"]),
        Paragraph("TURMA",   ST["label"]),
        Paragraph(_html(turma), ST["valor"]),
        Paragraph("SEMESTRE", ST["label"]),
        Paragraph(_html(semestre), ST["valor"]),
    ]]
    larguras = [
        larg_curso_lbl, larg_curso_val,
        larg_turma_lbl, larg_turma_val,
        larg_sem_lbl,   larg_sem_val,
    ]
    tabela = Table(dados, colWidths=larguras, rowHeights=[7 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING",   (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, CINZA_ESCURO),
        ("LINEAFTER", (1, 0), (1, 0), 0.4, CINZA_FIO),
        ("LINEAFTER", (3, 0), (3, 0), 0.4, CINZA_FIO),
    ]))
    return tabela


# ============================================================
# CABEÇALHO DA MATRIZ
# ============================================================
def _cabecalho(bloco, mapa, wm, wn, wc):
    linha_uc        = [Paragraph("MATRÍCULA", ST["matricula_header"]),
                       Paragraph("ESTUDANTE", ST["estudante_header"])]
    linha_iduc      = [Paragraph("", ST["matricula_header"]),
                       Paragraph("", ST["estudante_header"])]
    linha_indicador = [Paragraph("", ST["matricula_header"]),
                       Paragraph("", ST["estudante_header"])]

    larguras = [wm, wn]

    for nome_coluna in bloco:
        larguras.append(wc)
        if nome_coluna is None:
            linha_uc.append(Paragraph("", ST["uc"]))
            linha_iduc.append(Paragraph("", ST["iduc"]))
            linha_indicador.append(Paragraph("", ST["indicador_vazio"]))
            continue

        uc   = _nome_uc(nome_coluna)
        iduc = mapa.get(_normalizar(uc), "")
        tipo = _tipo_coluna(nome_coluna)

        linha_uc.append(Paragraph(_html(uc), ST["uc"]))
        linha_iduc.append(Paragraph(_html(iduc), ST["iduc"]))

        if tipo == "FAL":
            linha_indicador.append(Paragraph("F", ST["indicador"]))
        elif tipo == "CON":
            linha_indicador.append(Paragraph("C", ST["indicador"]))
        else:
            linha_indicador.append(Paragraph("", ST["indicador_vazio"]))

    return [linha_uc, linha_iduc, linha_indicador], larguras


# ============================================================
# MESCLAGEM DE UCs (calculada uma única vez)
# ============================================================
def _spans_uc(bloco):
    """
    Retorna lista de tuplas (col_inicio, col_fim) para SPAN das UCs
    que aparecem em colunas consecutivas (ex.: FAL + CON).
    """
    spans = []
    idx = 0
    n = len(bloco)
    while idx < n:
        col_atual = bloco[idx]
        if col_atual is None:
            idx += 1
            continue

        uc_atual = _nome_uc(col_atual)
        span_len = 1
        while (idx + span_len) < n:
            col_prox = bloco[idx + span_len]
            if col_prox is not None and _nome_uc(col_prox) == uc_atual:
                span_len += 1
            else:
                break

        if span_len > 1:
            spans.append((2 + idx, 2 + idx + span_len - 1))

        idx += span_len
    return spans


# ============================================================
# TABELA PRINCIPAL
# ============================================================
def _tabela(df, bloco, mapa, wm, wn, wc):
    cabecalho, larguras = _cabecalho(bloco, mapa, wm, wn, wc)
    posicoes = {coluna: i for i, coluna in enumerate(df.columns)}
    linhas = list(cabecalho)

    # Pré-computa colunas válidas (evita checagem `if coluna is None` por linha)
    bloco_validos = [c for c in bloco]  # preserva ordem/None

    for _, row in df.iterrows():
        linha = [
            Paragraph(_html(row.iloc[0]), ST["matricula"]),
            Paragraph(_html(row.iloc[1]), ST["nome"]),
        ]
        for coluna in bloco_validos:
            valor = "" if coluna is None else _texto(row.iloc[posicoes[coluna]])
            linha.append(Paragraph(_html(valor), ST["valor_celula"]))
        linhas.append(linha)

    tabela = Table(linhas, colWidths=larguras, repeatRows=3, hAlign="LEFT")

    n_linhas = len(linhas)

    comandos = [
        # Mesclagem vertical do cabeçalho
        ("SPAN", (0, 0), (0, 2)),
        ("SPAN", (1, 0), (1, 2)),

        # Fios do cabeçalho
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, PRETO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, CINZA_FIO),
        ("LINEBELOW", (0, 1), (-1, 1), 0.3, CINZA_FIO_SUAVE),
        ("LINEBELOW", (0, 2), (-1, 2), 1.0, PRETO),

        # Fios verticais estruturais (col 0 → Matrícula, col 1 → Estudante)
        ("LINEAFTER", (0, 0), (0, -1), 0.4, CINZA_FIO),
        ("LINEAFTER", (1, 0), (1, -1), 1.0, CINZA_ESCURO),

        # Alinhamento
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",  (1, 3), (1, -1), "LEFT"),

        # Padding
        ("TOPPADDING",   (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 1.2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 1.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.0),
    ]

    # SPANs das UCs mescladas (título + IDUC)
    for col_ini, col_fim in _spans_uc(bloco):
        comandos.append(("SPAN", (col_ini, 0), (col_fim, 0)))
        comandos.append(("SPAN", (col_ini, 1), (col_fim, 1)))

    # Divisória entre pares F/C
    for posicao, coluna in enumerate(bloco, start=2):
        if coluna is not None and _tipo_coluna(coluna) == "CON":
            comandos.append(("LINEAFTER", (posicao, 0), (posicao, -1), 0.5, CINZA_ESCURO))

    # Fios horizontais suaves entre linhas de dados
    comandos.extend(
        ("LINEBELOW", (0, i), (-1, i), 0.2, CINZA_FIO_SUAVE)
        for i in range(3, n_linhas)
    )

    # Fio inferior forte
    comandos.append(("LINEBELOW", (0, n_linhas - 1), (-1, n_linhas - 1), 1.0, PRETO))

    tabela.setStyle(TableStyle(comandos))
    return tabela


# ============================================================
# RODAPÉ
# ============================================================
def _rodape(canvas, doc):
    canvas.saveState()
    largura_pagina, _ = landscape(A4)
    y = 6.0 * mm

    canvas.setStrokeColor(CINZA_FIO)
    canvas.setLineWidth(0.3)
    canvas.line(MARGEM_ESQ, y + 3.0 * mm, largura_pagina - MARGEM_DIR, y + 3.0 * mm)

    canvas.setFont("Helvetica", 5.4)
    canvas.setFillColor(CINZA_MEDIO)
    canvas.drawString(MARGEM_ESQ, y, "CEP ETP • Matriz AFIN")

    data_geracao = datetime.now().strftime("%d/%m/%Y")
    canvas.drawCentredString(largura_pagina / 2, y, f"Gerado em {data_geracao}")
    canvas.drawRightString(largura_pagina - MARGEM_DIR, y, f"Página {doc.page}")

    canvas.setFont("Helvetica", 4.8)
    canvas.setFillColor(CINZA_CLARO)
    canvas.drawString(MARGEM_ESQ, y - 2.6 * mm, "F = Faltas   •   C = Conceito")

    canvas.restoreState()


# ============================================================
# PREPARAÇÃO DO DATAFRAME
# ============================================================
def _preparar_dataframe(df_matriz):
    if df_matriz is None:
        return pd.DataFrame()
    if not isinstance(df_matriz, pd.DataFrame):
        raise TypeError("df_matriz deve ser um pandas.DataFrame.")

    df = df_matriz.copy()
    if df.empty:
        return df

    if len(df.columns) < 2:
        raise ValueError("A matriz deve possuir pelo menos Matrícula e Estudante.")

    colunas = list(df.columns)
    if not _texto(colunas[0]):
        colunas[0] = "Matrícula"
    if not _texto(colunas[1]):
        colunas[1] = "Estudante"
    df.columns = colunas
    return df


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def gerar_pdf_afin(df_matriz, turma, semestre, curso="", mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN (modelo tradicional P&B)."""
    df = _preparar_dataframe(df_matriz)
    buffer = io.BytesIO()
    pagina = landscape(A4)
    largura_pagina, _ = pagina
    largura_util = largura_pagina - MARGEM_ESQ - MARGEM_DIR

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagina,
        leftMargin=MARGEM_ESQ,
        rightMargin=MARGEM_DIR,
        topMargin=MARGEM_SUP,
        bottomMargin=MARGEM_INF,
        title="Matriz AFIN",
        author="CEP ETP — Escola Técnica de Planaltina",
        subject="Acompanhamento da Frequência e Conceito",
        creator="CEP ETP",
    )

    mapa = _mapa_iduc(mapa_nomes_iduc)
    colunas = [] if df.empty else list(df.columns[2:])
    blocos = _blocos(colunas)

    largura_restante = largura_util - LARGURA_MATRICULA - LARGURA_ESTUDANTE
    largura_coluna = largura_restante / COLUNAS_MATRIZ_POR_PAGINA

    story = []

    for numero_bloco, bloco in enumerate(blocos, start=1):
        if numero_bloco > 1:
            story.append(PageBreak())

        story.append(_topo(largura_util))
        story.append(Spacer(1, 2.0 * mm))
        story.append(_identificacao(largura_util, curso, turma, semestre))
        story.append(Spacer(1, 2.0 * mm))

        if df.empty:
            tabela_vazia = Table(
                [[Paragraph("Nenhum registro disponível.", ST["nome"])]],
                colWidths=[largura_util],
            )
            tabela_vazia.setStyle(TableStyle([
                ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",   (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
                ("LINEABOVE", (0, 0), (-1, 0), 0.8, PRETO),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, PRETO),
            ]))
            story.append(tabela_vazia)
        else:
            story.append(
                _tabela(df, bloco, mapa,
                        LARGURA_MATRICULA, LARGURA_ESTUDANTE,
                        largura_coluna)
            )

    doc.build(story, onFirstPage=_rodape, onLaterPages=_rodape)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_relatorio_turma(dados):
    """Função auxiliar mantida para compatibilidade com relatórios da turma."""
    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n% Relatorio da Turma em desenvolvimento\n")
    buffer.seek(0)
    return buffer.getvalue()






from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Table, TableStyle


def gerar_pdf_declaracao_escolaridade(dados_aluno):
    """Gera o PDF da Declaração de Escolaridade em conformidade com o layout oficial."""
    
    def get_dado(dados, *chaves):
        if not isinstance(dados, dict):
            return ""
        for chave in chaves:
            if chave in dados and dados[chave] is not None:
                val = str(dados[chave]).strip()
                if val and val.lower() != "none":
                    return val
            target = chave.lower().replace(" ", "_").replace(":", "")
            for k, v in dados.items():
                k_clean = k.lower().replace(" ", "_").replace(":", "")
                if k_clean == target:
                    if v is not None:
                        val = str(v).strip()
                        if val and val.lower() != "none":
                            return val
        return ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    styles = getSampleStyleSheet()

    # Estilos de Texto
    style_header_title = ParagraphStyle(
        "HeaderTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        alignment=1,
        leading=12,
    )
    style_header_sub = ParagraphStyle(
        "HeaderSub", fontName="Helvetica", fontSize=8, alignment=1, leading=10
    )
    style_doc_title = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        alignment=1,
        leading=13,
    )

    style_label = ParagraphStyle(
        "Label",
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#333333"),
    )
    style_val = ParagraphStyle(
        "Val", fontName="Helvetica", fontSize=8, leading=10
    )
    style_obs = ParagraphStyle(
        "ObsText", fontName="Helvetica", fontSize=8, leading=12
    )

    PAGE_WIDTH = 523  # Largura útil da página (595 - 72)

    # -------------------------------------------------------------------------
    # 1. CABEÇALHO INSTITUCIONAL COM LOGOS
    # -------------------------------------------------------------------------
    try:
        img_gdf = Image("logo_gdf.png", width=50, height=50)
    except Exception:
        img_gdf = Paragraph("", styles["Normal"])

    try:
        img_escola = Image("logo_escola.png", width=50, height=50)
    except Exception:
        img_escola = Paragraph("", styles["Normal"])

    header_text = [
        Paragraph("<b>Governo do Distrito Federal</b>", style_header_title),
        Paragraph("Secretaria de Estado de Educação", style_header_sub),
        Paragraph("Subsecretaria de Educação Básica", style_header_sub),
        Paragraph(
            "Coordenação Regional de Ensino de Planaltina", style_header_sub
        ),
        Paragraph(
            "<b>Centro de Educação Profissional - Escola Técnica de Planaltina</b>",
            style_header_sub,
        ),
    ]

    tabela_cabecalho = Table(
        [[img_gdf, header_text, img_escola]],
        colWidths=[60, PAGE_WIDTH - 120, 60],
    )
    tabela_cabecalho.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(tabela_cabecalho)

    # Título do Documento
    tabela_titulo = Table(
        [[Paragraph("DECLARAÇÃO DE ESCOLARIDADE", style_doc_title)]],
        colWidths=[PAGE_WIDTH],
    )
    tabela_titulo.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ])
    )
    story.append(tabela_titulo)

    # -------------------------------------------------------------------------
    # 2. GRADE DE DADOS DO ALUNO
    # -------------------------------------------------------------------------
    def celula(rotulo, valor):
        v = str(valor) if valor and str(valor).lower() != "none" else ""
        return [
            Paragraph(rotulo, style_label),
            Paragraph(f"<b>{v}</b>", style_val),
        ]

    curso = get_dado(dados_aluno, "curso")
    matricula = get_dado(dados_aluno, "matricula", "matricula_aluno")
    turma = get_dado(dados_aluno, "turma", "turma_turno")
    nome = get_dado(dados_aluno, "nome", "nome_aluno")
    sexo = get_dado(dados_aluno, "sexo")
    data_nascimento = get_dado(dados_aluno, "data_nascimento", "dt_nascimento", "dt nascimento")
    nacionalidade = get_dado(dados_aluno, "nacionalidade") or "BRASILEIRA"
    naturalidade = get_dado(dados_aluno, "naturalidade", "cidade")
    uf = get_dado(dados_aluno, "uf", "uf_endereco") or "DF"
    rg = get_dado(dados_aluno, "rg", "identidade")
    
    # Captura correta para Órgão Expedidor e Data de Expedição com base nas chaves da imagem
    orgao_expeditor = get_dado(dados_aluno, "org_expedidor", "orgao_expeditor", "orgao_exp")
    data_expedicao = get_dado(dados_aluno, "dta_expedicao", "data_expedicao", "data_exp")
    
    cpf = get_dado(dados_aluno, "cpf")
    nome_mae = get_dado(dados_aluno, "nome_mae", "nome_da_mae", "nome da mae", "mae")
    
    # Tratamento para o nome do pai
    raw_pai = get_dado(dados_aluno, "nome_pai", "nome_do_pai", "nome do pai", "pai", "nome do responsavel")
    ignorar_pai = ["não sei", "nao sei", "não informado", "nao informado", "não", "nao", "-"]
    if raw_pai.lower() in ignorar_pai:
        nome_pai = ""
    else:
        nome_pai = raw_pai

    endereco_completo = get_dado(dados_aluno, "endereco")
    bairro = get_dado(dados_aluno, "bairro")
    endereco_final = f"{endereco_completo} {bairro}".strip()
    cep = get_dado(dados_aluno, "cep")

    dados_grid = [
        # Linha 1: Curso
        [
            celula("Curso:", curso),
            "", "", "", "", "", "", "",
        ],
        # Linha 2: Matrícula / Turma / Nome / Sexo
        [
            celula("Matrícula:", matricula),
            "",
            celula("Turma/Turno:", turma),
            "",
            celula("Nome:", nome),
            "", "",
            celula("Sexo:", sexo),
        ],
        # Linha 3: Dt Nasc / Nacionalidade / Naturalidade / UF / RG / Org.Exp / Dt.Exp
        [
            celula("Data de Nascimento:", data_nascimento),
            celula("Nacionalidade:", nacionalidade),
            celula("Naturalidade:", naturalidade),
            celula("UF:", uf),
            celula("Identidade:", rg),
            celula("Órg. Exp.:", orgao_expeditor),
            celula("Data de Expedição:", data_expedicao),
            "",
        ],
        # Linha 4: CPF / Filiação (Mãe)
        [
            celula("CPF:", cpf),
            "",
            celula("Nome da Mãe:", nome_mae),
            "", "", "", "", "",
        ],
        # Linha 5: Filiação (Pai)
        [
            "",
            "",
            celula("Nome do Pai:", nome_pai),
            "", "", "", "", "",
        ],
        # Linha 6: Endereço
        [
            celula("Endereço:", endereco_final),
            "", "", "",
            celula("CEP:", cep),
            "",
            celula("UF:", uf),
            "",
        ],
    ]

    # Distribuição refinada das larguras das colunas da linha 3 (Identidade, Órg. Exp., Data de Expedição)
    col_widths = [75, 75, 70, 35, 95, 55, 64, 54]
    tabela_dados = Table(dados_grid, colWidths=col_widths)
    tabela_dados.setStyle(
        TableStyle([
            # Spans
            ("SPAN", (0, 0), (7, 0)),  # Curso
            ("SPAN", (0, 1), (1, 1)),  # Matrícula
            ("SPAN", (2, 1), (3, 1)),  # Turma
            ("SPAN", (4, 1), (6, 1)),  # Nome
            ("SPAN", (2, 3), (7, 3)),  # Mãe
            ("SPAN", (2, 4), (7, 4)),  # Pai
            ("SPAN", (0, 5), (3, 5)),  # Endereço
            ("SPAN", (4, 5), (5, 5)),  # CEP
            ("SPAN", (6, 5), (7, 5)),  # UF
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(tabela_dados)

    # -------------------------------------------------------------------------
    # 3. BLOCO DE OBSERVAÇÕES E HORÁRIOS
    # -------------------------------------------------------------------------
    obs_content = [
        Paragraph("<b>Observações:</b>", style_label),
        Paragraph(
            "• <b>Turno Matutino:</b> Aulas de 08h00min às 12h00min, de segunda-feira a sexta-feira.",
            style_obs,
        ),
        Paragraph(
            "• <b>Turno Vespertino:</b> Aulas de 13h30min às 17h30min, de segunda-feira a sexta-feira.",
            style_obs,
        ),
        Paragraph(
            "• <b>Turno Noturno:</b> Aulas de 19h00min às 23h00min, de segunda-feira a sexta-feira.",
            style_obs,
        ),
        Paragraph(
            "• Declaração válida somente sem emendas e sem rasuras por 30 dias.",
            style_obs,
        ),
        Paragraph(
            "• <b>Observação: O(a) aluno(a) está regularmente matriculado(a) nesta Instituição de Ensino.</b>",
            style_obs,
        ),
    ]

    tabela_obs = Table([[obs_content]], colWidths=[PAGE_WIDTH])
    tabela_obs.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 120),  # Espaço vertical central
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(tabela_obs)

    # -------------------------------------------------------------------------
    # 4. RODAPÉ DE DATAS E ASSINATURA
    # -------------------------------------------------------------------------
    data_atual = datetime.now().strftime("%d/%m/%Y")
    rodape_grid = [
        [
            Paragraph(
                f"<b>PLANALTINA-DF, {data_atual}</b>", style_obs
            ),
            "",
        ],
        [
            Paragraph(
                "_____________________________________________________<br/><b>Secretaria Escolar</b>",
                ParagraphStyle("Sig", fontName="Helvetica", fontSize=8, alignment=1),
            ),
            "",
        ],
    ]

    tabela_rodape = Table(rodape_grid, colWidths=[PAGE_WIDTH / 2, PAGE_WIDTH / 2])
    tabela_rodape.setStyle(
        TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(tabela_rodape)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()




from datetime import datetime
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Table, TableStyle


def gerar_pdf_passe_estudantil(dados_aluno):
    """Gera o PDF da Declaração para Obtenção de Passe Estudantil em conformidade com o layout oficial."""
    
    def get_dado(dados, *chaves):
        if not isinstance(dados, dict):
            return ""
        for chave in chaves:
            if chave in dados and dados[chave] is not None:
                val = str(dados[chave]).strip()
                if val and val.lower() != "none":
                    return val
            target = chave.lower().replace(" ", "_").replace(":", "")
            for k, v in dados.items():
                k_clean = k.lower().replace(" ", "_").replace(":", "")
                if k_clean == target:
                    if v is not None:
                        val = str(v).strip()
                        if val and val.lower() != "none":
                            return val
        return ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    styles = getSampleStyleSheet()

    # Estilos de Texto
    style_header_title = ParagraphStyle(
        "HeaderTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        alignment=1,
        leading=12,
    )
    style_header_sub = ParagraphStyle(
        "HeaderSub", fontName="Helvetica", fontSize=8, alignment=1, leading=10
    )
    style_doc_title = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        alignment=1,
        leading=13,
    )

    style_label = ParagraphStyle(
        "Label",
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#333333"),
    )
    style_val = ParagraphStyle(
        "Val", fontName="Helvetica", fontSize=8, leading=10
    )
    style_obs = ParagraphStyle(
        "ObsText", fontName="Helvetica", fontSize=8, leading=12
    )

    PAGE_WIDTH = 523  # Largura útil da página (595 - 72)

    # -------------------------------------------------------------------------
    # 1. CABEÇALHO INSTITUCIONAL COM LOGOS
    # -------------------------------------------------------------------------
    try:
        img_gdf = Image("logo_gdf.png", width=50, height=50)
    except Exception:
        img_gdf = Paragraph("", styles["Normal"])

    try:
        img_escola = Image("logo_escola.png", width=50, height=50)
    except Exception:
        img_escola = Paragraph("", styles["Normal"])

    header_text = [
        Paragraph("<b>Governo do Distrito Federal</b>", style_header_title),
        Paragraph("Secretaria de Estado de Educação", style_header_sub),
        Paragraph("Subsecretaria de Educação Básica", style_header_sub),
        Paragraph(
            "Centro de Educação Profissional Escola Técnica de Planaltina", style_header_sub
        ),
    ]

    tabela_cabecalho = Table(
        [[img_gdf, header_text, img_escola]],
        colWidths=[60, PAGE_WIDTH - 120, 60],
    )
    tabela_cabecalho.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(tabela_cabecalho)

    # Título do Documento
    tabela_titulo = Table(
        [[Paragraph("DECLARAÇÃO PARA OBTENÇÃO DE PASSE ESTUDANTIL", style_doc_title)]],
        colWidths=[PAGE_WIDTH],
    )
    tabela_titulo.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ])
    )
    story.append(tabela_titulo)

    # -------------------------------------------------------------------------
    # 2. GRADE DE DADOS DO ALUNO (PASSE ESTUDANTIL)
    # -------------------------------------------------------------------------
    def celula(rotulo, valor):
        v = str(valor) if valor and str(valor).lower() != "none" else ""
        return [
            Paragraph(rotulo, style_label),
            Paragraph(f"<b>{v}</b>", style_val),
        ]

    curso = get_dado(dados_aluno, "curso")
    matricula = get_dado(dados_aluno, "matricula", "matricula_aluno")
    turma = get_dado(dados_aluno, "turma", "turma_turno")
    nome = get_dado(dados_aluno, "nome", "nome_aluno")
    sexo = get_dado(dados_aluno, "sexo")
    data_nascimento = get_dado(dados_aluno, "data_nascimento", "dt_nascimento", "dt nascimento")
    nacionalidade = get_dado(dados_aluno, "nacionalidade") or "BRASILEIRA"
    naturalidade = get_dado(dados_aluno, "naturalidade", "cidade")
    uf = get_dado(dados_aluno, "uf", "uf_endereco") or "DF"
    rg = get_dado(dados_aluno, "rg", "identidade")
    orgao_expeditor = get_dado(dados_aluno, "org_expedidor", "orgao_expeditor", "orgao_exp")
    data_expedicao = get_dado(dados_aluno, "dta_expedicao", "data_expedicao", "data_exp")
    cpf = get_dado(dados_aluno, "cpf")
    nome_mae = get_dado(dados_aluno, "nome_mae", "nome_da_mae", "nome da mae", "mae")
    
    raw_pai = get_dado(dados_aluno, "nome_pai", "nome_do_pai", "nome do pai", "pai")
    ignorar_pai = ["não sei", "nao sei", "não informado", "nao informado", "não", "nao", "-"]
    nome_pai = "" if raw_pai.lower() in ignorar_pai else raw_pai

    nome_responsavel = get_dado(dados_aluno, "nome_responsavel", "nome do responsavel")
    
    endereco = get_dado(dados_aluno, "endereco")
    bairro = get_dado(dados_aluno, "bairro")
    cidade = get_dado(dados_aluno, "cidade") or "PLANALTINA"
    uf_federacao = get_dado(dados_aluno, "uf_federacao", "uf") or "DF"
    cep = get_dado(dados_aluno, "cep")

    dados_grid = [
        # Linha 0: Curso
        [celula("Curso:", curso), "", "", "", "", "", "", ""],
        # Linha 1: Matrícula / Turma / Nome / Sexo
        [celula("Matrícula:", matricula), "", celula("Turma/ Turno:", turma), "", celula("Nome:", nome), "", "", celula("Sexo:", sexo)],
        # Linha 2: Dt Nasc / Nacionalidade / Naturalidade / UF / Identidade / Org. Exp. / Dt. Expedição
        [celula("Data de Nascimento:", data_nascimento), celula("Nacionalidade:", nacionalidade), celula("Naturalidade:", naturalidade), celula("UF:", uf), celula("Identidade:", rg), celula("Org. Exp.:", orgao_expeditor), celula("Data de Expedição:", data_expedicao), ""],
        # Linha 3: CPF / Nome da Mãe
        [celula("CPF:", cpf), "", celula("Nome da Mãe:", nome_mae), "", "", "", "", ""],
        # Linha 4: Nome do Pai
        [celula("", ""), "", celula("Nome do Pai:", nome_pai), "", "", "", "", ""],
        # Linha 5: Nome do Responsável
        [celula("", ""), "", celula("Nome do Responsável:", nome_responsavel), "", "", "", "", ""],
        # Linha 6: Endereço / Bairro
        [celula("Endereço:", endereco), "", "", "", celula("Bairro:", bairro), "", "", ""],
        # Linha 7: Cidade / Unidade da Federação / CEP
        [celula("Cidade:", cidade), "", celula("Unidade da Federação:", uf_federacao), "", "", celula("CEP:", cep), "", ""]
    ]

    col_widths = [75, 75, 70, 35, 95, 55, 64, 54]
    tabela_dados = Table(dados_grid, colWidths=col_widths)
    tabela_dados.setStyle(
        TableStyle([
            ("SPAN", (0, 0), (7, 0)),  # Curso
            ("SPAN", (0, 1), (1, 1)),  # Matrícula
            ("SPAN", (2, 1), (3, 1)),  # Turma/Turno
            ("SPAN", (4, 1), (6, 1)),  # Nome
            ("SPAN", (2, 3), (7, 3)),  # Nome da Mãe
            ("SPAN", (2, 4), (7, 4)),  # Nome do Pai
            ("SPAN", (2, 5), (7, 5)),  # Nome do Responsável
            ("SPAN", (0, 6), (3, 6)),  # Endereço
            ("SPAN", (4, 6), (7, 6)),  # Bairro
            ("SPAN", (0, 7), (1, 7)),  # Cidade
            ("SPAN", (2, 7), (4, 7)),  # UF
            ("SPAN", (5, 7), (7, 7)),  # CEP
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(tabela_dados)

    # -------------------------------------------------------------------------
    # 3. BLOCO DE OBSERVAÇÕES E DATAS DO SEMESTRE
    # -------------------------------------------------------------------------
    obs_content = [
        Paragraph("<b>Observações:</b>", style_label),
        Paragraph("• Turno Matutino: Aulas de 8h00min às 12h00min, de segunda-feira a sexta-feira.", style_obs),
        Paragraph("• Turno Vespertino: Aulas de 13h30min às 17h30min, de segunda-feira a sexta-feira.", style_obs),
        Paragraph("• Turno Noturno: Aulas de 19h00min às 23h00min, de segunda-feira a sexta-feira.", style_obs),
        Paragraph("• Declaração válida somente sem emendas e sem rasuras por 30 dias.", style_obs),
        Paragraph("• Início do 1º Semestre Letivo: 12/02/2026 – Término: 10/07/2026.", style_obs),
        Paragraph("• Início do 2º Semestre Letivo: 28/07/2026 – Término: 22/12/2026.", style_obs),
        Paragraph("• <b>Observação: O(a) aluno(a) está regularmente matriculado(a) nesta Instituição de Ensino.</b>", style_obs),
    ]

    tabela_obs = Table([[obs_content]], colWidths=[PAGE_WIDTH])
    tabela_obs.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 80),  # Espaço vertical central ajustado
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(tabela_obs)

    # -------------------------------------------------------------------------
    # 4. RODAPÉ DE DATAS E ASSINATURA
    # -------------------------------------------------------------------------
    data_atual = datetime.now().strftime("%d/%m/%Y")
    rodape_grid = [
        [
            Paragraph(f"<b>PLANALTINA-DF,</b> {data_atual}", style_obs),
            "",
        ],
        [
            Paragraph(
                "_____________________________________________________<br/><b>Secretário(a) Escolar</b>",
                ParagraphStyle("Sig", fontName="Helvetica", fontSize=8, alignment=1),
            ),
            "",
        ],
    ]

    tabela_rodape = Table(rodape_grid, colWidths=[PAGE_WIDTH / 2, PAGE_WIDTH / 2])
    tabela_rodape.setStyle(
        TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 1), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(tabela_rodape)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()



import io
import pypdf  # Biblioteca responsável por juntar os PDFs

# ... (as suas outras funções de geração de PDF individuais, como gerar_pdf_passe_estudantil)

def gerar_pdf_passes_turma_unificado(df_turma_alunos):
    """
    Gera um único documento PDF consolidado contendo o passe estudantil 
    de todos os alunos da turma, um após o outro.
    """
    merger = pypdf.PdfMerger()
    
    for _, aluno in df_turma_alunos.iterrows():
        dados_dict = aluno.to_dict()
        
        # 1. Gera o PDF individual do aluno em formato de bytes
        pdf_bytes = gerar_pdf_passe_estudantil(dados_dict)
        
        # 2. Converte os bytes para um objeto de leitura em memória e adiciona ao unificador
        pdf_file_like = io.BytesIO(pdf_bytes)
        merger.append(pdf_file_like)
        
    # 3. Consolida todas as páginas num único buffer final
    output_buffer = io.BytesIO()
    merger.write(output_buffer)
    merger.close()
    
    output_buffer.seek(0)
    return output_buffer.getvalue()

