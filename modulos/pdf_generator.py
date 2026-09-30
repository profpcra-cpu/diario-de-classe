# -*- coding: utf-8 -*-
import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def gerar_pdf_renovacao_matricula(dados_aluno):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Estilos
    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=14, alignment=1, textColor=colors.darkblue)
    texto_style = ParagraphStyle('TextoDoc', parent=styles['Normal'], fontSize=10, leading=14)
    negrito_style = ParagraphStyle('TextoNegrito', parent=texto_style, fontName='Helvetica-Bold')

    # Cabeçalho
    story.append(Paragraph("<b>INSTITUIÇÃO DE ENSINO TÉCNICO E PROFISSIONALIZANTE</b>", titulo_style))
    story.append(Paragraph("<b>SECRETARIA ACADÉMICA - FICHA DE RENOVAÇÃO DE MATRÍCULA</b>", titulo_style))
    story.append(Spacer(1, 15))

    # Tabela de Dados Pessoais
    nome = str(dados_aluno.get("nome", ""))
    matricula = str(dados_aluno.get("matricula", ""))
    curso = str(dados_aluno.get("curso", ""))
    turma = str(dados_aluno.get("turma", ""))
    rg = str(dados_aluno.get("identidade", dados_aluno.get("rg", "")))
    cpf = str(dados_aluno.get("cpf", ""))
    mae = str(dados_aluno.get("nome_mae", dados_aluno.get("mae", "")))
    pai = str(dados_aluno.get("nome_pai", dados_aluno.get("pai", "")))
    nasc = str(dados_aluno.get("data_nascimento", ""))

    dados_tabela = [
        [Paragraph(f"<b>Estudante:</b> {nome}", texto_style), Paragraph(f"<b>Matrícula:</b> {matricula}", texto_style)],
        [Paragraph(f"<b>Curso:</b> {curso}", texto_style), Paragraph(f"<b>Turma:</b> {turma}", texto_style)],
        [Paragraph(f"<b>RG:</b> {rg}", texto_style), Paragraph(f"<b>CPF:</b> {cpf}", texto_style)],
        [Paragraph(f"<b>Mãe:</b> {mae}", texto_style), Paragraph(f"<b>Pai:</b> {pai}", texto_style)],
        [Paragraph(f"<b>Data de Nascimento:</b> {nasc}", texto_style), Paragraph("", texto_style)]
    ]

    t = Table(dados_tabela, colWidths=[270, 270])
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Observações / Instruções
    obs = str(dados_aluno.get("observacao", "Renovação de matrícula referente ao período letivo."))
    story.append(Paragraph("<b>Termos e Instruções:</b>", negrito_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph(obs.replace("\n", "<br/>"), texto_style))
    story.append(Spacer(1, 40))

    # Assinaturas
    story.append(Paragraph("_" * 50, texto_style))
    story.append(Paragraph("Assinatura do Estudante ou Responsável Legal", texto_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_passe_estudantil(dados_aluno):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=14, alignment=1, textColor=colors.darkblue)
    texto_style = ParagraphStyle('TextoDoc', parent=styles['Normal'], fontSize=10, leading=14)

    story.append(Paragraph("<b>DECLARAÇÃO PARA PASSE ESTUDANTIL</b>", titulo_style))
    story.append(Spacer(1, 20))

    nome = str(dados_aluno.get("nome", ""))
    matricula = str(dados_aluno.get("matricula", ""))
    curso = str(dados_aluno.get("curso", ""))
    turma = str(dados_aluno.get("turma", ""))
    cpf = str(dados_aluno.get("cpf", ""))

    texto_declaracao = f"""
    Declaramos para os devidos fins de direito, junto à empresa de transporte público, que o(a) estudante <b>{nome}</b>, 
    inscrito(a) sob a matrícula <b>{matricula}</b>, portador(a) do CPF <b>{cpf}</b>, encontra-se regularmente matriculado(a) 
    e frequentando o curso <b>{curso}</b>, turma <b>{turma}</b>, nesta instituição de ensino.
    <br/><br/>
    A presente declaração é válida por 30 (trinta) dias a contar da data de sua emissão.
    """
    story.append(Paragraph(texto_declaracao, texto_style))
    story.append(Spacer(1, 60))

    story.append(Paragraph("Planaltina - DF, 29 de Setembro de 2026.", texto_style))
    story.append(Spacer(1, 40))
    story.append(Paragraph("_" * 40, texto_style))
    story.append(Paragraph("Secretaria Escolar", texto_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_declaracao_escolaridade(dados_aluno):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=14, alignment=1, textColor=colors.darkblue)
    texto_style = ParagraphStyle('TextoDoc', parent=styles['Normal'], fontSize=11, leading=16)

    story.append(Paragraph("<b>DECLARAÇÃO DE ESCOLARIDADE</b>", titulo_style))
    story.append(Spacer(1, 25))

    nome = str(dados_aluno.get("nome", ""))
    matricula = str(dados_aluno.get("matricula", ""))
    curso = str(dados_aluno.get("curso", ""))
    turma = str(dados_aluno.get("turma", ""))
    rg = str(dados_aluno.get("identidade", dados_aluno.get("rg", "")))

    texto_dec = f"""
    Declaramos para os devidos fins que o(a) aluno(a) <b>{nome}</b>, portador(a) da cédula de identidade RG nº <b>{rg}</b> 
    e matrícula nº <b>{matricula}</b>, está devidamente matriculado(a) e frequentando o curso <b>{curso}</b>, 
    nesta instituição, Turma <b>{turma}</b>.
    """
    story.append(Paragraph(texto_dec, texto_style))
    story.append(Spacer(1, 50))
    story.append(Paragraph("Secretaria Escolar", texto_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=13, alignment=1)
    texto_style = ParagraphStyle('TextoDoc', parent=styles['Normal'], fontSize=9)

    story.append(Paragraph("<b>HISTÓRICO ESCOLAR / REGISTO CURRICULAR</b>", titulo_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Aluno(a):</b> {dados_aluno.get('nome', '')} | <b>Matrícula:</b> {dados_aluno.get('matricula', '')}", texto_style))
    story.append(Spacer(1, 15))

    if not df_historico.empty:
        tabela_dados = [["Unidade Curricular", "Carga Horária", "Módulo", "Faltas"]]
        for _, row in df_historico.iterrows():
            tabela_dados.append([
                str(row.get("unidade_curricular", "")),
                str(row.get("carga_horaria", "")),
                str(row.get("modulo", "")),
                str(row.get("faltas", ""))
            ])
        t = Table(tabela_dados, colWidths=[240, 100, 100, 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------------------------------------------------------
# FUNÇÕES DE EMISSÃO UNIFICADA EM LOTE (TURMA INTEIRA)
# -------------------------------------------------------------------------

def gerar_pdf_passes_turma_unificado(df_turma):
    """Gera um único PDF contendo o passe estudantil de todos os alunos da turma (um por página)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=14, alignment=1, textColor=colors.darkblue)
    texto_style = ParagraphStyle('TextoDoc', parent=styles['Normal'], fontSize=11, leading=16)

    total_alunos = len(df_turma)
    for idx, (_, row) in enumerate(df_turma.iterrows()):
        aluno_dict = row.to_dict()
        nome = str(aluno_dict.get("nome", ""))
        matricula = str(aluno_dict.get("matricula", ""))
        curso = str(aluno_dict.get("curso", ""))
        turma = str(aluno_dict.get("turma", ""))
        cpf = str(aluno_dict.get("cpf", ""))

        story.append(Paragraph("<b>DECLARAÇÃO PARA PASSE ESTUDANTIL (LOTE)</b>", titulo_style))
        story.append(Spacer(1, 20))

        texto_declaracao = f"""
        Declaramos para os devidos fins de direito, junto à empresa de transporte público, que o(a) estudante <b>{nome}</b>, 
        inscrito(a) sob a matrícula <b>{matricula}</b>, portador(a) do CPF <b>{cpf}</b>, encontra-se regularmente matriculado(a) 
        e frequentando o curso <b>{curso}</b>, turma <b>{turma}</b>, nesta instituição de ensino.
        <br/><br/>
        A presente declaração é válida por 30 (trinta) dias a contar da data de sua emissão.
        """
        story.append(Paragraph(texto_declaracao, texto_style))
        story.append(Spacer(1, 60))

        story.append(Paragraph("Planaltina - DF, 29 de Setembro de 2026.", texto_style))
        story.append(Spacer(1, 40))
        story.append(Paragraph("_" * 40, texto_style))
        story.append(Paragraph("Secretaria Escolar", texto_style))

        # Adiciona quebra de página se não for o último aluno
        if idx < total_alunos - 1:
            story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_renovacao_turma_unificado(df_turma):
    """Gera um único PDF contendo a ficha de renovação de matrícula de todos os alunos da turma (uma por página)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontSize=14, alignment=1, textColor=colors.darkblue)
    texto_style = ParagraphStyle('TextoDoc', parent=styles['Normal'], fontSize=10, leading=14)
    negrito_style = ParagraphStyle('TextoNegrito', parent=texto_style, fontName='Helvetica-Bold')

    total_alunos = len(df_turma)
    for idx, (_, row) in enumerate(df_turma.iterrows()):
        aluno_dict = row.to_dict()
        
        story.append(Paragraph("<b>INSTITUIÇÃO DE ENSINO TÉCNICO E PROFISSIONALIZANTE</b>", titulo_style))
        story.append(Paragraph("<b>SECRETARIA ACADÉMICA - FICHA DE RENOVAÇÃO DE MATRÍCULA (LOTE)</b>", titulo_style))
        story.append(Spacer(1, 15))

        nome = str(aluno_dict.get("nome", ""))
        matricula = str(aluno_dict.get("matricula", ""))
        curso = str(aluno_dict.get("curso", ""))
        turma = str(aluno_dict.get("turma", ""))
        rg = str(aluno_dict.get("identidade", aluno_dict.get("rg", "")))
        cpf = str(aluno_dict.get("cpf", ""))
        mae = str(aluno_dict.get("nome_mae", aluno_dict.get("mae", "")))
        pai = str(aluno_dict.get("nome_pai", aluno_dict.get("pai", "")))
        nasc = str(aluno_dict.get("data_nascimento", ""))

        dados_tabela = [
            [Paragraph(f"<b>Estudante:</b> {nome}", texto_style), Paragraph(f"<b>Matrícula:</b> {matricula}", texto_style)],
            [Paragraph(f"<b>Curso:</b> {curso}", texto_style), Paragraph(f"<b>Turma:</b> {turma}", texto_style)],
            [Paragraph(f"<b>RG:</b> {rg}", texto_style), Paragraph(f"<b>CPF:</b> {cpf}", texto_style)],
            [Paragraph(f"<b>Mãe:</b> {mae}", texto_style), Paragraph(f"<b>Pai:</b> {pai}", texto_style)],
            [Paragraph(f"<b>Data de Nascimento:</b> {nasc}", texto_style), Paragraph("", texto_style)]
        ]

        t = Table(dados_tabela, colWidths=[270, 270])
        t.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.grey),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        obs = "1. Deseja renovar a matrícula para o próximo semestre? [ X ] Sim [  ] Não\n2. Está cursando o Ensino Médio atualmente? [ X ] Sim [  ] Não\nA renovação de matrícula não é automática."
        story.append(Paragraph("<b>Termos e Instruções:</b>", negrito_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(obs.replace("\n", "<br/>"), texto_style))
        story.append(Spacer(1, 40))

        story.append(Paragraph("_" * 50, texto_style))
        story.append(Paragraph("Assinatura do Estudante ou Responsável Legal", texto_style))

        if idx < total_alunos - 1:
            story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
