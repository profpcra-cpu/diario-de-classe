import io
import os
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from modulos.conexao import executar_query


def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """
    Gera o Histórico Escolar em A4, com diagramação institucional,
    alinhamento rigoroso de colunas (todas somando exatamente 554 pt)
    e limpeza de campos acadêmicos quando o semestre não estiver lançado.
    """

    # Compatibilidade com chamada invertida
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()

    # ------------------------------------------------------------------
    # CONFIGURAÇÃO DO DOCUMENTO (Largura útil exata: 554 pt)
    # A4 = 595.27 de largura. Margens de 28 pt à esquerda e direita.
    # ------------------------------------------------------------------
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=22,
        bottomMargin=24,
        title="Histórico Escolar",
        author="Centro de Educação Profissional Escola Técnica de Planaltina"
    )

    styles = getSampleStyleSheet()

    # ------------------------------------------------------------------
    # PALETA
    # ------------------------------------------------------------------
    CINZA_TEXTO = colors.HexColor("#263238")
    CINZA_MEDIO = colors.HexColor("#5F6B72")
    CINZA_LINHA = colors.HexColor("#C8CED2")
    CINZA_CAB = colors.HexColor("#E7EAEC")
    PRETO = colors.HexColor("#111111")

    # ------------------------------------------------------------------
    # ESTILOS
    # ------------------------------------------------------------------
    estilo_institucional = ParagraphStyle(
        "Institucional",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.3,
        leading=8.4,
        alignment=TA_CENTER,
        textColor=PRETO,
        spaceAfter=0,
        spaceBefore=0
    )

    estilo_institucional_bold = ParagraphStyle(
        "InstitucionalBold",
        parent=estilo_institucional,
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=8.7
    )

    estilo_titulo = ParagraphStyle(
        "TituloHistorico",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        alignment=TA_CENTER,
        textColor=PRETO,
        spaceBefore=5,
        spaceAfter=7
    )

    estilo_secao = ParagraphStyle(
        "Secao",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.4,
        leading=8.5,
        alignment=TA_LEFT,
        textColor=PRETO,
        spaceBefore=0,
        spaceAfter=0
    )

    estilo_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.2,
        leading=7,
        textColor=CINZA_MEDIO,
        spaceBefore=0,
        spaceAfter=0
    )

    estilo_valor = ParagraphStyle(
        "Valor",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=8.7,
        textColor=CINZA_TEXTO,
        spaceBefore=0,
        spaceAfter=0
    )

    estilo_valor_bold = ParagraphStyle(
        "ValorBold",
        parent=estilo_valor,
        fontName="Helvetica-Bold",
        textColor=PRETO
    )

    estilo_th = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.8,
        leading=7.6,
        alignment=TA_CENTER,
        textColor=PRETO
    )

    estilo_td = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.9,
        leading=7.7,
        alignment=TA_CENTER,
        textColor=CINZA_TEXTO
    )

    estilo_td_left = ParagraphStyle(
        "TDLeft",
        parent=estilo_td,
        alignment=TA_LEFT
    )

    estilo_rodape = ParagraphStyle(
        "Rodape",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=7.7,
        textColor=CINZA_MEDIO
    )

    estilo_assinatura = ParagraphStyle(
        "Assinatura",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8,
        alignment=TA_CENTER,
        textColor=PRETO
    )

    # ------------------------------------------------------------------
    # DADOS DO ALUNO
    # ------------------------------------------------------------------
    if isinstance(dados_aluno, dict):
        d = dados_aluno
    elif hasattr(dados_aluno, "iloc") and not dados_aluno.empty:
        d = dados_aluno.iloc[0].to_dict()
    else:
        d = {}

    def valor(*chaves, padrao=""):
        for chave in chaves:
            v = d.get(chave)
            if v is not None and str(v).strip() not in ("", "nan", "None"):
                return str(v).strip()
        return padrao

    curso = valor("curso", padrao="TÉCNICO EM ENFERMAGEM")
    matricula = valor("matricula", "matrícula")
    turma = valor("turma")
    sigla = valor("sigla")
    nome = valor("nome")
    cpf = valor("cpf")
    sexo = valor("sexo")
    mae = valor("mae", "nome_mae")
    pai = valor("pai", "nome_pai")
    dt_nasc = valor("data_nascimento")
    nacionalidade = valor("nacionalidade", padrao="Brasileira")
    naturalidade = valor("naturalidade")
    uf = valor("uf", padrao="DF")
    rg = valor("rg")
    orgao = valor("orgao_expeditor")
    dt_exp = valor("data_expedicao")

    # ------------------------------------------------------------------
    # BASE LEGAL
    # ------------------------------------------------------------------
    base_legal_texto = (
        "LEI Nº 9.394/96, DECRETO Nº 5.154/2004, "
        "RESOLUÇÃO Nº 02/2023 - CEDF"
    )

    if sigla and turma:
        try:
            df_bl = executar_query(
                """
                SELECT base_legal
                FROM TB_BASE_LEGAL
                WHERE sigla = %s AND turma = %s
                """,
                params=(sigla, turma)
            )

            if (
                not df_bl.empty
                and pd.notnull(df_bl.iloc[0]["base_legal"])
                and str(df_bl.iloc[0]["base_legal"]).strip()
            ):
                base_legal_texto = str(df_bl.iloc[0]["base_legal"]).strip()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # LOGOS E CABEÇALHO
    # ------------------------------------------------------------------
    path_logo_gdf = "logo_gdf.png"
    path_logo_escola = "logo_escola.png"

    img_gdf = (
        Image(path_logo_gdf, width=42, height=42)
        if os.path.exists(path_logo_gdf)
        else Paragraph("", estilo_valor)
    )

    img_escola = (
        Image(path_logo_escola, width=42, height=42)
        if os.path.exists(path_logo_escola)
        else Paragraph("", estilo_valor)
    )

    texto_institucional = [
        Paragraph("GOVERNO DO DISTRITO FEDERAL", estilo_institucional_bold),
        Paragraph("Secretaria de Estado de Educação", estilo_institucional),
        Paragraph("Subsecretaria de Educação Básica", estilo_institucional),
        Paragraph("Coordenação Regional de Ensino de Planaltina", estilo_institucional),
        Paragraph(
            "Centro de Educação Profissional Escola Técnica de Planaltina",
            estilo_institucional_bold
        ),
    ]

    cabecalho = Table(
        [[img_gdf, texto_institucional, img_escola]],
        colWidths=[52, 450, 52],
        rowHeights=[51],
        hAlign="LEFT"
    )

    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    # ------------------------------------------------------------------
    # FUNÇÕES AUXILIARES DE DIAGRAMAÇÃO
    # ------------------------------------------------------------------
    def bloco_secao(titulo):
        t = Table(
            [[Paragraph(titulo, estilo_secao)]],
            colWidths=[554],
            rowHeights=[17],
            hAlign="LEFT"
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CINZA_CAB),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, CINZA_LINHA),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    def tabela_campos(linhas, larguras):
        t = Table(linhas, colWidths=larguras, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, CINZA_LINHA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return t

    story = []

    # Cabeçalho e Título Principal
    story.append(cabecalho)
    story.append(Paragraph("HISTÓRICO ESCOLAR", estilo_titulo))

    # Identificação Acadêmica (Soma exata: 330 + 110 + 114 = 554 pt)
    story.append(bloco_secao("IDENTIFICAÇÃO ACADÊMICA"))
    identificacao = [
        [
            Paragraph("CURSO", estilo_label),
            Paragraph("MATRÍCULA", estilo_label),
            Paragraph("TURMA / TURNO", estilo_label),
        ],
        [
            Paragraph(curso, estilo_valor_bold),
            Paragraph(matricula or "—", estilo_valor),
            Paragraph(turma or "—", estilo_valor),
        ],
    ]
    story.append(tabela_campos(identificacao, [330, 110, 114]))
    story.append(Spacer(1, 4))

    # Dados do Estudante (Soma exata por linha: 300 + 120 + 134 = 554 pt)
    story.append(bloco_secao("DADOS DO ESTUDANTE"))
    dados_estudante = [
        [
            Paragraph("NOME", estilo_label),
            Paragraph("CPF", estilo_label),
            Paragraph("SEXO", estilo_label),
        ],
        [
            Paragraph(nome or "—", estilo_valor_bold),
            Paragraph(cpf or "—", estilo_valor),
            Paragraph(sexo or "—", estilo_valor),
        ],
        [
            Paragraph("NOME DA MÃE", estilo_label),
            Paragraph("NOME DO PAI", estilo_label),
            Paragraph("DATA DE NASCIMENTO", estilo_label),
        ],
        [
            Paragraph(mae or "—", estilo_valor),
            Paragraph(pai or "—", estilo_valor),
            Paragraph(dt_nasc or "—", estilo_valor),
        ],
        [
            Paragraph("NACIONALIDADE", estilo_label),
            Paragraph("NATURALIDADE / UF", estilo_label),
            Paragraph("RG / ÓRGÃO / DATA DE EXPEDIÇÃO", estilo_label),
        ],
        [
            Paragraph(nacionalidade or "—", estilo_valor),
            Paragraph(f"{naturalidade} / {uf}".strip(" /") or "—", estilo_valor),
            Paragraph(" ".join(x for x in [rg, orgao, dt_exp] if x) or "—", estilo_valor),
        ],
    ]
    story.append(tabela_campos(dados_estudante, [300, 120, 134]))
    story.append(Spacer(1, 4))

    # Base Legal (Soma exata: 554 pt)
    story.append(bloco_secao("BASE LEGAL"))
    base_legal = Table(
        [[Paragraph(base_legal_texto, estilo_valor)]],
        colWidths=[554],
        hAlign="LEFT"
    )
    base_legal.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(base_legal)
    story.append(Spacer(1, 5))

    # ------------------------------------------------------------------
    # HISTÓRICO ACADÊMICO (Soma exata: 314 + 40 + 30 + 65 + 45 + 60 = 554 pt)
    # ------------------------------------------------------------------
    header_hist = [
        Paragraph("COMPONENTE CURRICULAR", estilo_th),
        Paragraph("SEM.", estilo_th),
        Paragraph("CH", estilo_th),
        Paragraph("MÓDULO", estilo_th),
        Paragraph("FALTAS", estilo_th),
        Paragraph("RESULTADO", estilo_th),
    ]

    tabela_hist_dados = [header_hist]

    if df_historico is not None and not df_historico.empty:
        for _, row in df_historico.iterrows():
            comp = str(
                row.get(
                    "unidade_curricular",
                    row.get("componente", row.get("disciplina", "---"))
                )
            )
            
            # Verifica se o semestre foi lançado (Lógica aplicada)
            sem = str(row.get("semestre", "")).strip()
            
            if not sem or sem.lower() in ("none", "nan", ""):
                # Mantém os campos acadêmicos limpos se não houver semestre
                sem = ""
                ch = ""
                mod = ""
                faltas = ""
                res = ""
            else:
                ch = str(row.get("carga_horaria", row.get("ch", "")))
                mod = str(row.get("modulo", ""))
                faltas = str(row.get("faltas", "0"))
                res = str(row.get("resultado", row.get("conceito", "")))

            tabela_hist_dados.append([
                Paragraph(comp, estilo_td_left),
                Paragraph(sem, estilo_td),
                Paragraph(ch, estilo_td),
                Paragraph(mod, estilo_td),
                Paragraph(faltas, estilo_td),
                Paragraph(res, estilo_td),
            ])

    t_hist = Table(
        tabela_hist_dados,
        repeatRows=1,
        colWidths=[314, 40, 30, 65, 45, 60],
        hAlign="LEFT"
    )

    estilo_hist = [
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CAB),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, CINZA_LINHA),
        ("GRID", (0, 0), (-1, -1), 0.3, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]

    for i in range(1, len(tabela_hist_dados)):
        if i % 2 == 0:
            estilo_hist.append(
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFAFA"))
            )

    t_hist.setStyle(TableStyle(estilo_hist))
    story.append(t_hist)
    story.append(Spacer(1, 5))

    # ------------------------------------------------------------------
    # BLOCO FINAL (Legenda, Data e Assinaturas alinhados a 554 pt)
    # ------------------------------------------------------------------
    rodape_legenda = Table(
        [[
            Paragraph(
                "<b>Legenda:</b> AP = Apto; AE = Aproveitamento de Estudos; "
                "NA = Não Apto; TR = Trancamento de Curso; D = Desistente",
                estilo_rodape
            ),
            Paragraph("<b>T. Teoria:</b> 1.366 h", estilo_rodape),
            Paragraph("<b>T. Prática:</b> 0 h", estilo_rodape),
        ]],
        colWidths=[350, 102, 102],
        hAlign="LEFT"
    )

    rodape_legenda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F8F8")),
        ("BOX", (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    data_documento = "PLANALTINA-DF, 27 DE SETEMBRO DE 2026"
    data_tabela = Table(
        [[Paragraph(data_documento, estilo_assinatura)]],
        colWidths=[554],
        hAlign="LEFT"
    )
    data_tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    assinatura = Table(
        [[
            Paragraph(
                "____________________________________________<br/>"
                "<b>Diretor(a)</b>",
                estilo_assinatura
            ),
            Paragraph(
                "____________________________________________<br/>"
                "<b>Chefe de Secretaria Escolar</b>",
                estilo_assinatura
            ),
        ]],
        colWidths=[277, 277],
        rowHeights=[43],
        hAlign="LEFT"
    )

    assinatura.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    bloco_final = KeepTogether([
        rodape_legenda,
        Spacer(1, 9),
        data_tabela,
        Spacer(1, 23),
        assinatura
    ])

    story.append(bloco_final)

    # ------------------------------------------------------------------
    # RODAPÉ DE PÁGINA (CANVAS)
    # ------------------------------------------------------------------
    def desenhar_rodape(canvas, doc):
        canvas.saveState()
        largura, altura = A4

        canvas.setStrokeColor(CINZA_LINHA)
        canvas.setLineWidth(0.4)
        canvas.line(
            doc.leftMargin,
            18,
            largura - doc.rightMargin,
            18
        )

        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(CINZA_MEDIO)
        canvas.drawString(
            doc.leftMargin,
            9,
            "Centro de Educação Profissional Escola Técnica de Planaltina"
        )

        canvas.drawRightString(
            largura - doc.rightMargin,
            9,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    # GERAÇÃO
    doc.build(
        story,
        onFirstPage=desenhar_rodape,
        onLaterPages=desenhar_rodape
    )

    buffer.seek(0)
    return buffer.getvalue()


# -*- coding: utf-8 -*-
"""
Gerador profissional da Matriz AFIN - CEP ETP.

Características:
- A4 paisagem
- 21 colunas acadêmicas por página
- Matrícula e Estudante repetidos em todas as páginas
- Cabeçalho institucional minimalista
- Tipografia otimizada para impressão
- Baixa poluição visual
- Compatível com impressão colorida ou escala de cinza
- Quebra automática de nomes extensos de UCs
- Cabeçalho da tabela repetido automaticamente
- Último bloco completado com colunas vazias para preservar a geometria
"""

import io
import re

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

COLUNAS_MATRIZ_POR_PAGINA = 21

MARGEM_ESQ = 10 * mm
MARGEM_DIR = 10 * mm
MARGEM_SUP = 8 * mm
MARGEM_INF = 9 * mm

LARGURA_MATRICULA = 24 * mm
LARGURA_ESTUDANTE = 49 * mm


# ============================================================
# PALETA INSTITUCIONAL
# ============================================================
#
# A ideia aqui não é colorir a tabela.
# A cor é usada apenas para criar hierarquia no cabeçalho.
#

AZUL_INSTITUCIONAL = colors.HexColor("#173B63")
AZUL_SECUNDARIO = colors.HexColor("#315D82")

AZUL_MUITO_CLARO = colors.HexColor("#F2F6FA")

CINZA_TEXTO = colors.HexColor("#28343F")
CINZA_SECUNDARIO = colors.HexColor("#68737D")

CINZA_LINHA = colors.HexColor("#D7DDE3")
CINZA_LINHA_SUAVE = colors.HexColor("#E9EDF1")

CINZA_ZEBRA = colors.HexColor("#FAFBFC")

BRANCO = colors.white


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def _texto(valor):
    """
    Converte qualquer valor em texto seguro para o PDF.
    Valores nulos ficam vazios.
    """
    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    texto = str(valor).strip()

    if texto.lower() in {"nan", "nat", "none"}:
        return ""

    return texto


def _html(valor):
    """
    Escapa caracteres especiais para uso dentro de Paragraph.
    """
    return (
        _texto(valor)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _normalizar(valor):
    """
    Normalização usada para comparação de nomes de UCs.
    """
    return re.sub(
        r"\s+",
        " ",
        _texto(valor).upper()
    ).strip()


# ============================================================
# IDENTIFICAÇÃO DE COLUNAS
# ============================================================

def _tipo_coluna(nome):
    """
    Identifica se uma coluna representa:

    FAL = faltas
    CON = conceito
    None = outro tipo
    """

    s = _normalizar(nome)

    if re.search(
        r"(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])",
        s
    ):
        return "FAL"

    if re.search(
        r"(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])",
        s
    ):
        return "CON"

    return None


def _nome_uc(nome):
    """
    Remove o sufixo FAL/CON do nome da coluna.
    """

    return re.sub(
        r"\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$",
        "",
        _texto(nome),
        flags=re.I,
    ).strip()


def _mapa_iduc(mapa):
    """
    Normaliza o mapa {iduc: nome_uc}
    para facilitar a localização do IDUC.
    """

    if not mapa:
        return {}

    resultado = {}

    for iduc, nome in mapa.items():
        nome = _texto(nome)

        if not nome:
            continue

        resultado[_normalizar(nome)] = _texto(iduc)

    return resultado


# ============================================================
# ESTILOS TIPOGRÁFICOS
# ============================================================

def _estilos():
    """
    Centraliza toda a tipografia do documento.

    A intenção é evitar que o PDF fique com muitas fontes,
    pesos ou tamanhos diferentes.
    """

    base = getSampleStyleSheet()

    return {

        # ----------------------------------------------------
        # CABEÇALHO INSTITUCIONAL
        # ----------------------------------------------------

        "instituicao": ParagraphStyle(
            "AFINInstituicao",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=9.2,
            alignment=TA_CENTER,
            textColor=AZUL_INSTITUCIONAL,
            spaceAfter=0,
        ),

        "titulo": ParagraphStyle(
            "AFINTitulo",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=11,
            alignment=TA_CENTER,
            textColor=AZUL_INSTITUCIONAL,
            spaceAfter=0,
        ),

        "subtitulo": ParagraphStyle(
            "AFINSubtitulo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=7.2,
            alignment=TA_CENTER,
            textColor=CINZA_SECUNDARIO,
            spaceAfter=0,
        ),

        # ----------------------------------------------------
        # IDENTIFICAÇÃO
        # ----------------------------------------------------

        "label": ParagraphStyle(
            "AFINLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.9,
            leading=6.5,
            alignment=TA_LEFT,
            textColor=CINZA_SECUNDARIO,
        ),

        "valor": ParagraphStyle(
            "AFINValor",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=8.5,
            alignment=TA_LEFT,
            textColor=CINZA_TEXTO,
        ),

        # ----------------------------------------------------
        # CABEÇALHO DA MATRIZ
        # ----------------------------------------------------

        "matricula_header": ParagraphStyle(
            "AFINMatriculaHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.7,
            leading=6.2,
            alignment=TA_CENTER,
            textColor=BRANCO,
        ),

        "estudante_header": ParagraphStyle(
            "AFINEstudanteHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.7,
            leading=6.2,
            alignment=TA_LEFT,
            textColor=BRANCO,
        ),

        "uc": ParagraphStyle(
            "AFINUC",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.1,
            leading=5.5,
            alignment=TA_CENTER,
            textColor=AZUL_INSTITUCIONAL,
        ),

        "iduc": ParagraphStyle(
            "AFINIDUC",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=4.8,
            leading=5.1,
            alignment=TA_CENTER,
            textColor=CINZA_SECUNDARIO,
        ),

        "indicador": ParagraphStyle(
            "AFINIndicador",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5,
            leading=5.2,
            alignment=TA_CENTER,
            textColor=BRANCO,
        ),

        # ----------------------------------------------------
        # CORPO
        # ----------------------------------------------------

        "matricula": ParagraphStyle(
            "AFINMatricula",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.4,
            leading=7,
            alignment=TA_CENTER,
            textColor=CINZA_TEXTO,
        ),

        "nome": ParagraphStyle(
            "AFINNome",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.5,
            leading=7.1,
            alignment=TA_LEFT,
            textColor=CINZA_TEXTO,
        ),

        "valor_celula": ParagraphStyle(
            "AFINValorCelula",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.3,
            leading=6.8,
            alignment=TA_CENTER,
            textColor=CINZA_TEXTO,
        ),

        # ----------------------------------------------------
        # RODAPÉ
        # ----------------------------------------------------

        "rodape": ParagraphStyle(
            "AFINRodape",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=5.5,
            leading=6,
            alignment=TA_LEFT,
            textColor=CINZA_SECUNDARIO,
        ),
    }


# ============================================================
# DIVISÃO DOS BLOCOS
# ============================================================

def _blocos(colunas):
    """
    Divide as colunas acadêmicas em blocos de 21.

    O último bloco recebe colunas vazias quando necessário.
    Isso mantém a largura e a geometria visual de todas as páginas.
    """

    if not colunas:
        return [[None] * COLUNAS_MATRIZ_POR_PAGINA]

    saida = []

    for inicio in range(
        0,
        len(colunas),
        COLUNAS_MATRIZ_POR_PAGINA
    ):
        bloco = list(
            colunas[
                inicio:
                inicio + COLUNAS_MATRIZ_POR_PAGINA
            ]
        )

        quantidade_faltante = (
            COLUNAS_MATRIZ_POR_PAGINA - len(bloco)
        )

        if quantidade_faltante > 0:
            bloco.extend(
                [None] * quantidade_faltante
            )

        saida.append(bloco)

    return saida


# ============================================================
# CABEÇALHO INSTITUCIONAL
# ============================================================

def _topo(largura, st):
    """
    Cabeçalho institucional minimalista.

    Não utiliza uma grande caixa colorida.
    """

    largura_linha = largura

    dados = [
        [
            Paragraph(
                "SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL",
                st["instituicao"],
            )
        ],
        [
            Paragraph(
                "CEP – ESCOLA TÉCNICA DE PLANALTINA",
                st["titulo"],
            )
        ],
        [
            Paragraph(
                "AFIN — ACOMPANHAMENTO DA FREQUÊNCIA E CONCEITO",
                st["subtitulo"],
            )
        ],
    ]

    tabela = Table(
        dados,
        colWidths=[largura_linha],
        rowHeights=[
            4.2 * mm,
            4.8 * mm,
            3.8 * mm,
        ],
        hAlign="LEFT",
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    BRANCO,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),

                (
                    "LINEBELOW",
                    (0, 2),
                    (-1, 2),
                    0.8,
                    AZUL_INSTITUCIONAL,
                ),
            ]
        )
    )

    return tabela


# ============================================================
# IDENTIFICAÇÃO DA TURMA
# ============================================================

def _identificacao(largura, turma, semestre, st):
    """
    Identificação compacta da turma e semestre.
    """

    metade = largura / 2

    dados = [
        [
            Paragraph("TURMA", st["label"]),
            Paragraph(_html(turma), st["valor"]),
            Paragraph("SEMESTRE", st["label"]),
            Paragraph(_html(semestre), st["valor"]),
        ]
    ]

    larguras = [
        15 * mm,
        metade - 15 * mm,
        20 * mm,
        metade - 20 * mm,
    ]

    tabela = Table(
        dados,
        colWidths=larguras,
        rowHeights=[7 * mm],
        hAlign="LEFT",
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    AZUL_MUITO_CLARO,
                ),

                (
                    "BACKGROUND",
                    (2, 0),
                    (2, 0),
                    AZUL_MUITO_CLARO,
                ),

                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 0),
                    0.4,
                    CINZA_LINHA,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2.5,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0.5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0.5,
                ),
            ]
        )
    )

    return tabela


