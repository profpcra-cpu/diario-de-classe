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
"""Gerador profissional da Matriz AFIN - CEP ETP."""
import io
import re
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

# ============================================================
# CONFIGURAÇÕES
# ============================================================
COLUNAS_MATRIZ_POR_PAGINA = 21
MARGEM_ESQ = 10 * mm
MARGEM_DIR = 10 * mm
MARGEM_SUP = 9 * mm
MARGEM_INF = 10 * mm
LARGURA_MATRICULA = 23 * mm
LARGURA_ESTUDANTE = 47 * mm

AZUL = colors.HexColor('#163A63')
AZUL_2 = colors.HexColor('#244F7D')
AZUL_CLARO = colors.HexColor('#EAF1F8')
CINZA_1 = colors.HexColor('#F7F9FB')
CINZA_2 = colors.HexColor('#E7ECF2')
CINZA_3 = colors.HexColor('#D5DDE6')
TEXTO = colors.HexColor('#25313D')
FAL_BG = colors.HexColor('#FFF4E5')
CON_BG = colors.HexColor('#EAF6EE')


def _texto(valor):
    if valor is None:
        return ''
    try:
        if pd.isna(valor):
            return ''
    except Exception:
        pass
    s = str(valor).strip()
    return '' if s.lower() in {'nan', 'nat', 'none'} else s


def _html(valor):
    return (_texto(valor).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _normalizar(valor):
    return re.sub(r'\s+', ' ', _texto(valor).upper()).strip()


def _tipo_coluna(nome):
    s = _normalizar(nome)
    if re.search(r'(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])', s):
        return 'FAL'
    if re.search(r'(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])', s):
        return 'CON'
    return None


def _nome_uc(nome):
    return re.sub(r'\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$', '', _texto(nome), flags=re.I).strip()


def _mapa_iduc(mapa):
    if not mapa:
        return {}
    return {_normalizar(nome): _texto(iduc) for iduc, nome in mapa.items() if _texto(nome)}


def _estilos():
    base = getSampleStyleSheet()
    return {
        'topo': ParagraphStyle('AFINTopo', parent=base['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=9.5, alignment=TA_CENTER, textColor=colors.white),
        'subtopo': ParagraphStyle('AFINSubTopo', parent=base['Normal'], fontName='Helvetica', fontSize=6.3, leading=7, alignment=TA_CENTER, textColor=colors.white),
        'label': ParagraphStyle('AFINLabel', parent=base['Normal'], fontName='Helvetica-Bold', fontSize=6.3, leading=7, alignment=TA_LEFT, textColor=AZUL),
        'valor': ParagraphStyle('AFINValor', parent=base['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=8.5, alignment=TA_LEFT, textColor=TEXTO),
        'th': ParagraphStyle('AFINTH', parent=base['Normal'], fontName='Helvetica-Bold', fontSize=5.5, leading=6, alignment=TA_CENTER, textColor=colors.white),
        'uc': ParagraphStyle('AFINUC', parent=base['Normal'], fontName='Helvetica-Bold', fontSize=5.2, leading=5.7, alignment=TA_CENTER, textColor=TEXTO),
        'iduc': ParagraphStyle('AFINIDUC', parent=base['Normal'], fontName='Helvetica-Bold', fontSize=5.1, leading=5.6, alignment=TA_CENTER, textColor=AZUL),
        'td': ParagraphStyle('AFINTD', parent=base['Normal'], fontName='Helvetica', fontSize=6.1, leading=6.8, alignment=TA_CENTER, textColor=TEXTO),
        'nome': ParagraphStyle('AFINNome', parent=base['Normal'], fontName='Helvetica', fontSize=6.1, leading=6.8, alignment=TA_LEFT, textColor=TEXTO),
    }


def _blocos(colunas):
    """Divide as colunas reais em blocos de exatamente 21 posições.
    Somente o último bloco recebe colunas vazias; nenhuma coluna real é repetida.
    """
    if not colunas:
        return [[None] * COLUNAS_MATRIZ_POR_PAGINA]
    saida = []
    for i in range(0, len(colunas), COLUNAS_MATRIZ_POR_PAGINA):
        bloco = list(colunas[i:i + COLUNAS_MATRIZ_POR_PAGINA])
        bloco.extend([None] * (COLUNAS_MATRIZ_POR_PAGINA - len(bloco)))
        saida.append(bloco)
    return saida


def _topo(largura, st):
    t = Table([
        [Paragraph('SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL', st['topo'])],
        [Paragraph('CEP ETP — ESCOLA TÉCNICA DE PLANALTINA', st['topo'])],
        [Paragraph('AFIN — ACOMPANHAMENTO DA FORMAÇÃO E INFORMAÇÕES ACADÊMICAS', st['subtopo'])],
    ], colWidths=[largura], rowHeights=[6.2*mm, 6.2*mm, 4.8*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,1), AZUL), ('BACKGROUND', (0,2), (-1,2), AZUL_2),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), .6, AZUL), ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    return t


def _identificacao(largura, turma, semestre, st):
    wl = 25*mm
    wv = (largura - 2*wl) / 2
    t = Table([[Paragraph('TURMA', st['label']), Paragraph(_html(turma), st['valor']),
                Paragraph('SEMESTRE', st['label']), Paragraph(_html(semestre), st['valor'])]],
              colWidths=[wl,wv,wl,wv], rowHeights=[8*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),AZUL_CLARO), ('BACKGROUND',(2,0),(2,0),AZUL_CLARO),
        ('BOX',(0,0),(-1,-1),.5,CINZA_3), ('INNERGRID',(0,0),(-1,-1),.5,CINZA_3),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('LEFTPADDING',(0,0),(-1,-1),4),
        ('RIGHTPADDING',(0,0),(-1,-1),4), ('TOPPADDING',(0,0),(-1,-1),1),
        ('BOTTOMPADDING',(0,0),(-1,-1),1),
    ]))
    return t


