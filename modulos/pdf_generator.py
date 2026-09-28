import io
import os
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from modulos.conexao import executar_query


def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """
    Gera o Histórico Escolar em A4, com diagramação institucional,
    alinhamento rigoroso de colunas e primeira coluna ampliada.
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
        rowHeights=[51]
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
            rowHeights=[17]
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
        t = Table(linhas, colWidths=larguras)
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

    # Identificação Acadêmica
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
    story.append(tabela_campos(identificacao, [330, 95, 129]))
    story.append(Spacer(1, 4))

    # Dados do Estudante
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
    story.append(tabela_campos(dados_estudante, [285, 150, 119]))
    story.append(Spacer(1, 4))

    # Base Legal
    story.append(bloco_secao("BASE LEGAL"))
    base_legal = Table(
        [[Paragraph(base_legal_texto, estilo_valor)]],
        colWidths=[554]
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
    # HISTÓRICO ACADÊMICO
    # Primeira coluna ampliada para 314 pt; demais colunas reduzidas proporcionalmente.
    # Total somando exatamente 554 pt.
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
            sem = str(row.get("semestre", ""))
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
    # RESUMO / LEGENDA
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
        colWidths=[350, 102, 102]
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

    story.append(rodape_legenda)
    story.append(Spacer(1, 9))

    # ------------------------------------------------------------------
    # LOCAL / DATA
    # ------------------------------------------------------------------
    data_documento = "PLANALTINA-DF, 27 DE SETEMBRO DE 2026"
    data_tabela = Table(
        [[Paragraph(data_documento, estilo_assinatura)]],
        colWidths=[554]
    )
    data_tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(data_tabela)
    story.append(Spacer(1, 23))

    # ------------------------------------------------------------------
    # ASSINATURAS
    # ------------------------------------------------------------------
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
        rowHeights=[43]
    )

    assinatura.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(assinatura)

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




def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN em formato paisagem com a nova paleta de cores e colunas compactas."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    story = []
    
    styles = getSampleStyleSheet()
    
    estilo_topo = ParagraphStyle(
        'TopoAFIN',
        parent=styles['Heading1'],
        fontSize=10,
        alignment=1,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold'
    )
    
    estilo_info_label = ParagraphStyle(
        'InfoLabelAFIN',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        textColor=colors.HexColor("#1A202C"),
        fontName='Helvetica-Bold'
    )

    estilo_info_val = ParagraphStyle(
        'InfoValAFIN',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,
        textColor=colors.HexColor("#1A202C"),
        fontName='Helvetica-Bold'
    )
    
    estilo_th = ParagraphStyle(
        'THAFIN',
        parent=styles['Normal'],
        fontSize=6,
        alignment=1,
        textColor=colors.HexColor("#1A202C"),
        fontName='Helvetica-Bold'
    )

    estilo_th_top = ParagraphStyle(
        'THAffinTop',
        parent=styles['Normal'],
        fontSize=6,
        alignment=1,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold'
    )
    
    estilo_td = ParagraphStyle(
        'TDAFIN',
        parent=styles['Normal'],
        fontSize=7,
        alignment=1,
        textColor=colors.HexColor("#2D3748"),
        fontName='Helvetica'
    )

    estilo_td_nome = ParagraphStyle(
        'TDAFINNome',
        parent=styles['Normal'],
        fontSize=7,
        alignment=0,
        textColor=colors.HexColor("#2D3748"),
        fontName='Helvetica'
    )

    largura_total = 762  # 792 - 30 de margens
    larg_matr = 65
    larg_nome = 150
    
    colunas_originais = list(df_matriz.columns) if df_matriz is not None and not df_matriz.empty else []
    num_disciplinas = max(1, (len(colunas_originais) - 2) // 2)
    
    larg_restante = largura_total - (larg_matr + larg_nome)
    larg_dupla = larg_restante / num_disciplinas
    larg_col_uc = larg_dupla / 2.0

    # 1. Cabeçalho Superior Institucional (Azul Real)[cite: 7]
    tabela_topo = Table([
        [Paragraph("<b>SEEDF &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CEP ETP - AFIN &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CURSO: TÉCNICO EM SECRETARIA ESCOLAR</b>", estilo_topo)]
    ], colWidths=[largura_total])
    
    tabela_topo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0000CC")), # Azul Real Forte
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(tabela_topo)
    story.append(Spacer(1, 2))

    # 2. Informações de Semestre e Turma (Fundo Creme/Amarelado)[cite: 7]
    tabela_info = Table([
        [Paragraph("SEMESTRE", estilo_info_label), Paragraph(f"<b>{semestre}</b>", estilo_info_val)],
        [Paragraph("TURMA", estilo_info_label), Paragraph(f"<b>{turma}</b>", estilo_info_val)]
    ], colWidths=[larg_matr, larg_nome + larg_restante])
    
    tabela_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#FFFBEB")), # Tom Creme Suave nas labels
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#FEF3C7")), # Tom Amarelado Suave nos valores
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tabela_info)
    story.append(Spacer(1, 2))

    # 3. Construção das linhas de cabeçalho da matriz
    header_linha_disc = [Paragraph("<b>MATRÍCULA</b>", estilo_th_top), Paragraph("<b>ESTUDANTE</b>", estilo_th_top)]
    header_linha_iduc = [Paragraph("", estilo_th_top), Paragraph("", estilo_th_top)]
    header_linha_tipo = [Paragraph("<b>FAL</b>", estilo_th_top), Paragraph("<b>CON</b>", estilo_th_top)]
    
    col_widths = [larg_matr, larg_nome]
    span_commands = [
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (1, 2)),
    ]

    i = 2
    col_idx_atual = 2
    while i < len(colunas_originais):
        col_name = colunas_originais[i]
        if " - FAL" in col_name:
            nome_uc = col_name.replace(" - FAL", "")
            iduc_str = ""
            if mapa_nomes_iduc:
                for k, v in mapa_nomes_iduc.items():
                    if v == nome_uc:
                        iduc_str = k
                        break
            
            header_linha_disc.extend([Paragraph(f"<b>{nome_uc}</b>", estilo_th), Paragraph("", estilo_th)])
            header_linha_iduc.extend([Paragraph(f"<b>{iduc_str}</b>", estilo_th), Paragraph("", estilo_th)])
            header_linha_tipo.extend([Paragraph("<b>F</b>", estilo_th), Paragraph("<b>C</b>", estilo_th)])
            
            span_commands.append(('SPAN', (col_idx_atual, 0), (col_idx_atual + 1, 0)))
            span_commands.append(('SPAN', (col_idx_atual, 1), (col_idx_atual + 1, 1)))
            
            col_widths.extend([larg_col_uc, larg_col_uc])
            col_idx_atual += 2
            i += 2
        else:
            i += 1

    dados_tabela = [header_linha_disc, header_linha_iduc, header_linha_tipo]

    if df_matriz is not None:
        for _, row in df_matriz.iterrows():
            linha_dados = [
                Paragraph(str(row.iloc[0]), estilo_td),
                Paragraph(str(row.iloc[1]), estilo_td_nome)
            ]
            for col_idx in range(2, len(row)):
                val = row.iloc[col_idx]
                val_str = str(val) if pd.notnull(val) and str(val) != 'nan' else ""
                linha_dados.append(Paragraph(val_str, estilo_td))
            dados_tabela.append(linha_dados)

    tabela_matriz = Table(dados_tabela, repeatRows=3, colWidths=col_widths)
    
    # Estilização com cinza claro elegante para as disciplinas e margens compactas
    estilo_tabela_base = [
        ('BACKGROUND', (0, 0), (1, 2), colors.HexColor("#E2E8F0")), # Cinza Azulado para Matrícula/Estudante
        ('TEXTCOLOR', (0, 0), (1, 2), colors.HexColor("#1A202C")),
        ('BACKGROUND', (2, 0), (-1, 1), colors.HexColor("#EDF2F7")), # Cinza claro limpo para disciplinas e IDs[cite: 7]
        ('BACKGROUND', (2, 2), (-1, 2), colors.HexColor("#E2E8F0")), # Cinza para colunas F e C
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('BACKGROUND', (0, 3), (1, -1), colors.HexColor("#FFFFFF")),
        ('BACKGROUND', (2, 3), (-1, -1), colors.HexColor("#F8FAFC")),
    ]
    
    tabela_matriz.setStyle(TableStyle(estilo_tabela_base + span_commands))
    
    story.append(tabela_matriz)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
