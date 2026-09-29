import io
import os
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from modulos.conexao import executar_query


def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """
    Gera o Histórico Escolar em A4, com diagramação baseada na proposta visual,
    alinhamento rigoroso de colunas (largura útil total: 554 pt) e correção de campos.
    """

    # Compatibilidade com chamada invertida
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()

    # ------------------------------------------------------------------
    # CONFIGURAÇÃO DO DOCUMENTO (Largura útil exata: 554 pt)
    # A4 = 595.27 de largura. Margens de 20.6 pt à esquerda e direita.
    # ------------------------------------------------------------------
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20.6,
        leftMargin=20.6,
        topMargin=20,
        bottomMargin=22,
        title="Histórico Escolar",
        author="Centro de Educação Profissional Escola Técnica de Planaltina"
    )

    styles = getSampleStyleSheet()

    # ------------------------------------------------------------------
    # PALETA DE CORES
    # ------------------------------------------------------------------
    CINZA_TEXTO = colors.HexColor("#263238")
    CINZA_MEDIO = colors.HexColor("#5F6B72")
    CINZA_LINHA = colors.HexColor("#A0AAB0")
    CINZA_CAB = colors.HexColor("#E7EAEC")
    PRETO = colors.HexColor("#111111")

    # ------------------------------------------------------------------
    # ESTILOS
    # ------------------------------------------------------------------
    estilo_institucional = ParagraphStyle(
        "Institucional",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=8.5,
        alignment=TA_CENTER,
        textColor=PRETO
    )

    estilo_institucional_bold = ParagraphStyle(
        "InstitucionalBold",
        parent=estilo_institucional,
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=8.8
    )

    estilo_titulo = ParagraphStyle(
        "TituloHistorico",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=PRETO,
        spaceBefore=3,
        spaceAfter=3
    )

    estilo_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.0,
        leading=6.8,
        textColor=CINZA_MEDIO,
        spaceAfter=1
    )

    estilo_valor = ParagraphStyle(
        "Valor",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=8.2,
        textColor=CINZA_TEXTO
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
        fontSize=6.8,
        leading=7.6,
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
        leading=7.5,
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
    # TRATAMENTO DOS DADOS DO ALUNO
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

    curso = valor("curso", padrao="CURSO TÉCNICO EM NUTRIÇÃO E DIETÉTICA").upper()
    matricula = valor("matricula", "matrícula")
    turma = valor("turma")
    sigla = valor("sigla")
    nome = valor("nome").upper()
    cpf = valor("cpf")
    sexo = valor("sexo").upper()
    mae = valor("mae", "nome_mae").upper()
    pai = valor("pai", "nome_pai").upper()
    dt_nasc = valor("data_nascimento")
    
    # Tratamento para remover espaços incorretos em palavras como "BRASILEIRA"
    nacionalidade = valor("nacionalidade", padrao="BRASILEIRA").upper().replace(" ", "")
    if not nacionalidade:
        nacionalidade = "BRASILEIRA"
        
    naturalidade = valor("naturalidade").upper()
    uf = valor("uf", padrao="DF").upper()
    rg = valor("rg")
    orgao = valor("orgao_expeditor", "orgao").upper()
    dt_exp = valor("data_expedicao")

    # Formatação combinada de RG / Órgão / Expedição para evitar confusão com datas
    doc_rg_partes = [x for x in [rg, orgao, dt_exp] if x]
    doc_rg_str = " - ".join(doc_rg_partes) if doc_rg_partes else "—"

    # ------------------------------------------------------------------
    # BASE LEGAL
    # ------------------------------------------------------------------
    base_legal_texto = (
        "LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 04/99 - CEB/CNE, "
        "RESOLUÇÃO Nº 02/2023 - CEDF, PARECER Nº 27/2013-CEDF, PORTARIA Nº 56/2013 SEDF"
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
        Image(path_logo_gdf, width=38, height=38)
        if os.path.exists(path_logo_gdf)
        else Paragraph("", estilo_valor)
    )

    img_escola = (
        Image(path_logo_escola, width=38, height=38)
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
        colWidths=[45, 464, 45],
        rowHeights=[45],
        hAlign="LEFT"
    )

    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    story = []
    story.append(cabecalho)
    story.append(Paragraph("HISTÓRICO ESCOLAR", estilo_titulo))

    # ------------------------------------------------------------------
    # ORGANIZAÇÃO DAS LINHAS DO ESTUDANTE (GRELHA DE DADOS)
    # Largura total: 554 pt. Distribuição: [200, 110, 144, 100]
    # ------------------------------------------------------------------
    def celula_campo(rotulo, valor_txt, em_negrito=False):
        est_val = estilo_valor_bold if em_negrito else estilo_valor
        return [
            Paragraph(rotulo, estilo_label),
            Paragraph(valor_txt or "—", est_val)
        ]

    dados_estudante_grid = [
        # Linha 1: Curso / Nome / CPF / Sexo
        [
            celula_campo("Curso", curso, em_negrito=True),
            celula_campo("Nome", nome, em_negrito=True),
            celula_campo("CPF", cpf),
            celula_campo("Sexo", sexo),
        ],
        # Linha 2: Matrícula / Turma / Mãe / Pai
        [
            celula_campo("Matrícula", matricula, em_negrito=True),
            celula_campo("Turma", turma, em_negrito=True),
            celula_campo("Nome da Mãe", mae),
            celula_campo("Nome do Pai", pai),
        ],
        # Linha 3: Data Nasc. / Nacionalidade / Naturalidade-UF / RG-Órgão-Expedição
        [
            celula_campo("Data de Nascimento", dt_nasc),
            celula_campo("Nacionalidade", nacionalidade),
            celula_campo("Naturalidade / UF", f"{naturalidade} / {uf}".strip(" /")),
            celula_campo("RG / Órgão / Expedição", doc_rg_str),
        ],
    ]

    tabela_dados = Table(
        dados_estudante_grid,
        colWidths=[130, 184, 140, 100],
        hAlign="LEFT"
    )

    tabela_dados.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    story.append(tabela_dados)

    # ------------------------------------------------------------------
    # BASE LEGAL (Linha Integrada de Largura Total: 554 pt)
    # ------------------------------------------------------------------
    celula_base_legal = [
        Paragraph("Base Legal", estilo_label),
        Paragraph(base_legal_texto, estilo_valor)
    ]
    
    tabela_base_legal = Table(
        [[celula_base_legal]],
        colWidths=[554],
        hAlign="LEFT"
    )
    tabela_base_legal.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    story.append(tabela_base_legal)
    story.append(Spacer(1, 4))

    # ------------------------------------------------------------------
    # HISTÓRICO ACADÊMICO (Soma exata: 314 + 50 + 35 + 55 + 40 + 60 = 554 pt)
    # ------------------------------------------------------------------
    header_hist = [
        Paragraph("Componente Curricular", estilo_th),
        Paragraph("Semestre", estilo_th),
        Paragraph("CH", estilo_th),
        Paragraph("Módulo", estilo_th),
        Paragraph("Faltas", estilo_th),
        Paragraph("Resultado", estilo_th),
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
            
            sem = str(row.get("semestre", "")).strip()
            
            if not sem or sem.lower() in ("none", "nan", ""):
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
        colWidths=[314, 50, 35, 55, 40, 60],
        hAlign="LEFT"
    )

    estilo_hist = [
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CAB),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, CINZA_LINHA),
        ("GRID", (0, 0), (-1, -1), 0.35, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
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
    # BLOCO FINAL (Legenda, Data e Assinaturas)
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
        Spacer(1, 8),
        data_tabela,
        Spacer(1, 20),
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

    # GERAÇÃO DO PDF
    doc.build(
        story,
        onFirstPage=desenhar_rodape,
        onLaterPages=desenhar_rodape
    )

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

MARGEM_ESQ = 12 * mm
MARGEM_DIR = 12 * mm
MARGEM_SUP = 12 * mm
MARGEM_INF = 12 * mm

LARGURA_MATRICULA = 24 * mm
LARGURA_ESTUDANTE = 52 * mm


# ============================================================
# PALETA — PRETO, BRANCO E CINZAS
# Apenas tons neutros. Nenhum preenchimento colorido.
# ============================================================

PRETO            = colors.HexColor("#000000")
CINZA_ESCURO     = colors.HexColor("#333333")
CINZA_MEDIO      = colors.HexColor("#666666")
CINZA_CLARO      = colors.HexColor("#999999")
CINZA_FIO        = colors.HexColor("#AAAAAA")
CINZA_FIO_SUAVE  = colors.HexColor("#CCCCCC")
BRANCO           = colors.white


# ============================================================
# FUNÇÕES DE NORMALIZAÇÃO
# ============================================================

def _texto(valor):
    """Converte qualquer valor em texto seguro para o PDF."""
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
    """Escapa caracteres especiais para uso dentro de Paragraph."""
    return (
        _texto(valor)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _normalizar(valor):
    """Normalização usada para comparação de nomes de UCs."""
    return re.sub(r"\s+", " ", _texto(valor).upper()).strip()


# ============================================================
# IDENTIFICAÇÃO DE COLUNAS
# ============================================================

def _tipo_coluna(nome):
    """Identifica FAL (Faltas) ou CON (Conceito)."""
    s = _normalizar(nome)
    if re.search(r"(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])", s):
        return "FAL"
    if re.search(r"(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])", s):
        return "CON"
    return None


def _nome_uc(nome):
    """Remove o sufixo FAL/CON do nome da coluna."""
    return re.sub(
        r"\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$",
        "",
        _texto(nome),
        flags=re.I,
    ).strip()


def _mapa_iduc(mapa):
    """Normaliza o mapa {iduc: nome_uc}."""
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
        # --- Cabeçalho institucional ---
        "instituicao": ParagraphStyle(
            "AFINInstituicao", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8, leading=9,
            alignment=TA_CENTER, textColor=PRETO
        ),
        "titulo": ParagraphStyle(
            "AFINTitulo", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=11, leading=12,
            alignment=TA_CENTER, textColor=PRETO
        ),
        "subtitulo": ParagraphStyle(
            "AFINSubtitulo", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.5, leading=8.5,
            alignment=TA_CENTER, textColor=CINZA_ESCURO
        ),
        # --- Identificação do curso/turma ---
        "label": ParagraphStyle(
            "AFINLabel", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=6, leading=6.5,
            alignment=TA_LEFT, textColor=CINZA_MEDIO
        ),
        "valor": ParagraphStyle(
            "AFINValor", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=8.5, leading=9,
            alignment=TA_LEFT, textColor=PRETO
        ),
        # --- Cabeçalho da matriz ---
        "matricula_header": ParagraphStyle(
            "AFINMatriculaHeader", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=5.8, leading=6.2,
            alignment=TA_CENTER, textColor=PRETO
        ),
        "estudante_header": ParagraphStyle(
            "AFINEstudanteHeader", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=5.8, leading=6.2,
            alignment=TA_LEFT, textColor=PRETO
        ),
        "uc": ParagraphStyle(
            "AFINUC", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=5.4, leading=5.8,
            alignment=TA_CENTER, textColor=PRETO
        ),
        "iduc": ParagraphStyle(
            "AFINIDUC", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=4.6, leading=4.9,
            alignment=TA_CENTER, textColor=CINZA_MEDIO
        ),
        "indicador": ParagraphStyle(
            "AFINIndicador", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=5.5, leading=5.7,
            alignment=TA_CENTER, textColor=PRETO
        ),
        "indicador_vazio": ParagraphStyle(
            "AFINIndicadorVazio", parent=base["Normal"],
            fontName="Helvetica", fontSize=5.5, leading=5.7,
            alignment=TA_CENTER, textColor=CINZA_CLARO
        ),
        # --- Corpo ---
        "matricula": ParagraphStyle(
            "AFINMatricula", parent=base["Normal"],
            fontName="Courier", fontSize=6.2, leading=6.8,
            alignment=TA_CENTER, textColor=PRETO
        ),
        "nome": ParagraphStyle(
            "AFINNome", parent=base["Normal"],
            fontName="Helvetica", fontSize=6.5, leading=7.1,
            alignment=TA_LEFT, textColor=PRETO
        ),
        "valor_celula": ParagraphStyle(
            "AFINValorCelula", parent=base["Normal"],
            fontName="Helvetica", fontSize=6.3, leading=6.8,
            alignment=TA_CENTER, textColor=PRETO
        ),
    }


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
        quantidade_faltante = COLUNAS_MATRIZ_POR_PAGINA - len(bloco)
        if quantidade_faltante > 0:
            bloco.extend([None] * quantidade_faltante)
        saida.append(bloco)
    return saida


# ============================================================
# CABEÇALHO INSTITUCIONAL (sóbrio, com fios)
# ============================================================

def _topo(largura, st):
    dados = [
        [Paragraph("SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL", st["instituicao"])],
        [Paragraph("CEP – ESCOLA TÉCNICA DE PLANALTINA", st["titulo"])],
        [Paragraph("AFIN — ACOMPANHAMENTO DA FREQUÊNCIA E CONCEITO", st["subtitulo"])],
    ]
    tabela = Table(
        dados,
        colWidths=[largura],
        rowHeights=[4.5 * mm, 5.5 * mm, 4.0 * mm],
        hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, PRETO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, CINZA_FIO),
        ("LINEBELOW", (0, 1), (-1, 1), 0.4, CINZA_FIO),
        ("LINEBELOW", (0, 2), (-1, 2), 1.2, PRETO),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tabela


# ============================================================
# IDENTIFICAÇÃO DA TURMA E CURSO (linha simples com rótulos e valores)
# ============================================================

def _identificacao(largura, curso, turma, semestre, st):
    # Distribuição proporcional: Curso ~ 45%, Turma ~ 30%, Semestre ~ 25%
    larg_curso_lbl, larg_curso_val = 14 * mm, (largura * 0.45) - 14 * mm
    larg_turma_lbl, larg_turma_val = 14 * mm, (largura * 0.30) - 14 * mm
    larg_sem_lbl, larg_sem_val     = 18 * mm, (largura * 0.25) - 18 * mm

    dados = [[
        Paragraph("CURSO", st["label"]),
        Paragraph(_html(curso if curso else "—"), st["valor"]),
        Paragraph("TURMA", st["label"]),
        Paragraph(_html(turma), st["valor"]),
        Paragraph("SEMESTRE", st["label"]),
        Paragraph(_html(semestre), st["valor"]),
    ]]
    larguras = [
        larg_curso_lbl, larg_curso_val,
        larg_turma_lbl, larg_turma_val,
        larg_sem_lbl, larg_sem_val
    ]
    tabela = Table(dados, colWidths=larguras, rowHeights=[7 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, CINZA_ESCURO),
        ("LINEAFTER", (1, 0), (1, 0), 0.4, CINZA_FIO),
        ("LINEAFTER", (3, 0), (3, 0), 0.4, CINZA_FIO),
    ]))
    return tabela