def _cabecalho(bloco, mapa, wm, wn, wc, st):
    l1 = [Paragraph('MATRÍCULA', st['th']), Paragraph('ESTUDANTE', st['th'])]
    l2 = [Paragraph('', st['th']), Paragraph('', st['th'])]
    l3 = [Paragraph('', st['th']), Paragraph('', st['th'])]
    larguras = [wm, wn]
    for nome_col in bloco:
        larguras.append(wc)
        if nome_col is None:
            l1.append(Paragraph('', st['uc']))
            l2.append(Paragraph('', st['iduc']))
            l3.append(Paragraph('', st['th']))
            continue
        uc = _nome_uc(nome_col)
        iduc = mapa.get(_normalizar(uc), '')
        tipo = _tipo_coluna(nome_col)
        l1.append(Paragraph(_html(uc), st['uc']))
        l2.append(Paragraph(_html(iduc), st['iduc']))
        l3.append(Paragraph('F' if tipo == 'FAL' else 'C' if tipo == 'CON' else '', st['th']))
    return [l1,l2,l3], larguras


def _tabela(df, bloco, mapa, wm, wn, wc, st):
    cab, larguras = _cabecalho(bloco, mapa, wm, wn, wc, st)
    pos = {c:i for i,c in enumerate(df.columns)}
    linhas = list(cab)
    for _, row in df.iterrows():
        linha = [Paragraph(_html(row.iloc[0]), st['td']), Paragraph(_html(row.iloc[1]), st['nome'])]
        for c in bloco:
            valor = '' if c is None else _texto(row.iloc[pos[c]])
            linha.append(Paragraph(_html(valor), st['td']))
        linhas.append(linha)

    t = Table(linhas, colWidths=larguras, repeatRows=3, hAlign='LEFT')
    comandos = [
        ('BACKGROUND',(0,0),(1,2),AZUL), ('BACKGROUND',(2,0),(-1,0),CINZA_2),
        ('BACKGROUND',(2,1),(-1,1),AZUL_CLARO), ('BACKGROUND',(2,2),(-1,2),AZUL),
        ('BACKGROUND',(0,3),(1,-1),colors.white), ('BACKGROUND',(2,3),(-1,-1),CINZA_1),
        ('GRID',(0,0),(-1,-1),.35,CINZA_3), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(0,0),(-1,-1),'CENTER'), ('ALIGN',(1,3),(1,-1),'LEFT'),
        ('TOPPADDING',(0,0),(-1,-1),1.1), ('BOTTOMPADDING',(0,0),(-1,-1),1.1),
        ('LEFTPADDING',(0,0),(-1,-1),1.1), ('RIGHTPADDING',(0,0),(-1,-1),1.1),
    ]
    for j, c in enumerate(bloco, start=2):
        if c is None:
            continue
        tipo = _tipo_coluna(c)
        if tipo == 'FAL':
            comandos.append(('BACKGROUND',(j,2),(j,-1),FAL_BG))
        elif tipo == 'CON':
            comandos.append(('BACKGROUND',(j,2),(j,-1),CON_BG))
    t.setStyle(TableStyle(comandos))
    return t


