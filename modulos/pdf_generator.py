import io
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """
    Gera o PDF do Histórico Escolar do Aluno.
    Garante compatibilidade caso os parâmetros venham invertidos (dicionário vs dataframe).
    """
    # Proteção caso a ordem dos argumentos tenha sido invertida na chamada
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'TituloInstituicao',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=1,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'SubInstituicao',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15
    )
    
    # Extrair nome e matrícula de forma segura (seja dicionário ou série)
    nome_aluno = ""
    matricula_aluno = ""
    if isinstance(dados_aluno, dict):
        nome_aluno = dados_aluno.get('nome', '')
        matricula_aluno = dados_aluno.get('matricula', '')
    elif hasattr(dados_aluno, 'iloc') and not dados_aluno.empty:
        nome_aluno = str(dados_aluno.iloc[0].get('nome', ''))
        matricula_aluno = str(dados_aluno.iloc[0].get('matricula', ''))

    story.append(Paragraph("CEP ESCOLA TÉCNICA DE PLANALTINA - HISTÓRICO ESCOLAR", titulo_style))
    story.append(Paragraph(f"Aluno: {nome_aluno} | Matrícula: {matricula_aluno}", sub_style))
    story.append(Spacer(1, 10))
    
    if df_historico is not None and not df_historico.empty:
        headers = list(df_historico.columns)
        dados_tabela = [headers]
        for _, row in df_historico.iterrows():
            dados_tabela.append([str(val) if pd.notnull(val) else "" for val in row])
            
        tabela = Table(dados_tabela, repeatRows=1)
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
        ]))
        story.append(tabela)
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN em formato paisagem perfeitamente estruturado."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
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
    
    estilo_info = ParagraphStyle(
        'InfoAFIN',
        parent=styles['Normal'],
        fontSize=9,
        alignment=0,
        textColor=colors.HexColor("#1A202C"),
        fontName='Helvetica-Bold'
    )
    
    estilo_th = ParagraphStyle(
        'THAFIN',
        parent=styles['Normal'],
        fontSize=6.5,
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

    largura_total = 742
    larg_matr = 65
    larg_nome = 175
    
    colunas_originais = list(df_matriz.columns) if df_matriz is not None and not df_matriz.empty else []
    num_disciplinas = max(1, (len(colunas_originais) - 2) // 2)
    
    larg_restante = largura_total - (larg_matr + larg_nome)
    larg_dupla = larg_restante / num_disciplinas
    larg_col_uc = larg_dupla / 2.0

    # 1. Cabeçalho Institucional Superior (Faixa Azul)
    tabela_topo = Table([
        [Paragraph("SEEDF &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CEP ETP - AFIN &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CURSO: TÉCNICO EM SECRETARIA ESCOLAR", estilo_topo)]
    ], colWidths=[largura_total])
    
    tabela_topo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1A365D")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(tabela_topo)
    story.append(Spacer(1, 4))

    # 2. Informações de Semestre e Turma
    tabela_info = Table([
        [Paragraph(f"SEMESTRE: {semestre}", estilo_info), Paragraph(f"TURMA: {turma}", estilo_info)]
    ], colWidths=[largura_total / 2.0, largura_total / 2.0])
    tabela_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEFCBF")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ECC94B")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tabela_info)
    story.append(Spacer(1, 6))

    # 3. Construção do Cabeçalho Multinível
    header_linha_disc = [Paragraph("<b>MATRÍCULA</b>", estilo_th), Paragraph("<b>ESTUDANTE</b>", estilo_th)]
    header_linha_iduc = [Paragraph("", estilo_th), Paragraph("", estilo_th)]
    header_linha_tipo = [Paragraph("", estilo_th), Paragraph("", estilo_th)]
    
    col_widths = [larg_matr, larg_nome]

    i = 2
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
            header_linha_tipo.extend([Paragraph("<b>FAL</b>", estilo_th), Paragraph("<b>CON</b>", estilo_th)])
            
            col_widths.extend([larg_col_uc, larg_col_uc])
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
    
    tabela_matriz.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 2), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 2), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 3), (1, -1), colors.HexColor("#FFFFFF")),
        ('BACKGROUND', (2, 3), (-1, -1), colors.HexColor("#F7FAFC")),
    ]))
    
    story.append(tabela_matriz)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
