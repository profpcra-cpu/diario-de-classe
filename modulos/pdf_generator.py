import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

def gerar_pdf_historico_aluno(dados_aluno, df_historico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    title_style = ParagraphStyle('TitleStyle', parent=normal_style, fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=1)
    sub_title_style = ParagraphStyle('SubTitleStyle', parent=normal_style, fontName='Helvetica', fontSize=7, leading=9, alignment=1)
    doc_title_style = ParagraphStyle('DocTitleStyle', parent=normal_style, fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1)
    cell_style = ParagraphStyle('CellStyle', parent=normal_style, fontName='Helvetica', fontSize=7, leading=9)
    cell_bold = ParagraphStyle('CellBold', parent=normal_style, fontName='Helvetica-Bold', fontSize=7, leading=9)
    cell_center = ParagraphStyle('CellCenter', parent=normal_style, fontName='Helvetica', fontSize=7, leading=9, alignment=1)
    cell_center_bold = ParagraphStyle('CellCenterBold', parent=normal_style, fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=1)

    elements = []

    # Carregamento das Logos da Raiz do Repositório
    try:
        logo_gdf = Image("logo_gdf.png", width=2.0 * cm, height=1.8 * cm)
        logo_gdf.hAlign = 'CENTER'
    except:
        logo_gdf = Paragraph("<b>[Logo GDF]</b>", cell_center)

    try:
        logo_escola = Image("logo_escola.png", width=2.0 * cm, height=1.8 * cm)
        logo_escola.hAlign = 'CENTER'
    except:
        logo_escola = Paragraph("<b>[Logo Escola]</b>", cell_center)

    header_text = [
        Paragraph("Governo do Distrito Federal", title_style),
        Paragraph("Secretaria de Estado de Educação", sub_title_style),
        Paragraph("Subsecretaria de Educação Básica", sub_title_style),
        Paragraph("Coordenação Regional de Ensino de Planaltina", sub_title_style),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina", sub_title_style),
        Spacer(1, 0.2 * cm),
        Paragraph("HISTÓRICO ESCOLAR", doc_title_style)
    ]

    header_table = Table([[logo_gdf, header_text, logo_escola]], colWidths=[3.0 * cm, 12.0 * cm, 3.0 * cm])
    header_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.1 * cm))

    nome_aluno = dados_aluno.get('nome', 'N/D')
    mat_aluno = dados_aluno.get('matricula', 'N/D')
    turma_aluno = dados_aluno.get('turma', 'N/D')
    sexo_aluno = dados_aluno.get('sexo', 'N/D')
    
    data_ident = [
        [Paragraph("<b>Curso:</b> TÉCNICO EM SECRETARIADO ESCOLAR", cell_style), "", "", ""],
        [Paragraph(f"<b>Matrícula:</b> {mat_aluno}", cell_style), Paragraph(f"<b>Turma/ Turno:</b> {turma_aluno}", cell_style), Paragraph(f"<b>Nome:</b> {nome_aluno}", cell_style), Paragraph(f"<b>Sexo:</b> {sexo_aluno}", cell_style)],
        [Paragraph("<b>Nome da Mãe:</b> -", cell_style), "", "", ""],
        [Paragraph("<b>Nome do Pai:</b> -", cell_style), "", "", ""],
        [Paragraph("<b>Data de Nasc.:</b> -", cell_style), Paragraph("<b>Nacionalidade:</b> BRASILEIRA", cell_style), Paragraph("<b>Naturalidade:</b> -", cell_style), Paragraph("<b>UF:</b> DF", cell_style)],
        [Paragraph("<b>RG/CPF/CNH:</b> -", cell_style), Paragraph("<b>Órgão Expedidor:</b> -", cell_style), Paragraph("<b>Data de Expedição:</b> -", cell_style), Paragraph("", cell_style)],
        [Paragraph("<b>Base Legal:</b> LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 02/2023 - CEDF", cell_style), "", "", ""]
    ]

    t_ident = Table(data_ident, colWidths=[4.5 * cm, 4.5 * cm, 6.0 * cm, 3.0 * cm])
    t_ident.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('SPAN', (0,0), (3,0)),
        ('SPAN', (0,2), (3,2)),
        ('SPAN', (0,3), (3,3)),
        ('SPAN', (0,6), (3,6)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_ident)
    elements.append(Spacer(1, 0.1 * cm))

    header_comp = [
        Paragraph("<b>Componente Curricular (Unidade Curricular)</b>", cell_bold),
        Paragraph("<b>Semestre</b>", cell_center_bold),
        Paragraph("<b>C/H</b>", cell_center_bold),
        Paragraph("<b>Módulo</b>", cell_center_bold),
        Paragraph("<b>Faltas</b>", cell_center_bold),
        Paragraph("<b>Resultado</b>", cell_center_bold)
    ]

    components_data = [header_comp]
    
    if df_historico.empty:
        components_data.append([Paragraph("Sem registos curriculares", cell_style), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center)])
    else:
        for _, row in df_historico.iterrows():
            components_data.append([
                Paragraph(str(row.get('unidade_curricular', '')), cell_style),
                Paragraph(str(row.get('semestre', '')), cell_center),
                Paragraph(str(row.get('carga_horaria', '')), cell_center),
                Paragraph(str(row.get('modulo', '')), cell_center),
                Paragraph(str(row.get('faltas', '')), cell_center),
                Paragraph(str(row.get('conceito', '')), cell_center)
            ])

    t_comp = Table(components_data, colWidths=[9.0 * cm, 2.5 * cm, 1.5 * cm, 2.0 * cm, 1.5 * cm, 1.5 * cm])
    t_comp.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(t_comp)
    elements.append(Spacer(1, 0.1 * cm))

    footer_data = [
        [Paragraph("AP = Aprovado; AE = Aproveitamento de Estudos; NA = Não Apto", cell_style), Paragraph("<b>T. Teoria:</b> 1.353", cell_style), Paragraph("<b>T. Prática:</b> 0", cell_style)],
        [Paragraph("PLANALTINA-DF, 26/09/2026", cell_style), "", ""],
        [Paragraph("", cell_style), "", ""],
        [Paragraph("", cell_style), "", ""],
        [Paragraph("DIRETOR", cell_center_bold), "", Paragraph("SECRETÁRIO(A) ESCOLAR", cell_center_bold)]
    ]

    t_footer = Table(footer_data, colWidths=[9.0 * cm, 4.5 * cm, 4.5 * cm])
    t_footer.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('SPAN', (0,0), (0,0)),
        ('SPAN', (0,1), (2,1)),
        ('SPAN', (0,2), (2,2)),
        ('SPAN', (0,3), (2,3)),
        ('SPAN', (1,4), (2,4)),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_footer)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