# ============================================================
# CABEÇALHO DA MATRIZ
# ============================================================

def _cabecalho(bloco, mapa, wm, wn, wc, st):
    linha_uc = [
        Paragraph("MATRÍCULA", st["matricula_header"]),
        Paragraph("ESTUDANTE", st["estudante_header"]),
    ]
    linha_iduc = [
        Paragraph("", st["matricula_header"]),
        Paragraph("", st["estudante_header"]),
    ]
    linha_indicador = [
        Paragraph("", st["matricula_header"]),
        Paragraph("", st["estudante_header"]),
    ]

    larguras = [wm, wn]

    for nome_coluna in bloco:
        larguras.append(wc)
        if nome_coluna is None:
            linha_uc.append(Paragraph("", st["uc"]))
            linha_iduc.append(Paragraph("", st["iduc"]))
            linha_indicador.append(Paragraph("", st["indicador_vazio"]))
            continue

        uc = _nome_uc(nome_coluna)
        iduc = mapa.get(_normalizar(uc), "")
        tipo = _tipo_coluna(nome_coluna)

        linha_uc.append(Paragraph(_html(uc), st["uc"]))
        linha_iduc.append(Paragraph(_html(iduc), st["iduc"]))

        indicador = "F" if tipo == "FAL" else ("C" if tipo == "CON" else "")
        if indicador:
            linha_indicador.append(Paragraph(indicador, st["indicador"]))
        else:
            linha_indicador.append(Paragraph("", st["indicador_vazio"]))

    return [linha_uc, linha_iduc, linha_indicador], larguras


