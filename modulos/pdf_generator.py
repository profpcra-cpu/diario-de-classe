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
Gerador Profissional da Matriz AFIN - CEP ETP.

Modelo Refinado e Minimalista (baseado na referência visual):
- Cabeçalho superior em texto limpo (sem blocos azuis pesados)
- Identificação da turma/semestre com fundo creme suave
- Azul marinho profundo (#1F3A52) pontual para MATRÍCULA/ESTUDANTE e barra F/C
- Texto vertical (90º) para nomes longos de disciplinas
- Tabela limpa com linhas de divisão suaves
- A4 Paisagem com 21 colunas por página
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
# CONFIGURAÇÕES GERAIS DE GEOMETRIA
# ============================================================

COLUNAS_MATRIZ_POR_PAGINA = 21

MARGEM_ESQ = 8 * mm
MARGEM_DIR = 8 * mm
MARGEM_SUP = 6 * mm
MARGEM_INF = 8 * mm

LARGURA_MATRICULA = 22 * mm
LARGURA_ESTUDANTE = 48 * mm

# ============================================================
# PALETA DE CORES REFINADA (MODELO LIMPO)
# ============================================================

AZUL_MARINHO_NOBRE    = colors.HexColor("#1F3A52")  # Azul escuro e elegante
AMARELO_PASTEL_HEADER = colors.HexColor("#F9F4E1")  # Fundo limpo do topo/UCs
AMARELO_PASTEL_TURMA  = colors.HexColor("#FFF8DC")  # Destaque de Turma/Semestre

CINZA_TEXTO           = colors.HexColor("#222222")
CINZA_SECUNDARIO      = colors.HexColor("#666666")

CINZA_LINHA           = colors.HexColor("#CCCCCC")
CINZA_LINHA_SUAVE     = colors.HexColor("#E5E7EB")

FUNDO_DADOS           = colors.white
CINZA_ZEBRA           = colors.HexColor("#FAFAFA")  # Zebra quase impercetível

BRANCO                = colors.white


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def _texto(valor):
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
    return (
        _texto(valor)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _normalizar(valor):
    return re.sub(r"\s+", " ", _texto(valor).upper()).strip()


def _tipo_coluna(nome):
    s = _normalizar(nome)
    if re.search(r"(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])", s):
        return "FAL"
    if re.search(r"(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])", s):
        return "CON"
    return None


def _nome_uc(nome):
    return re.sub(
        r"\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$",
        "",
        _texto(nome),
        flags=re.I,
    ).strip()


def _mapa_iduc(mapa):
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
    base = getSampleStyleSheet()
    return {
        "instituicao": ParagraphStyle(
            "AFINInstituicao", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, leading=10,
            alignment=TA_CENTER, textColor=CINZA_TEXTO
        ),
        "titulo": ParagraphStyle(
            "AFINTitulo", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=11, leading=12,
            alignment=TA_CENTER, textColor=AZUL_MARINHO_NOBRE
        ),
        "subtitulo": ParagraphStyle(
            "AFINSubtitulo", parent=base["Normal"],
            fontName="Helvetica", fontSize=7, leading=8,
            alignment=TA_CENTER, textColor=CINZA_SECUNDARIO
        ),
        "label": ParagraphStyle(
            "AFINLabel", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=6.5, leading=7,
            alignment=TA_LEFT, textColor=CINZA_SECUNDARIO
        ),
        "valor": ParagraphStyle(
            "AFINValor", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8.5, leading=9,
            alignment=TA_LEFT, textColor=AZUL_MARINHO_NOBRE
        ),
        "matricula_header": ParagraphStyle(
            "AFINMatriculaHeader", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=6, leading=6.5,
            alignment=TA_CENTER, textColor=BRANCO
        ),
        "estudante_header": ParagraphStyle(
            "AFINEstudanteHeader", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=6, leading=6.5,
            alignment=TA_LEFT, textColor=BRANCO
        ),
        "uc": ParagraphStyle(
            "AFINUC", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=4.8, leading=5.2,
            alignment=TA_CENTER, textColor=CINZA_TEXTO
        ),
        "iduc": ParagraphStyle(
            "AFINIDUC", parent=base["Normal"],
            fontName="Helvetica", fontSize=4.5, leading=4.8,
            alignment=TA_CENTER, textColor=CINZA_SECUNDARIO
        ),
        "indicador": ParagraphStyle(
            "AFINIndicador", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=5.5, leading=6,
            alignment=TA_CENTER, textColor=BRANCO
        ),
        "matricula": ParagraphStyle(
            "AFINMatricula", parent=base["Normal"],
            fontName="Helvetica", fontSize=6.2, leading=6.8,
            alignment=TA_CENTER, textColor=CINZA_TEXTO
        ),
        "nome": ParagraphStyle(
            "AFINNome", parent=base["Normal"],
            fontName="Helvetica", fontSize=6.2, leading=6.8,
            alignment=TA_LEFT, textColor=CINZA_TEXTO
        ),
        "valor_celula": ParagraphStyle(
            "AFINValorCelula", parent=base["Normal"],
            fontName="Helvetica", fontSize=6.0, leading=6.5,
            alignment=TA_CENTER, textColor=CINZA_TEXTO
        ),
    }


# ============================================================
# DIVISÃO DOS BLOCOS
# ============================================================

def _blocos(colunas):
    if not colunas:
        return [[None] * COLUNAS_MATRIZ_POR_PAGINA]
    saida = []
    for inicio in range(0, len(colunas), COLUNAS_MATRIZ_POR_PAGINA):
        bloco = list(colunas[inicio:inicio + COLUNAS_MATRIZ_POR_PAGINA])
        faltante = COLUNAS_MATRIZ_POR_PAGINA - len(bloco)
        if faltante > 0:
            bloco.extend([None] * faltante)
        saida.append(bloco)
    return saida


# ============================================================
# CABEÇALHO INSTITUCIONAL CLEAN
# ============================================================

def _topo(largura, st):
    dados = [
        [Paragraph("SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL", st["instituicao"])],
        [Paragraph("CEP – ESCOLA TÉCNICA DE PLANALTINA", st["titulo"])],
        [Paragraph("AFIN — ACOMPANHAMENTO DA FREQUÊNCIA E CONCEITO", st["subtitulo"])],
    ]
    tabela = Table(dados, colWidths=[largura], rowHeights=[3.8 * mm, 4.5 * mm, 3.2 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


# ============================================================
# IDENTIFICAÇÃO DA TURMA (BARRA SUPERIOR PASTEL)
# ============================================================

def _identificacao(largura, turma, semestre, st):
    metade = largura / 2
    dados = [[
        Paragraph("TURMA:", st["label"]),
        Paragraph(_html(turma), st["valor"]),
        Paragraph("SEMESTRE:", st["label"]),
        Paragraph(_html(semestre), st["valor"]),
    ]]
    larguras = [14 * mm, metade - 14 * mm, 18 * mm, metade - 18 * mm]
    tabela = Table(dados, colWidths=larguras, rowHeights=[6.5 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AMARELO_PASTEL_TURMA),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, CINZA_LINHA),
        ("LINETOP", (0, 0), (-1, 0), 0.5, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


# ============================================================
# CABEÇALHO DA TABELA
# ============================================================

def _cabecalho(bloco, mapa, wm, wn, wc, st):
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


# ============================================================
# TABELA PRINCIPAL
# ============================================================

def _tabela(df, bloco, mapa, wm, wn, wc, st):
    cabecalho, larguras = _cabecalho(bloco, mapa, wm, wn, wc, st)
    posicoes = {coluna: indice for indice, coluna in enumerate(df.columns)}
    linhas = list(cabecalho)

    for _, row in df.iterrows():
        linha = [
            Paragraph(_html(row.iloc[0]), st["matricula"]),
            Paragraph(_html(row.iloc[1]), st["nome"]),
        ]
        for coluna in bloco:
            if coluna is None:
                valor = ""
            else:
                valor = _texto(row.iloc[posicoes[coluna]])
            linha.append(Paragraph(_html(valor), st["valor_celula"]))
        linhas.append(linha)

    tabela = Table(linhas, colWidths=larguras, repeatRows=3, hAlign="LEFT")

    comandos = [
        # Cabeçalho Matrícula / Estudante em Azul Marinho
        ("BACKGROUND", (0, 0), (1, 2), AZUL_MARINHO_NOBRE),

        # Nomes das UCs sobre fundo Creme Pastelo Limpo
        ("BACKGROUND", (2, 0), (-1, 0), AMARELO_PASTEL_HEADER),
        ("BACKGROUND", (2, 1), (-1, 1), AMARELO_PASTEL_HEADER),
        
        # Faixa dos Indicadores (F/C) em Azul Marinho
        ("BACKGROUND", (2, 2), (-1, 2), AZUL_MARINHO_NOBRE),

        # Corpo dos Dados
        ("BACKGROUND", (0, 3), (-1, -1), FUNDO_DADOS),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 3), (1, -1), "LEFT"),

        # Linhas de Estrutura
        ("LINEBELOW", (0, 2), (-1, 2), 0.8, AZUL_MARINHO_NOBRE),
        ("LINEBELOW", (2, 0), (-1, 0), 0.3, CINZA_LINHA),
        ("LINEAFTER", (0, 0), (0, -1), 0.3, CINZA_LINHA),
        ("LINEAFTER", (1, 0), (1, -1), 0.8, AZUL_MARINHO_NOBRE),

        # Padding Ajustado
        ("TOPPADDING", (0, 0), (-1, -1), 0.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 0.8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0.8),
    ]

    # Zebra Discreta
    for indice in range(3, len(linhas)):
        if (indice - 3) % 2 == 1:
            comandos.append(("BACKGROUND", (0, indice), (-1, indice), CINZA_ZEBRA))
        comandos.append(("LINEBELOW", (0, indice), (-1, indice), 0.2, CINZA_LINHA_SUAVE))

    # Divisória entre Blocos de Disciplinas
    for posicao, coluna in enumerate(bloco, start=2):
        if coluna is None:
            continue
        if _tipo_coluna(coluna) == "CON":
            comandos.append(("LINEAFTER", (posicao, 0), (posicao, -1), 0.35, CINZA_LINHA))

    tabela.setStyle(TableStyle(comandos))
    return tabela


# ============================================================
# RODAPÉ
# ============================================================

def _rodape(canvas, doc):
    canvas.saveState()
    largura_pagina, _ = landscape(A4)
    y = 4.5 * mm

    canvas.setStrokeColor(CINZA_LINHA_SUAVE)
    canvas.setLineWidth(0.3)
    canvas.line(MARGEM_ESQ, y + 2.8 * mm, largura_pagina - MARGEM_DIR, y + 2.8 * mm)

    canvas.setFont("Helvetica", 5.2)
    canvas.setFillColor(CINZA_SECUNDARIO)
    canvas.drawString(MARGEM_ESQ, y, "CEP ETP • Documento Oficial de Frequência e Conceito")
    canvas.drawRightString(largura_pagina - MARGEM_DIR, y, f"Página {doc.page}")

    canvas.restoreState()


# ============================================================
# PREPARAÇÃO E FUNÇÃO PRINCIPAL
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


def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN com visual limpo e refinado."""
    df = _preparar_dataframe(df_matriz)
    buffer = io.BytesIO()
    pagina = landscape(A4)
    largura_pagina, altura_pagina = pagina
    largura_util = largura_pagina - MARGEM_ESQ - MARGEM_DIR

    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=MARGEM_ESQ, rightMargin=MARGEM_DIR,
        topMargin=MARGEM_SUP, bottomMargin=MARGEM_INF,
        title="Matriz AFIN", author="CEP ETP — Escola Técnica de Planaltina",
        subject="Acompanhamento da Frequência e Conceito", creator="CEP ETP",
    )

    st = _estilos()
    mapa = _mapa_iduc(mapa_nomes_iduc)
    colunas = [] if df.empty else list(df.columns[2:])
    blocos = _blocos(colunas)

    largura_restante = largura_util - LARGURA_MATRICULA - LARGURA_ESTUDANTE
    largura_coluna = largura_restante / COLUNAS_MATRIZ_POR_PAGINA

    story = []

    for numero_bloco, bloco in enumerate(blocos, start=1):
        if numero_bloco > 1:
            story.append(PageBreak())

        story.append(_topo(largura_util, st))
        story.append(Spacer(1, 1.2 * mm))
        story.append(_identificacao(largura_util, turma, semestre, st))
        story.append(Spacer(1, 1.5 * mm))

        if df.empty:
            tabela_vazia = Table([[Paragraph("Nenhum registo disponível.", st["nome"])]], colWidths=[largura_util])
            tabela_vazia.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, -1), CINZA_SECUNDARIO),
            ]))
            story.append(tabela_vazia)
        else:
            story.append(_tabela(df, bloco, mapa, LARGURA_MATRICULA, LARGURA_ESTUDANTE, largura_coluna, st))

    doc.build(story, onFirstPage=_rodape, onLaterPages=_rodape)
    buffer.seek(0)
    return buffer.getvalue()