# ============================================================
# CABEÇALHO DA MATRIZ
# ============================================================

def _cabecalho(
    bloco,
    mapa,
    wm,
    wn,
    wc,
    st,
):
    """
    Constrói as três linhas do cabeçalho:

    Linha 1 = UC
    Linha 2 = IDUC
    Linha 3 = F/C
    """

    linha_uc = [
        Paragraph(
            "MATRÍCULA",
            st["matricula_header"],
        ),
        Paragraph(
            "ESTUDANTE",
            st["estudante_header"],
        ),
    ]

    linha_iduc = [
        Paragraph("", st["matricula_header"]),
        Paragraph("", st["estudante_header"]),
    ]

    linha_indicador = [
        Paragraph("", st["matricula_header"]),
        Paragraph("", st["estudante_header"]),
    ]

    larguras = [
        wm,
        wn,
    ]

    for nome_coluna in bloco:

        larguras.append(wc)

        if nome_coluna is None:

            linha_uc.append(
                Paragraph("", st["uc"])
            )

            linha_iduc.append(
                Paragraph("", st["iduc"])
            )

            linha_indicador.append(
                Paragraph("", st["indicador"])
            )

            continue

        uc = _nome_uc(nome_coluna)

        iduc = mapa.get(
            _normalizar(uc),
            "",
        )

        tipo = _tipo_coluna(
            nome_coluna
        )

        linha_uc.append(
            Paragraph(
                _html(uc),
                st["uc"],
            )
        )

        linha_iduc.append(
            Paragraph(
                _html(iduc),
                st["iduc"],
            )
        )

        indicador = ""

        if tipo == "FAL":
            indicador = "F"

        elif tipo == "CON":
            indicador = "C"

        linha_indicador.append(
            Paragraph(
                indicador,
                st["indicador"],
            )
        )

    return [
        linha_uc,
        linha_iduc,
        linha_indicador,
    ], larguras