# ============================================================
# TABELA PRINCIPAL (COM MESCLAGEM DE UCs)
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
        # Mesclagem vertical para Matrícula e Estudante no cabeçalho
        ("SPAN", (0, 0), (0, 2)),
        ("SPAN", (1, 0), (1, 2)),

        # --- Fios do cabeçalho ---
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, PRETO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, CINZA_FIO),
        ("LINEBELOW", (0, 1), (-1, 1), 0.3, CINZA_FIO_SUAVE),
        ("LINEBELOW", (0, 2), (-1, 2), 1.0, PRETO),

        # --- Fios verticais estruturais ---
        ("LINEAFTER", (0, 0), (0, -1), 0.4, CINZA_FIO),
        ("LINEAFTER", (1, 0), (1, -1), 0.4, CINZA_FIO),
        ("LINEAFTER", (1, 0), (1, -1), 1.0, CINZA_ESCURO),

        # --- Alinhamento ---
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 3), (1, -1), "LEFT"),

        # --- Padding ---
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.0),
    ]

    # --- Lógica de mesclagem das colunas de UC (pares FAL e CON) ---
    idx = 0
    while idx < len(bloco):
        col_atual = bloco[idx]
        if col_atual is None:
            idx += 1
            continue

        uc_atual = _nome_uc(col_atual)
        span_len = 1

        # Verifica se as colunas subsequentes pertencem à mesma UC
        while (idx + span_len) < len(bloco):
            col_prox = bloco[idx + span_len]
            if col_prox is not None and _nome_uc(col_prox) == uc_atual:
                span_len += 1
            else:
                break

        col_inicio = 2 + idx
        col_fim = 2 + idx + span_len - 1

        if span_len > 1:
            # Mescla as células do título da UC
            comandos.append(("SPAN", (col_inicio, 0), (col_fim, 0)))
            # Mescla as células do IDUC (se houver)
            comandos.append(("SPAN", (col_inicio, 1), (col_fim, 1)))

        idx += span_len

    # --- Fio inferior forte no final da tabela ---
    quantidade_linhas = len(linhas)
    comandos.append(("LINEBELOW", (0, quantidade_linhas - 1), (-1, quantidade_linhas - 1), 1.0, PRETO))

    # --- Divisão entre pares F/C ---
    for posicao, coluna in enumerate(bloco, start=2):
        if coluna is None:
            continue
        if _tipo_coluna(coluna) == "CON":
            comandos.append(("LINEAFTER", (posicao, 0), (posicao, -1), 0.5, CINZA_ESCURO))

    # --- Fios horizontais suaves entre linhas de dados ---
    for indice in range(3, quantidade_linhas):
        comandos.append(("LINEBELOW", (0, indice), (-1, indice), 0.2, CINZA_FIO_SUAVE))

    tabela.setStyle(TableStyle(comandos))
    return tabela


