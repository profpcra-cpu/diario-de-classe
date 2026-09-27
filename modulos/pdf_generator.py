from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

def gerar_pdf_afin(df_matriz, turma, semestre):
    buffer = io.BytesIO()
    # Usamos formato paisagem (landscape) devido à quantidade de colunas (FAL e CON por disciplina)
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'TituloInstituicao',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1, # Centralizado
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'SubInstituicao',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15
    )
    
    # Cabeçalho Oficial
    story.append(Paragraph("CEP ESCOLA TÉCNICA DE PLANALTINA - AFIN", titulo_style))
    story.append(Paragraph(f"Acompanhamento da Frequência e Conceito — Turma: {turma} | Semestre: {semestre}", sub_style))
    story.append(Spacer(1, 10))
    
    # Preparar dados para a tabela do ReportLab
    # Converter colunas e dados do DataFrame para listas de strings
    headers = list(df_matriz.columns)
    dados_tabela = [headers]
    
    for _, row in df_matriz.iterrows():
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