# ============================================================
# TABELA PRINCIPAL
# ============================================================

def _tabela(
    df,
    bloco,
    mapa,
    wm,
    wn,
    wc,
    st,
):
    """
    Constrói a tabela acadêmica.

    A estratégia visual é:
    - cabeçalho forte;
    - corpo branco;
    - zebra extremamente discreta;
    - poucas linhas;
    - ausência de grades verticais excessivas.
    """

    cabecalho, larguras = _cabecalho(
        bloco,
        mapa,
        wm,
        wn,
        wc,
        st,
    )

    posicoes = {
        coluna: indice
        for indice, coluna
        in enumerate(df.columns)
    }

    linhas = list(cabecalho)

    # --------------------------------------------------------
    # CORPO
    # --------------------------------------------------------

    for _, row in df.iterrows():

        linha = [
            Paragraph(
                _html(row.iloc[0]),
                st["matricula"],
            ),

            Paragraph(
                _html(row.iloc[1]),
                st["nome"],
            ),
        ]

        for coluna in bloco:

            if coluna is None:
                valor = ""

            else:
                valor = _texto(
                    row.iloc[
                        posicoes[coluna]
                    ]
                )

            linha.append(
                Paragraph(
                    _html(valor),
                    st["valor_celula"],
                )
            )

        linhas.append(linha)

    tabela = Table(
        linhas,
        colWidths=larguras,
        repeatRows=3,
        hAlign="LEFT",
    )

    comandos = [

        # ----------------------------------------------------
        # CABEÇALHO — MATRÍCULA / ESTUDANTE
        # ----------------------------------------------------

        (
            "BACKGROUND",
            (0, 0),
            (1, 2),
            AZUL_INSTITUCIONAL,
        ),

        # ----------------------------------------------------
        # CABEÇALHO — UCs
        # ----------------------------------------------------

        (
            "BACKGROUND",
            (2, 0),
            (-1, 0),
            AZUL_MUITO_CLARO,
        ),

        (
            "BACKGROUND",
            (2, 1),
            (-1, 1),
            BRANCO,
        ),

        (
            "BACKGROUND",
            (2, 2),
            (-1, 2),
            AZUL_SECUNDARIO,
        ),

        # ----------------------------------------------------
        # CORPO
        # ----------------------------------------------------

        (
            "BACKGROUND",
            (0, 3),
            (-1, -1),
            BRANCO,
        ),

        # ----------------------------------------------------
        # ALINHAMENTO
        # ----------------------------------------------------

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER",
        ),

        (
            "ALIGN",
            (1, 3),
            (1, -1),
            "LEFT",
        ),

        # ----------------------------------------------------
        # LINHAS DO CABEÇALHO
        # ----------------------------------------------------

        (
            "LINEBELOW",
            (0, 2),
            (-1, 2),
            0.65,
            AZUL_INSTITUCIONAL,
        ),

        (
            "LINEBELOW",
            (2, 0),
            (-1, 0),
            0.35,
            CINZA_LINHA,
        ),

        (
            "LINEBELOW",
            (2, 1),
            (-1, 1),
            0.3,
            CINZA_LINHA,
        ),

        # ----------------------------------------------------
        # SEPARAÇÃO MATRÍCULA / ESTUDANTE / UCs
        # ----------------------------------------------------

        (
            "LINEAFTER",
            (0, 0),
            (0, -1),
            0.45,
            CINZA_LINHA,
        ),

        (
            "LINEAFTER",
            (1, 0),
            (1, -1),
            0.8,
            AZUL_SECUNDARIO,
        ),

        # ----------------------------------------------------
        # PADDING
        # ----------------------------------------------------

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            1.0,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            1.0,
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            1.0,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            1.0,
        ),
    ]

    # --------------------------------------------------------
    # ZEBRA DISCRETA
    # --------------------------------------------------------
    #
    # Não usamos cor por FAL/CON.
    # A diferenciação ocorre pela posição e pelo cabeçalho.
    #

    quantidade_linhas = len(linhas)

    for indice in range(
        3,
        quantidade_linhas,
    ):

        numero_linha = indice - 3

        if numero_linha % 2 == 1:

            comandos.append(
                (
                    "BACKGROUND",
                    (0, indice),
                    (-1, indice),
                    CINZA_ZEBRA,
                )
            )

    # --------------------------------------------------------
    # LINHAS HORIZONTAIS DISCRETAS
    # --------------------------------------------------------

    for indice in range(
        3,
        quantidade_linhas,
    ):

        comandos.append(
            (
                "LINEBELOW",
                (0, indice),
                (-1, indice),
                0.22,
                CINZA_LINHA_SUAVE,
            )
        )

    # --------------------------------------------------------
    # DIVISÃO SUAVE ENTRE CADA PAR F/C
    # --------------------------------------------------------
    #
    # Mantemos alguma orientação visual sem transformar
    # cada célula em uma caixa.
    #

    for posicao, coluna in enumerate(
        bloco,
        start=2,
    ):

        if coluna is None:
            continue

        tipo = _tipo_coluna(
            coluna
        )

        if tipo == "CON":

            comandos.append(
                (
                    "LINEAFTER",
                    (posicao, 0),
                    (posicao, -1),
                    0.35,
                    CINZA_LINHA,
                )
            )

    # --------------------------------------------------------
    # APLICAÇÃO
    # --------------------------------------------------------

    tabela.setStyle(
        TableStyle(comandos)
    )

    return tabela