# ============================================================
# RODAPÉ
# ============================================================

def _rodape(canvas, doc):
    canvas.saveState()
    largura_pagina, _ = landscape(A4)
    y = 6.0 * mm

    # Fio fino acima do rodapé
    canvas.setStrokeColor(CINZA_FIO)
    canvas.setLineWidth(0.3)
    canvas.line(MARGEM_ESQ, y + 3.0 * mm, largura_pagina - MARGEM_DIR, y + 3.0 * mm)

    # Linha 1 — identificação + data + página
    canvas.setFont("Helvetica", 5.4)
    canvas.setFillColor(CINZA_MEDIO)
    canvas.drawString(MARGEM_ESQ, y, "CEP ETP • Matriz AFIN")

    data_geracao = datetime.now().strftime("%d/%m/%Y")
    canvas.drawCentredString(largura_pagina / 2, y, f"Gerado em {data_geracao}")
    canvas.drawRightString(largura_pagina - MARGEM_DIR, y, f"Página {doc.page}")

    # Linha 2 — legenda
    canvas.setFont("Helvetica", 4.8)
    canvas.setFillColor(CINZA_CLARO)
    canvas.drawString(MARGEM_ESQ, y - 2.6 * mm, "F = Faltas   •   C = Conceito")

    canvas.restoreState()


# ============================================================
# PREPARAÇÃO DO DATAFRAME E FUNÇÃO PRINCIPAL
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


def gerar_pdf_afin(df_matriz, turma, semestre, curso="", mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN (modelo tradicional P&B)."""
    df = _preparar_dataframe(df_matriz)
    buffer = io.BytesIO()
    pagina = landscape(A4)
    largura_pagina, altura_pagina = pagina
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
        story.append(Spacer(1, 2.0 * mm))
        story.append(_identificacao(largura_util, curso, turma, semestre, st))
        story.append(Spacer(1, 2.0 * mm))

        if df.empty:
            tabela_vazia = Table(
                [[Paragraph("Nenhum registro disponível.", st["nome"])]],
                colWidths=[largura_util],
            )
            tabela_vazia.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEABOVE", (0, 0), (-1, 0), 0.8, PRETO),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, PRETO),
            ]))
            story.append(tabela_vazia)
        else:
            story.append(
                _tabela(
                    df, bloco, mapa,
                    LARGURA_MATRICULA, LARGURA_ESTUDANTE, largura_coluna, st,
                )
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