def _rodape(canvas, doc):
    canvas.saveState()
    w, _ = landscape(A4)
    y = 5.5*mm
    canvas.setStrokeColor(CINZA_3)
    canvas.setLineWidth(.5)
    canvas.line(MARGEM_ESQ, y+4*mm, w-MARGEM_DIR, y+4*mm)
    canvas.setFont('Helvetica', 5.8)
    canvas.setFillColor(colors.HexColor('#66727E'))
    canvas.drawString(MARGEM_ESQ, y, 'CEP ETP — Matriz AFIN')
    canvas.drawRightString(w-MARGEM_DIR, y, f'Página {doc.page}')
    canvas.restoreState()


def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN em A4 paisagem."""
    if df_matriz is None:
        df_matriz = pd.DataFrame()
    if not isinstance(df_matriz, pd.DataFrame):
        raise TypeError('df_matriz deve ser um pandas.DataFrame.')
    if not df_matriz.empty and len(df_matriz.columns) < 2:
        raise ValueError('A matriz deve possuir pelo menos Matrícula e Estudante.')

    buffer = io.BytesIO()
    pagina = landscape(A4)
    w, _ = pagina
    largura_util = w - MARGEM_ESQ - MARGEM_DIR
    doc = SimpleDocTemplate(buffer, pagesize=pagina, leftMargin=MARGEM_ESQ, rightMargin=MARGEM_DIR,
                            topMargin=MARGEM_SUP, bottomMargin=MARGEM_INF,
                            title='Matriz AFIN', author='CEP ETP — Escola Técnica de Planaltina')
    st = _estilos()
    mapa = _mapa_iduc(mapa_nomes_iduc)
    colunas = list(df_matriz.columns[2:]) if not df_matriz.empty else []
    blocos = _blocos(colunas)

    largura_restante = largura_util - LARGURA_MATRICULA - LARGURA_ESTUDANTE
    largura_coluna = largura_restante / COLUNAS_MATRIZ_POR_PAGINA
    story = []

    for i, bloco in enumerate(blocos):
        if i:
            story.append(PageBreak())
        story.append(_topo(largura_util, st))
        story.append(Spacer(1, 2*mm))
        story.append(_identificacao(largura_util, turma, semestre, st))
        story.append(Spacer(1, 2*mm))
        story.append(_tabela(df_matriz, bloco, mapa, LARGURA_MATRICULA, LARGURA_ESTUDANTE, largura_coluna, st))

    doc.build(story, onFirstPage=_rodape, onLaterPages=_rodape)
    buffer.seek(0)
    return buffer.getvalue()