# ============================================================
# RODAPÉ
# ============================================================

def _rodape(canvas, doc):
    """
    Rodapé extremamente discreto.
    """

    canvas.saveState()

    largura_pagina, _ = landscape(A4)

    y = 5.0 * mm

    # Linha muito fina
    canvas.setStrokeColor(
        CINZA_LINHA
    )

    canvas.setLineWidth(0.3)

    canvas.line(
        MARGEM_ESQ,
        y + 3.2 * mm,
        largura_pagina - MARGEM_DIR,
        y + 3.2 * mm,
    )

    # Texto esquerdo
    canvas.setFont(
        "Helvetica",
        5.4,
    )

    canvas.setFillColor(
        CINZA_SECUNDARIO
    )

    canvas.drawString(
        MARGEM_ESQ,
        y,
        "CEP ETP • AFIN",
    )

    # Página
    canvas.drawRightString(
        largura_pagina - MARGEM_DIR,
        y,
        f"Página {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# LIMPEZA E PREPARAÇÃO DO DATAFRAME
# ============================================================

def _preparar_dataframe(df_matriz):
    """
    Faz uma cópia segura do DataFrame e garante
    nomes de colunas utilizáveis.

    Não altera o DataFrame original recebido pelo Streamlit.
    """

    if df_matriz is None:
        return pd.DataFrame()

    if not isinstance(
        df_matriz,
        pd.DataFrame,
    ):
        raise TypeError(
            "df_matriz deve ser um pandas.DataFrame."
        )

    df = df_matriz.copy()

    if df.empty:
        return df

    if len(df.columns) < 2:
        raise ValueError(
            "A matriz deve possuir pelo menos "
            "Matrícula e Estudante."
        )

    # --------------------------------------------------------
    # Garantir que os dois primeiros campos tenham nomes
    # --------------------------------------------------------

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

def gerar_pdf_afin(
    df_matriz,
    turma,
    semestre,
    mapa_nomes_iduc=None,
):
    """
    Gera o PDF consolidado da Matriz AFIN.

    Parâmetros
    ----------
    df_matriz : pandas.DataFrame
        DataFrame contendo:
        - coluna 0 = Matrícula
        - coluna 1 = Estudante
        - demais colunas = dados das UCs

    turma : str
        Identificação da turma.

    semestre : str
        Semestre acadêmico.

    mapa_nomes_iduc : dict, opcional
        Mapa no formato:
            {iduc: nome_uc}

    Retorno
    -------
    bytes
        Conteúdo binário do PDF.
    """

    # --------------------------------------------------------
    # PREPARAÇÃO
    # --------------------------------------------------------

    df = _preparar_dataframe(
        df_matriz
    )

    buffer = io.BytesIO()

    pagina = landscape(A4)

    largura_pagina, altura_pagina = pagina

    largura_util = (
        largura_pagina
        - MARGEM_ESQ
        - MARGEM_DIR
    )

    # --------------------------------------------------------
    # DOCUMENTO
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagina,

        leftMargin=MARGEM_ESQ,
        rightMargin=MARGEM_DIR,

        topMargin=MARGEM_SUP,
        bottomMargin=MARGEM_INF,

        title="Matriz AFIN",
        author=(
            "CEP ETP — "
            "Escola Técnica de Planaltina"
        ),

        subject=(
            "Acompanhamento da Frequência "
            "e Conceito"
        ),

        creator="CEP ETP",
    )

    # --------------------------------------------------------
    # ESTILOS
    # --------------------------------------------------------

    st = _estilos()

    # --------------------------------------------------------
    # MAPA IDUC
    # --------------------------------------------------------

    mapa = _mapa_iduc(
        mapa_nomes_iduc
    )

    # --------------------------------------------------------
    # COLUNAS ACADÊMICAS
    # --------------------------------------------------------

    if df.empty:

        colunas = []

    else:

        colunas = list(
            df.columns[2:]
        )

    # --------------------------------------------------------
    # BLOCOS DE 21 COLUNAS
    # --------------------------------------------------------

    blocos = _blocos(
        colunas
    )

    # --------------------------------------------------------
    # LARGURA DAS COLUNAS
    # --------------------------------------------------------

    largura_restante = (
        largura_util
        - LARGURA_MATRICULA
        - LARGURA_ESTUDANTE
    )

    largura_coluna = (
        largura_restante
        / COLUNAS_MATRIZ_POR_PAGINA
    )

    # --------------------------------------------------------
    # STORY
    # --------------------------------------------------------

    story = []

    for numero_bloco, bloco in enumerate(
        blocos,
        start=1,
    ):

        # ----------------------------------------------------
        # NOVA PÁGINA
        # ----------------------------------------------------

        if numero_bloco > 1:
            story.append(
                PageBreak()
            )

        # ----------------------------------------------------
        # CABEÇALHO
        # ----------------------------------------------------

        story.append(
            _topo(
                largura_util,
                st,
            )
        )

        story.append(
            Spacer(
                1,
                1.6 * mm,
            )
        )

        # ----------------------------------------------------
        # IDENTIFICAÇÃO
        # ----------------------------------------------------

        story.append(
            _identificacao(
                largura_util,
                turma,
                semestre,
                st,
            )
        )

        story.append(
            Spacer(
                1,
                1.7 * mm,
            )
        )

        # ----------------------------------------------------
        # TABELA
        # ----------------------------------------------------

        if df.empty:

            tabela_vazia = Table(
                [
                    [
                        Paragraph(
                            "Nenhum registro disponível.",
                            st["nome"],
                        )
                    ]
                ],
                colWidths=[
                    largura_util
                ],
            )

            tabela_vazia.setStyle(
                TableStyle(
                    [
                        (
                            "ALIGN",
                            (0, 0),
                            (-1, -1),
                            "CENTER",
                        ),

                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),

                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, -1),
                            CINZA_SECUNDARIO,
                        ),
                    ]
                )
            )

            story.append(
                tabela_vazia
            )

        else:

            story.append(
                _tabela(
                    df,
                    bloco,
                    mapa,
                    LARGURA_MATRICULA,
                    LARGURA_ESTUDANTE,
                    largura_coluna,
                    st,
                )
            )

    # --------------------------------------------------------
    # CONSTRUÇÃO
    # --------------------------------------------------------

    doc.build(
        story,
        onFirstPage=_rodape,
        onLaterPages=_rodape,
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# RELATÓRIO DE TURMA
# ============================================================

def gerar_pdf_relatorio_turma(dados):
    """
    Função auxiliar mantida para compatibilidade
    com outras partes do sistema.

    Esta função ainda é um placeholder.
    """

    buffer = io.BytesIO()

    buffer.write(
        b"%PDF-1.4\n"
        b"% Relatorio da Turma em desenvolvimento\n"
    )

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

    
    return buffer.getvalue()



# ============================================================
# DECLARAÇÃO DE ESCOLARIDADE (Placeholder / Funcional)
# ============================================================

def gerar_pdf_declaracao_escolaridade(dados_aluno):
    """
    Gera a Declaração de Escolaridade em A4.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph("DECLARAÇÃO DE ESCOLARIDADE", styles["Heading1"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PASSE ESTUDANTIL (Individual)
# ============================================================

def gerar_pdf_passe_estudantil(dados_aluno):
    """
    Gera o documento de Passe Estudantil individual.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph("PASSE ESTUDANTIL", styles["Heading1"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PASSES DA TURMA UNIFICADO
# ============================================================

def gerar_pdf_passes_turma_unificado(df_turma, turma_nome=""):
    """
    Gera o relatório unificado de passes estudantis da turma.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"PASSES ESTUDANTIS - TURMA: {turma_nome}", styles["Heading1"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
