import io
import os
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """Gera o PDF do Histórico Escolar do Aluno rigorosamente idêntico ao modelo oficial com logotipos."""
    # Proteção caso os argumentos venham invertidos
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()
    # Margens ajustadas para documento retrato (Letter)
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    story = []
    
    styles = getSampleStyleSheet()
    
    estilo_cab_gov = ParagraphStyle(
        'CabGov',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1, # Centralizado
        textColor=colors.HexColor("#1A202C"),
        fontName='Helvetica-Bold',
        spaceAfter=1
    )
    
    estilo_titulo_he = ParagraphStyle(
        'TituloHE',
        parent=styles['Heading1'],
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor("#1A365D"),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    estilo_label = ParagraphStyle(
        'LabelHE',
        parent=styles['Normal'],
        fontSize=6,
        textColor=colors.HexColor("#4A5568"),
        fontName='Helvetica-Bold'
    )
    
    estilo_val = ParagraphStyle(
        'ValHE',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor("#1A202C"),
        fontName='Helvetica'
    )

    estilo_th = ParagraphStyle(
        'THHE',
        parent=styles['Normal'],
        fontSize=7,
        alignment=1,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold'
    )

    estilo_td = ParagraphStyle(
        'TDHE',
        parent=styles['Normal'],
        fontSize=7,
        alignment=1,
        textColor=colors.HexColor("#2D3748"),
        fontName='Helvetica'
    )

    estilo_td_left = ParagraphStyle(
        'TDHELeft',
        parent=styles['Normal'],
        fontSize=7,
        alignment=0,
        textColor=colors.HexColor("#2D3748"),
        fontName='Helvetica'
    )

    # 1. Carregamento seguro dos logotipos (se disponíveis no diretório raiz do projeto)
    path_logo_gdf = "logo_gdf.png"
    path_logo_escola = "logo_escola.png"
    
    img_gdf = Image(path_logo_gdf, width=45, height=45) if os.path.exists(path_logo_gdf) else Paragraph("", estilo_val)
    img_escola = Image(path_logo_escola, width=45, height=45) if os.path.exists(path_logo_escola) else Paragraph("", estilo_val)

    texto_institucional = [
        Paragraph("Governo do Distrito Federal", estilo_cab_gov),
        Paragraph("Secretaria de Estado de Educação", estilo_cab_gov),
        Paragraph("Subsecretaria de Educação Básica", estilo_cab_gov),
        Paragraph("Coordenação Regional de Ensino de Planaltina", estilo_cab_gov),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina", estilo_cab_gov),
    ]

    tabela_cabecalho_topo = Table([
        [img_gdf, texto_institucional, img_escola]
    ], colWidths=[60, 442, 60])
    
    tabela_cabecalho_topo.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(tabela_cabecalho_topo)
    story.append(Spacer(1, 4))
    story.append(Paragraph("HISTÓRICO ESCOLAR", estilo_titulo_he))
    
    # Extrair dados do aluno com segurança
    if isinstance(dados_aluno, dict):
        d = dados_aluno
    elif hasattr(dados_aluno, 'iloc') and not dados_aluno.empty:
        d = dados_aluno.iloc[0].to_dict()
    else:
        d = {}

    curso = str(d.get('curso', 'TÉCNICO REGISTRO E INFORMAÇÃO EM SAÚDE'))
    matricula = str(d.get('matricula', d.get('matrícula', '')))
    turma = str(d.get('turma', ''))
    nome = str(d.get('nome', ''))
    cpf = str(d.get('cpf', '87488014187'))
    sexo = str(d.get('sexo', 'FEMININO'))
    mae = str(d.get('mae', d.get('nome_mae', 'Luiza do Nascimento Montezuma')))
    pai = str(d.get('pai', d.get('nome_pai', 'Diomedio Montezuma')))
    dt_nasc = str(d.get('data_nascimento', '30/07/1980'))
    nacionalidade = str(d.get('nacionalidade', 'Brasileira'))
    naturalidade = str(d.get('naturalidade', 'Brasília'))
    uf = str(d.get('uf', 'DF'))
    rg = str(d.get('rg', '1804433'))
    orgao = str(d.get('orgao_expeditor', 'SSP/DF'))
    dt_exp = str(d.get('data_expedicao', '07/07/2012'))

    # 2. Tabela de Dados Cadastrais
    dados_cadastrais = [
        [Paragraph("Curso", estilo_label), Paragraph(f"<b>{curso}</b>", estilo_val), Paragraph("", estilo_val), Paragraph("", estilo_val)],
        [Paragraph("Matrícula", estilo_label), Paragraph("Turma/ Turno", estilo_label), Paragraph("Nome", estilo_label), Paragraph("CPF / Sexo", estilo_label)],
        [Paragraph(matricula, estilo_val), Paragraph(turma, estilo_val), Paragraph(f"<b>{nome}</b>", estilo_val), Paragraph(f"{cpf} — {sexo}", estilo_val)],
        [Paragraph("Nome da Mãe:", estilo_label), Paragraph(mae, estilo_val), Paragraph("", estilo_val), Paragraph("", estilo_val)],
        [Paragraph("Nome do Pai:", estilo_label), Paragraph(pai, estilo_val), Paragraph("", estilo_val), Paragraph("", estilo_val)],
        [Paragraph("Data de Nascimento", estilo_label), Paragraph("Nacionalidade", estilo_label), Paragraph("Naturalidade / UF", estilo_label), Paragraph("CPF/RG / Órgão / Data", estilo_label)],
        [Paragraph(dt_nasc, estilo_val), Paragraph(nacionalidade, estilo_val), Paragraph(f"{naturalidade} / {uf}", estilo_val), Paragraph(f"{rg} {orgao} {dt_exp}", estilo_val)],
        [Paragraph("<b>Base Legal:</b>", estilo_label), Paragraph("<b>LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 02/2023 - CEDF, PARECER Nº 222/2016 -CEDF, PORTARIA Nº 456/2016 SEDF</b>", estilo_label), Paragraph("", estilo_label), Paragraph("", estilo_label)]
    ]
    
    t_cad = Table(dados_cadastrais, colWidths=[110, 120, 200, 132])
    t_cad.setStyle(TableStyle([
        ('SPAN', (1, 0), (3, 0)),
        ('SPAN', (1, 3), (3, 3)),
        ('SPAN', (1, 4), (3, 4)),
        ('SPAN', (1, 7), (3, 7)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story.append(t_cad)
    story.append(Spacer(1, 4))

    # 3. Tabela de Componentes Curriculares (Histórico)
    header_hist = [
        Paragraph("<b>Componente Curricular</b>", estilo_th),
        Paragraph("<b>Semestre</b>", estilo_th),
        Paragraph("<b>CH</b>", estilo_th),
        Paragraph("<b>Módulo</b>", estilo_th),
        Paragraph("<b>Faltas</b>", estilo_th),
        Paragraph("<b>Resultado</b>", estilo_th)
    ]
    
    tabela_hist_dados = [header_hist]
    
    if df_historico is not None and not df_historico.empty:
        for _, row in df_historico.iterrows():
            comp = str(row.get('unidade_curricular', row.get('componente', row.get('disciplina', '---'))))
            sem = str(row.get('semestre', '2026/2º'))
            ch = str(row.get('carga_horaria', row.get('ch', '40')))
            mod = str(row.get('modulo', 'Teoria'))
            faltas = str(row.get('faltas', '0'))
            res = str(row.get('resultado', row.get('conceito', 'AP')))
            
            tabela_hist_dados.append([
                Paragraph(comp, estilo_td_left),
                Paragraph(sem, estilo_td),
                Paragraph(ch, estilo_td),
                Paragraph(mod, estilo_td),
                Paragraph(faltas, estilo_td),
                Paragraph(res, estilo_td)
            ])
            
    t_hist = Table(tabela_hist_dados, repeatRows=1, colWidths=[242, 70, 50, 70, 60, 70])
    t_hist.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
    ]))
    
    story.append(t_hist)
    story.append(Spacer(1, 4))

    # 4. Rodapé Oficial, Legendas e Assinaturas
    rodape_dados = [
        [Paragraph("<b>AP = Apto; AE = Aprov. de Estudos; NA = Não Apto; TR = Tranc. de Curso; D = Desistente</b>", estilo_label),  
         Paragraph("<b>T. Teoria:</b> 1.366", estilo_val),  
         Paragraph("<b>T. Prática:</b> 0", estilo_val)],
        [Paragraph("<b>PLANALTINA-DF, &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 27/09/2026</b>", estilo_val), Paragraph("", estilo_val), Paragraph("", estilo_val)],
        [Paragraph("<br/><br/>________________________________________<br/><b>DIRETOR</b>", estilo_th), Paragraph("", estilo_th), Paragraph("<br/><br/>________________________________________<br/><b>SECRETÁRIO(A) ESCOLAR</b>", estilo_th)]
    ]
    
    t_rod = Table(rodape_dados, colWidths=[312, 125, 125])
    t_rod.setStyle(TableStyle([
        ('SPAN', (0, 1), (2, 1)),
        ('SPAN', (0, 2), (2, 2)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    story.append(t_rod)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    """Gera o PDF consolidado da Matriz AFIN em formato paisagem com layout idêntico à planilha oficial."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
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

    largura_total = 752  # Largura útil em paisagem (792 - 40 de margens)
    larg_matr = 60
    larg_nome = 160
    
    colunas_originais = list(df_matriz.columns) if df_matriz is not None and not df_matriz.empty else []
    num_disciplinas = max(1, (len(colunas_originais) - 2) // 2)
    
    larg_restante = largura_total - (larg_matr + larg_nome)
    larg_dupla = larg_restante / num_disciplinas
    larg_col_uc = larg_dupla / 2.0

    # 1. Cabeçalho Superior Institucional
    tabela_topo = Table([
        [Paragraph("SEEDF &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CEP ETP - AFIN &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; CURSO: TÉCNICO EM SECRETARIA ESCOLAR", estilo_topo)]
    ], colWidths=[largura_total])
    
    tabela_topo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#1A365D")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(tabela_topo)
    story.append(Spacer(1, 3))

    # 2. Informações de Semestre e Turma
    tabela_info = Table([
        [Paragraph(f"SEMESTRE: {semestre}", estilo_info), Paragraph(f"TURMA: {turma}", estilo_info)]
    ], colWidths=[largura_total / 2.0, largura_total / 2.0])
    tabela_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEFCBF")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ECC94B")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tabela_info)
    story.append(Spacer(1, 4))

    # 3. Construção das linhas de cabeçalho da matriz
    header_linha_disc = [Paragraph("<b>MATRÍCULA</b>", estilo_th), Paragraph("<b>ESTUDANTE</b>", estilo_th)]
    header_linha_iduc = [Paragraph("", estilo_th), Paragraph("", estilo_th)]
    header_linha_tipo = [Paragraph("", estilo_th), Paragraph("", estilo_th)]
    
    col_widths = [larg_matr, larg_nome]
    span_commands = [
        # Span vertical para MATRÍCULA e ESTUDANTE cobrindo as 3 linhas do cabeçalho
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
            
            # Adicionar células para FAL e CON
            header_linha_disc.extend([Paragraph(f"<b>{nome_uc}</b>", estilo_th), Paragraph("", estilo_th)])
            header_linha_iduc.extend([Paragraph(f"<b>{iduc_str}</b>", estilo_th), Paragraph("", estilo_th)])
            header_linha_tipo.extend([Paragraph("<b>FAL</b>", estilo_th), Paragraph("<b>CON</b>", estilo_th)])
            
            # Span horizontal unindo as duas colunas (FAL e CON) para o nome da UC e para o IDUC
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
    
    # Estilização completa da tabela e aplicação dos SPANs calculados
    estilo_tabela_base = [
        ('BACKGROUND', (0, 0), (-1, 2), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0, 0), (-1, 2), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('BACKGROUND', (0, 3), (1, -1), colors.HexColor("#FFFFFF")),
        ('BACKGROUND', (2, 3), (-1, -1), colors.HexColor("#F7FAFC")),
    ]
    
    tabela_matriz.setStyle(TableStyle(estilo_tabela_base + span_commands))
    
    story.append(tabela_matriz)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
