from datetime import datetime
import io
import os
import re
import pandas as pd

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from modulos.conexao import executar_query


# ============================================================
# 1. HISTÓRICO ESCOLAR
# ============================================================

def gerar_pdf_historico_aluno(df_historico, dados_aluno):
    """
    Gera o Histórico Escolar em A4, com diagramação institucional,
    alinhamento rigoroso de colunas (todas somando exatamente 554 pt)
    e limpeza de campos acadêmicos quando o semestre não estiver lançado.
    """
    if isinstance(df_historico, dict) and isinstance(dados_aluno, pd.DataFrame):
        df_historico, dados_aluno = dados_aluno, df_historico

    buffer = io.BytesIO()

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

    CINZA_TEXTO = colors.HexColor("#263238")
    CINZA_MEDIO = colors.HexColor("#5F6B72")
    CINZA_LINHA = colors.HexColor("#C8CED2")
    CINZA_CAB = colors.HexColor("#E7EAEC")
    PRETO = colors.HexColor("#111111")

    estilo_institucional = ParagraphStyle(
        "Institucional", parent=styles["Normal"], fontName="Helvetica", fontSize=7.3, leading=8.4, alignment=TA_CENTER, textColor=PRETO
    )
    estilo_institucional_bold = ParagraphStyle(
        "InstitucionalBold", parent=estilo_institucional, fontName="Helvetica-Bold", fontSize=7.5, leading=8.7
    )
    estilo_titulo = ParagraphStyle(
        "TituloHistorico", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=16, alignment=TA_CENTER, textColor=PRETO, spaceBefore=5, spaceAfter=7
    )
    estilo_secao = ParagraphStyle(
        "Secao", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=8.5, alignment=TA_LEFT, textColor=PRETO
    )
    estilo_label = ParagraphStyle(
        "Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=6.2, leading=7, textColor=CINZA_MEDIO
    )
    estilo_valor = ParagraphStyle(
        "Valor", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=8.7, textColor=CINZA_TEXTO
    )
    estilo_valor_bold = ParagraphStyle(
        "ValorBold", parent=estilo_valor, fontName="Helvetica-Bold", textColor=PRETO
    )
    estilo_th = ParagraphStyle(
        "TH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=6.8, leading=7.6, alignment=TA_CENTER, textColor=PRETO
    )
    estilo_td = ParagraphStyle(
        "TD", parent=styles["Normal"], fontName="Helvetica", fontSize=6.9, leading=7.7, alignment=TA_CENTER, textColor=CINZA_TEXTO
    )
    estilo_td_left = ParagraphStyle("TDLeft", parent=estilo_td, alignment=TA_LEFT)
    estilo_rodape = ParagraphStyle("Rodape", parent=styles["Normal"], fontName="Helvetica", fontSize=6.5, leading=7.7, textColor=CINZA_MEDIO)
    estilo_assinatura = ParagraphStyle("Assinatura", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=8, alignment=TA_CENTER, textColor=PRETO)

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

    base_legal_texto = "LEI Nº 9.394/96, DECRETO Nº 5.154/2004, RESOLUÇÃO Nº 02/2023 - CEDF"
    if sigla and turma:
        try:
            df_bl = executar_query("SELECT base_legal FROM TB_BASE_LEGAL WHERE sigla = %s AND turma = %s", params=(sigla, turma))
            if not df_bl.empty and pd.notnull(df_bl.iloc[0]["base_legal"]) and str(df_bl.iloc[0]["base_legal"]).strip():
                base_legal_texto = str(df_bl.iloc[0]["base_legal"]).strip()
        except Exception:
            pass

    path_logo_gdf = "logo_gdf.png"
    path_logo_escola = "logo_escola.png"
    img_gdf = Image(path_logo_gdf, width=42, height=42) if os.path.exists(path_logo_gdf) else Paragraph("", estilo_valor)
    img_escola = Image(path_logo_escola, width=42, height=42) if os.path.exists(path_logo_escola) else Paragraph("", estilo_valor)

    texto_institucional = [
        Paragraph("GOVERNO DO DISTRITO FEDERAL", estilo_institucional_bold),
        Paragraph("Secretaria de Estado de Educação", estilo_institucional),
        Paragraph("Subsecretaria de Educação Básica", estilo_institucional),
        Paragraph("Coordenação Regional de Ensino de Planaltina", estilo_institucional),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina", estilo_institucional_bold),
    ]

    cabecalho = Table([[img_gdf, texto_institucional, img_escola]], colWidths=[52, 450, 52], rowHeights=[51], hAlign="LEFT")
    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.8, CINZA_LINHA),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    def bloco_secao(titulo):
        t = Table([[Paragraph(titulo, estilo_secao)]], colWidths=[554], rowHeights=[17], hAlign="LEFT")
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

    story = [cabecalho, Paragraph("HISTÓRICO ESCOLAR", estilo_titulo), bloco_secao("IDENTIFICAÇÃO ACADÊMICA")]
    
    identificacao = [
        [Paragraph("CURSO", estilo_label), Paragraph("MATRÍCULA", estilo_label), Paragraph("TURMA / TURNO", estilo_label)],
        [Paragraph(curso, estilo_valor_bold), Paragraph(matricula or "—", estilo_valor), Paragraph(turma or "—", estilo_valor)],
    ]
    story.append(tabela_campos(identificacao, [330, 110, 114]))
    story.append(Spacer(1, 4))

    story.append(bloco_secao("DADOS DO ESTUDANTE"))
    dados_estudante = [
        [Paragraph("NOME", estilo_label), Paragraph("CPF", estilo_label), Paragraph("SEXO", estilo_label)],
        [Paragraph(nome or "—", estilo_valor_bold), Paragraph(cpf or "—", estilo_valor), Paragraph(sexo or "—", estilo_valor)],
        [Paragraph("NOME DA MÃE", estilo_label), Paragraph("NOME DO PAI", estilo_label), Paragraph("DATA DE NASCIMENTO", estilo_label)],
        [Paragraph(mae or "—", estilo_valor), Paragraph(pai or "—", estilo_valor), Paragraph(dt_nasc or "—", estilo_valor)],
        [Paragraph("NACIONALIDADE", estilo_label), Paragraph("NATURALIDADE / UF", estilo_label), Paragraph("RG / ÓRGÃO / DATA DE EXPEDIÇÃO", estilo_label)],
        [Paragraph(nacionalidade or "—", estilo_valor), Paragraph(f"{naturalidade} / {uf}".strip(" /") or "—", estilo_valor), Paragraph(" ".join(x for x in [rg, orgao, dt_exp] if x) or "—", estilo_valor)],
    ]
    story.append(tabela_campos(dados_estudante, [300, 120, 134]))
    story.append(Spacer(1, 4))

    story.append(bloco_secao("BASE LEGAL"))
    base_legal = Table([[Paragraph(base_legal_texto, estilo_valor)]], colWidths=[554], hAlign="LEFT")
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
            comp = str(row.get("unidade_curricular", row.get("componente", row.get("disciplina", "---"))))
            sem = str(row.get("semestre", "")).strip()
            if not sem or sem.lower() in ("none", "nan", ""):
                sem, ch, mod, faltas, res = "", "", "", "", ""
            else:
                ch = str(row.get("carga_horaria", row.get("ch", "")))
                mod = str(row.get("modulo", ""))
                faltas = str(row.get("faltas", "0"))
                res = str(row.get("resultado", row.get("conceito", "")))

            tabela_hist_dados.append([
                Paragraph(comp, estilo_td_left), Paragraph(sem, estilo_td), Paragraph(ch, estilo_td),
                Paragraph(mod, estilo_td), Paragraph(faltas, estilo_td), Paragraph(res, estilo_td),
            ])

    t_hist = Table(tabela_hist_dados, repeatRows=1, colWidths=[314, 40, 30, 65, 45, 60], hAlign="LEFT")
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
            estilo_hist.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFAFA")))
    t_hist.setStyle(TableStyle(estilo_hist))
    story.append(t_hist)
    story.append(Spacer(1, 5))

    rodape_legenda = Table([[
        Paragraph("<b>Legenda:</b> AP = Apto; AE = Aproveitamento de Estudos; NA = Não Apto; TR = Trancamento de Curso; D = Desistente", estilo_rodape),
        Paragraph("<b>T. Teoria:</b> 1.366 h", estilo_rodape),
        Paragraph("<b>T. Prática:</b> 0 h", estilo_rodape),
    ]], colWidths=[350, 102, 102], hAlign="LEFT")
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
    data_tabela = Table([[Paragraph(data_documento, estilo_assinatura)]], colWidths=[554], hAlign="LEFT")
    data_tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    assinatura = Table([[
        Paragraph("____________________________________________<br/><b>Diretor(a)</b>", estilo_assinatura),
        Paragraph("____________________________________________<br/><b>Chefe de Secretaria Escolar</b>", estilo_assinatura),
    ]], colWidths=[277, 277], rowHeights=[43], hAlign="LEFT")
    assinatura.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    bloco_final = KeepTogether([rodape_legenda, Spacer(1, 9), data_tabela, Spacer(1, 23), assinatura])
    story.append(bloco_final)

    def desenhar_rodape(canvas, doc):
        canvas.saveState()
        largura, _ = A4
        canvas.setStrokeColor(CINZA_LINHA)
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, 18, largura - doc.rightMargin, 18)
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(CINZA_MEDIO)
        canvas.drawString(doc.leftMargin, 9, "Centro de Educação Profissional Escola Técnica de Planaltina")
        canvas.drawRightString(largura - doc.rightMargin, 9, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 2. MATRIZ AFIN
# ============================================================

COLUNAS_MATRIZ_POR_PAGINA = 21
MARGEM_ESQ = 10 * mm
MARGEM_DIR = 10 * mm
MARGEM_SUP = 8 * mm
MARGEM_INF = 9 * mm
LARGURA_MATRICULA = 24 * mm
LARGURA_ESTUDANTE = 49 * mm

AZUL_INSTITUCIONAL = colors.HexColor("#173B63")
AZUL_SECUNDARIO = colors.HexColor("#315D82")
AZUL_MUITO_CLARO = colors.HexColor("#F2F6FA")
CINZA_TEXTO_AFIN = colors.HexColor("#28343F")
CINZA_SECUNDARIO = colors.HexColor("#68737D")
CINZA_ZEBRA = colors.HexColor("#FAFBFC")

def _texto(valor):
    if valor is None: return ""
    try:
        if pd.isna(valor): return ""
    except Exception: pass
    texto = str(valor).strip()
    return "" if texto.lower() in {"nan", "nat", "none"} else texto

def _html(valor):
    return _texto(valor).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _normalizar(valor):
    return re.sub(r"\s+", " ", _texto(valor).upper()).strip()

def _tipo_coluna(nome):
    s = _normalizar(nome)
    if re.search(r"(?:^|[\s_-])(?:FAL|FALTAS)(?:$|[\s_-])", s): return "FAL"
    if re.search(r"(?:^|[\s_-])(?:CON|CONCEITO)(?:$|[\s_-])", s): return "CON"
    return None

def _nome_uc(nome):
    return re.sub(r"\s*[-–—]\s*(?:FAL|FALTAS|CON|CONCEITO)\s*$", "", _texto(nome), flags=re.I).strip()

def _mapa_iduc(mapa):
    if not mapa: return {}
    resultado = {}
    for iduc, nome in mapa.items():
        nome = _texto(nome)
        if nome: resultado[_normalizar(nome)] = _texto(iduc)
    return resultado

def _estilos_afin():
    base = getSampleStyleSheet()
    return {
        "instituicao": ParagraphStyle("AFINInstituicao", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=9.2, alignment=TA_CENTER, textColor=AZUL_INSTITUCIONAL),
        "titulo": ParagraphStyle("AFINTitulo", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.2, leading=11, alignment=TA_CENTER, textColor=AZUL_INSTITUCIONAL),
        "subtitulo": ParagraphStyle("AFINSubtitulo", parent=base["Normal"], fontName="Helvetica", fontSize=6.5, leading=7.2, alignment=TA_CENTER, textColor=CINZA_SECUNDARIO),
        "label": ParagraphStyle("AFINLabel", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.9, leading=6.5, alignment=TA_LEFT, textColor=CINZA_SECUNDARIO),
        "valor": ParagraphStyle("AFINValor", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=8.5, alignment=TA_LEFT, textColor=CINZA_TEXTO_AFIN),
        "matricula_header": ParagraphStyle("AFINMatriculaHeader", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.7, leading=6.2, alignment=TA_CENTER, textColor=colors.white),
        "estudante_header": ParagraphStyle("AFINEstudanteHeader", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.7, leading=6.2, alignment=TA_LEFT, textColor=colors.white),
        "uc": ParagraphStyle("AFINUC", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5.1, leading=5.5, alignment=TA_CENTER, textColor=AZUL_INSTITUCIONAL),
        "iduc": ParagraphStyle("AFINIDUC", parent=base["Normal"], fontName="Helvetica", fontSize=4.8, leading=5.1, alignment=TA_CENTER, textColor=CINZA_SECUNDARIO),
        "indicador": ParagraphStyle("AFINIndicador", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=5, leading=5.2, alignment=TA_CENTER, textColor=colors.white),
        "matricula": ParagraphStyle("AFINMatricula", parent=base["Normal"], fontName="Helvetica", fontSize=6.4, leading=7, alignment=TA_CENTER, textColor=CINZA_TEXTO_AFIN),
        "nome": ParagraphStyle("AFINNome", parent=base["Normal"], fontName="Helvetica", fontSize=6.5, leading=7.1, alignment=TA_LEFT, textColor=CINZA_TEXTO_AFIN),
        "valor_celula": ParagraphStyle("AFINValorCelula", parent=base["Normal"], fontName="Helvetica", fontSize=6.3, leading=6.8, alignment=TA_CENTER, textColor=CINZA_TEXTO_AFIN),
    }

def _blocos(colunas):
    if not colunas: return [[None] * COLUNAS_MATRIZ_POR_PAGINA]
    saida = []
    for inicio in range(0, len(colunas), COLUNAS_MATRIZ_POR_PAGINA):
        bloco = list(colunas[inicio:inicio + COLUNAS_MATRIZ_POR_PAGINA])
        falta = COLUNAS_MATRIZ_POR_PAGINA - len(bloco)
        if falta > 0: bloco.extend([None] * falta)
        saida.append(bloco)
    return saida

def _topo(largura, st):
    dados = [
        [Paragraph("SECRETARIA DE ESTADO DE EDUCAÇÃO DO DISTRITO FEDERAL", st["instituicao"])],
        [Paragraph("CEP – ESCOLA TÉCNICA DE PLANALTINA", st["titulo"])],
        [Paragraph("AFIN — ACOMPANHAMENTO DA FREQUÊNCIA E CONCEITO", st["subtitulo"])],
    ]
    tabela = Table(dados, colWidths=[largura], rowHeights=[4.2 * mm, 4.8 * mm, 3.8 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 2), (-1, 2), 0.8, AZUL_INSTITUCIONAL),
    ]))
    return tabela

def _identificacao(largura, turma, semestre, st):
    metade = largura / 2
    dados = [[Paragraph("TURMA", st["label"]), Paragraph(_html(turma), st["valor"]), Paragraph("SEMESTRE", st["label"]), Paragraph(_html(semestre), st["valor"])]]
    larguras = [15 * mm, metade - 15 * mm, 20 * mm, metade - 20 * mm]
    tabela = Table(dados, colWidths=larguras, rowHeights=[7 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), AZUL_MUITO_CLARO),
        ("BACKGROUND", (2, 0), (2, 0), AZUL_MUITO_CLARO),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, CINZA_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return tabela

def _cabecalho_afin(bloco, mapa, wm, wn, wc, st):
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

def _tabela_afin(df, bloco, mapa, wm, wn, wc, st):
    cabecalho, larguras = _cabecalho_afin(bloco, mapa, wm, wn, wc, st)
    posicoes = {coluna: indice for indice, coluna in enumerate(df.columns)}
    linhas = list(cabecalho)

    for _, row in df.iterrows():
        linha = [Paragraph(_html(row.iloc[0]), st["matricula"]), Paragraph(_html(row.iloc[1]), st["nome"])]
        for coluna in bloco:
            valor = "" if coluna is None else _texto(row.iloc[posicoes[coluna]])
            linha.append(Paragraph(_html(valor), st["valor_celula"]))
        linhas.append(linha)

    tabela = Table(linhas, colWidths=larguras, repeatRows=3, hAlign="LEFT")
    comandos = [
        ("BACKGROUND", (0, 0), (1, 2), AZUL_INSTITUCIONAL),
        ("BACKGROUND", (2, 0), (-1, 0), AZUL_MUITO_CLARO),
        ("BACKGROUND", (2, 1), (-1, 1), colors.white),
        ("BACKGROUND", (2, 2), (-1, 2), AZUL_SECUNDARIO),
        ("BACKGROUND", (0, 3), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 3), (1, -1), "LEFT"),
        ("LINEBELOW", (0, 2), (-1, 2), 0.65, AZUL_INSTITUCIONAL),
        ("LINEAFTER", (0, 0), (0, -1), 0.45, CINZA_LINHA),
        ("LINEAFTER", (1, 0), (1, -1), 0.8, AZUL_SECUNDARIO),
        ("TOPPADDING", (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.0),
    ]
    for indice in range(3, len(linhas)):
        if (indice - 3) % 2 == 1:
            comandos.append(("BACKGROUND", (0, indice), (-1, indice), CINZA_ZEBRA))
    tabela.setStyle(TableStyle(comandos))
    return tabela

def _rodape_afin(canvas, doc):
    canvas.saveState()
    largura_pagina, _ = landscape(A4)
    y = 5.0 * mm
    canvas.setStrokeColor(CINZA_LINHA)
    canvas.setLineWidth(0.3)
    canvas.line(MARGEM_ESQ, y + 3.2 * mm, largura_pagina - MARGEM_DIR, y + 3.2 * mm)
    canvas.setFont("Helvetica", 5.4)
    canvas.setFillColor(CINZA_SECUNDARIO)
    canvas.drawString(MARGEM_ESQ, y, "CEP ETP • AFIN")
    canvas.drawRightString(largura_pagina - MARGEM_DIR, y, f"Página {doc.page}")
    canvas.restoreState()

def gerar_pdf_afin(df_matriz, turma, semestre, mapa_nomes_iduc=None):
    df = df_matriz.copy() if df_matriz is not None else pd.DataFrame()
    if not df.empty and len(df.columns) >= 2:
        cols = list(df.columns)
        if not _texto(cols[0]): cols[0] = "Matrícula"
        if not _texto(cols[1]): cols[1] = "Estudante"
        df.columns = cols

    buffer = io.BytesIO()
    pagina = landscape(A4)
    largura_pagina, _ = pagina
    largura_util = largura_pagina - MARGEM_ESQ - MARGEM_DIR

    doc = SimpleDocTemplate(
        buffer, pagesize=pagina, leftMargin=MARGEM_ESQ, rightMargin=MARGEM_DIR,
        topMargin=MARGEM_SUP, bottomMargin=MARGEM_INF, title="Matriz AFIN"
    )
    st = _estilos_afin()
    mapa = _mapa_iduc(mapa_nomes_iduc)
    colunas = list(df.columns[2:]) if not df.empty else []
    blocos = _blocos(colunas)
    largura_restante = largura_util - LARGURA_MATRICULA - LARGURA_ESTUDANTE
    largura_coluna = largura_restante / COLUNAS_MATRIZ_POR_PAGINA

    story = []
    for numero_bloco, bloco in enumerate(blocos, start=1):
        if numero_bloco > 1: story.append(PageBreak())
        story.append(_topo(largura_util, st))
        story.append(Spacer(1, 1.6 * mm))
        story.append(_identificacao(largura_util, turma, semestre, st))
        story.append(Spacer(1, 1.7 * mm))
        if df.empty:
            story.append(Paragraph("Nenhum registro disponível.", st["nome"]))
        else:
            story.append(_tabela_afin(df, bloco, mapa, LARGURA_MATRICULA, LARGURA_ESTUDANTE, largura_coluna, st))

    doc.build(story, onFirstPage=_rodape_afin, onLaterPages=_rodape_afin)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 3. RELATÓRIO DE TURMA
# ============================================================

def gerar_pdf_relatorio_turma(dados):
    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n% Relatorio da Turma em desenvolvimento\n")
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 4. DECLARAÇÃO DE ESCOLARIDADE
# ============================================================

def gerar_pdf_declaracao_escolaridade(dados_aluno):
    def get_dado(dados, *chaves):
        if not isinstance(dados, dict): return ""
        for chave in chaves:
            if chave in dados and dados[chave] is not None:
                val = str(dados[chave]).strip()
                if val and val.lower() != "none": return val
            target = chave.lower().replace(" ", "_").replace(":", "")
            for k, v in dados.items():
                if k.lower().replace(" ", "_").replace(":", "") == target and v is not None:
                    val = str(v).strip()
                    if val and val.lower() != "none": return val
        return ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    style_header_title = ParagraphStyle("HeaderTitle", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=12)
    style_header_sub = ParagraphStyle("HeaderSub", fontName="Helvetica", fontSize=8, alignment=1, leading=10)
    style_doc_title = ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=11, alignment=1, leading=13)
    style_label = ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=colors.HexColor("#333333"))
    style_val = ParagraphStyle("Val", fontName="Helvetica", fontSize=8, leading=10)
    style_obs = ParagraphStyle("ObsText", fontName="Helvetica", fontSize=8, leading=12)

    PAGE_WIDTH = 523

    img_gdf = Image("logo_gdf.png", width=50, height=50) if os.path.exists("logo_gdf.png") else Paragraph("", styles["Normal"])
    img_escola = Image("logo_escola.png", width=50, height=50) if os.path.exists("logo_escola.png") else Paragraph("", styles["Normal"])

    header_text = [
        Paragraph("<b>Governo do Distrito Federal</b>", style_header_title),
        Paragraph("Secretaria de Estado de Educação", style_header_sub),
        Paragraph("Subsecretaria de Educação Básica", style_header_sub),
        Paragraph("Coordenação Regional de Ensino de Planaltina", style_header_sub),
        Paragraph("<b>Centro de Educação Profissional - Escola Técnica de Planaltina</b>", style_header_sub),
    ]

    tabela_cabecalho = Table([[img_gdf, header_text, img_escola]], colWidths=[60, PAGE_WIDTH - 120, 60])
    tabela_cabecalho.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(tabela_cabecalho)

    tabela_titulo = Table([[Paragraph("DECLARAÇÃO DE ESCOLARIDADE", style_doc_title)]], colWidths=[PAGE_WIDTH])
    tabela_titulo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(tabela_titulo)

    def celula(rotulo, valor):
        v = str(valor) if valor and str(valor).lower() != "none" else ""
        return [Paragraph(rotulo, style_label), Paragraph(f"<b>{v}</b>", style_val)]

    curso = get_dado(dados_aluno, "curso")
    matricula = get_dado(dados_aluno, "matricula", "matricula_aluno")
    turma = get_dado(dados_aluno, "turma", "turma_turno")
    nome = get_dado(dados_aluno, "nome", "nome_aluno")
    sexo = get_dado(dados_aluno, "sexo")
    data_nascimento = get_dado(dados_aluno, "data_nascimento", "dt_nascimento")
    nacionalidade = get_dado(dados_aluno, "nacionalidade") or "BRASILEIRA"
    naturalidade = get_dado(dados_aluno, "naturalidade", "cidade")
    uf = get_dado(dados_aluno, "uf") or "DF"
    rg = get_dado(dados_aluno, "rg", "identidade")
    orgao_expeditor = get_dado(dados_aluno, "org_expedidor", "orgao_expeditor")
    data_expedicao = get_dado(dados_aluno, "dta_expedicao", "data_expedicao")
    cpf = get_dado(dados_aluno, "cpf")
    nome_mae = get_dado(dados_aluno, "nome_mae", "mae")
    raw_pai = get_dado(dados_aluno, "nome_pai", "pai")
    nome_pai = "" if raw_pai.lower() in ["não sei", "nao sei", "não informado", "-"] else raw_pai
    endereco_final = f"{get_dado(dados_aluno, 'endereco')} {get_dado(dados_aluno, 'bairro')}".strip()
    cep = get_dado(dados_aluno, "cep")

    dados_grid = [
        [celula("Curso:", curso), "", "", "", "", "", "", ""],
        [celula("Matrícula:", matricula), "", celula("Turma/Turno:", turma), "", celula("Nome:", nome), "", "", celula("Sexo:", sexo)],
        [celula("Data de Nascimento:", data_nascimento), celula("Nacionalidade:", nacionalidade), celula("Naturalidade:", naturalidade), celula("UF:", uf), celula("Identidade:", rg), celula("Órg. Exp.:", orgao_expeditor), celula("Data de Expedição:", data_expedicao), ""],
        [celula("CPF:", cpf), "", celula("Nome da Mãe:", nome_mae), "", "", "", "", ""],
        [celula("", ""), "", celula("Nome do Pai:", nome_pai), "", "", "", "", ""],
        [celula("Endereço:", endereco_final), "", "", "", celula("CEP:", cep), "", celula("UF:", uf), ""],
    ]

    tabela_dados = Table(dados_grid, colWidths=[75, 75, 70, 35, 95, 55, 64, 54])
    tabela_dados.setStyle(TableStyle([
        ("SPAN", (0, 0), (7, 0)), ("SPAN", (0, 1), (1, 1)), ("SPAN", (2, 1), (3, 1)), ("SPAN", (4, 1), (6, 1)),
        ("SPAN", (2, 3), (7, 3)), ("SPAN", (2, 4), (7, 4)), ("SPAN", (0, 5), (3, 5)), ("SPAN", (4, 5), (5, 5)), ("SPAN", (6, 5), (7, 5)),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(tabela_dados)

    obs_content = [
        Paragraph("<b>Observações:</b>", style_label),
        Paragraph("• <b>Turno Matutino:</b> Aulas de 08h00min às 12h00min.", style_obs),
        Paragraph("• <b>Turno Vespertino:</b> Aulas de 13h30min às 17h30min.", style_obs),
        Paragraph("• <b>Turno Noturno:</b> Aulas de 19h00min às 23h00min.", style_obs),
        Paragraph("• Declaração válida somente sem emendas por 30 dias.", style_obs),
        Paragraph("• <b>Observação: O(a) aluno(a) está regularmente matriculado(a).</b>", style_obs),
    ]
    tabela_obs = Table([[obs_content]], colWidths=[PAGE_WIDTH])
    tabela_obs.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black), ("BOTTOMPADDING", (0, 0), (-1, -1), 120)]))
    story.append(tabela_obs)

    data_atual = datetime.now().strftime("%d/%m/%Y")
    tabela_rodape = Table([[Paragraph(f"<b>PLANALTINA-DF, {data_atual}</b>", style_obs), ""],
                           [Paragraph("_____________________________________________________<br/><b>Secretaria Escolar</b>", ParagraphStyle("Sig", fontName="Helvetica", fontSize=8, alignment=1)), ""]],
                          colWidths=[PAGE_WIDTH / 2, PAGE_WIDTH / 2])
    tabela_rodape.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("BOX", (0, 0), (-1, -1), 1, colors.black), ("ALIGN", (0, 1), (-1, -1), "CENTER")]))
    story.append(tabela_rodape)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 5. PASSE ESTUDANTIL
# ============================================================

def gerar_pdf_passe_estudantil(dados_aluno):
    def get_dado(dados, *chaves):
        if not isinstance(dados, dict): return ""
        for chave in chaves:
            if chave in dados and dados[chave] is not None:
                val = str(dados[chave]).strip()
                if val and val.lower() != "none": return val
            target = chave.lower().replace(" ", "_").replace(":", "")
            for k, v in dados.items():
                if k.lower().replace(" ", "_").replace(":", "") == target and v is not None:
                    val = str(v).strip()
                    if val and val.lower() != "none": return val
        return ""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    style_header_title = ParagraphStyle("HeaderTitle", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=12)
    style_header_sub = ParagraphStyle("HeaderSub", fontName="Helvetica", fontSize=8, alignment=1, leading=10)
    style_doc_title = ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=11, alignment=1, leading=13)
    style_label = ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=colors.HexColor("#333333"))
    style_val = ParagraphStyle("Val", fontName="Helvetica", fontSize=8, leading=10)
    style_obs = ParagraphStyle("ObsText", fontName="Helvetica", fontSize=8, leading=12)

    PAGE_WIDTH = 523

    img_gdf = Image("logo_gdf.png", width=50, height=50) if os.path.exists("logo_gdf.png") else Paragraph("", styles["Normal"])
    img_escola = Image("logo_escola.png", width=50, height=50) if os.path.exists("logo_escola.png") else Paragraph("", styles["Normal"])

    header_text = [
        Paragraph("<b>Governo do Distrito Federal</b>", style_header_title),
        Paragraph("Secretaria de Estado de Educação", style_header_sub),
        Paragraph("Subsecretaria de Educação Básica", style_header_sub),
        Paragraph("Centro de Educação Profissional Escola Técnica de Planaltina", style_header_sub),
    ]

    tabela_cabecalho = Table([[img_gdf, header_text, img_escola]], colWidths=[60, PAGE_WIDTH - 120, 60])
    tabela_cabecalho.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(tabela_cabecalho)

    tabela_titulo = Table([[Paragraph("DECLARAÇÃO PARA OBTENÇÃO DE PASSE ESTUDANTIL", style_doc_title)]], colWidths=[PAGE_WIDTH])
    tabela_titulo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(tabela_titulo)

    def celula(rotulo, valor):
        v = str(valor) if valor and str(valor).lower() != "none" else ""
        return [Paragraph(rotulo, style_label), Paragraph(f"<b>{v}</b>", style_val)]

    curso = get_dado(dados_aluno, "curso")
    matricula = get_dado(dados_aluno, "matricula", "matricula_aluno")
    turma = get_dado(dados_aluno, "turma", "turma_turno")
    nome = get_dado(dados_aluno, "nome", "nome_aluno")
    sexo = get_dado(dados_aluno, "sexo")
    data_nascimento = get_dado(dados_aluno, "data_nascimento", "dt_nascimento")
    nacionalidade = get_dado(dados_aluno, "nacionalidade") or "BRASILEIRA"
    naturalidade = get_dado(dados_aluno, "naturalidade", "cidade")
    uf = get_dado(dados_aluno, "uf") or "DF"
    rg = get_dado(dados_aluno, "rg", "identidade")
    orgao_expeditor = get_dado(dados_aluno, "org_expedidor", "orgao_expeditor")
    data_expedicao = get_dado(dados_aluno, "dta_expedicao", "data_expedicao")
    cpf = get_dado(dados_aluno, "cpf")
    nome_mae = get_dado(dados_aluno, "nome_mae", "mae")
    raw_pai = get_dado(dados_aluno, "nome_pai", "pai")
    nome_pai = "" if raw_pai.lower() in ["não sei", "nao sei", "não informado", "-"] else raw_pai
    nome_responsavel = get_dado(dados_aluno, "nome_responsavel")
    endereco = get_dado(dados_aluno, "endereco")
    bairro = get_dado(dados_aluno, "bairro")
    cidade = get_dado(dados_aluno, "cidade") or "PLANALTINA"
    uf_federacao = get_dado(dados_aluno, "uf_federacao", "uf") or "DF"
    cep = get_dado(dados_aluno, "cep")

    dados_grid = [
        [celula("Curso:", curso), "", "", "", "", "", "", ""],
        [celula("Matrícula:", matricula), "", celula("Turma/ Turno:", turma), "", celula("Nome:", nome), "", "", celula("Sexo:", sexo)],
        [celula("Data de Nascimento:", data_nascimento), celula("Nacionalidade:", nacionalidade), celula("Naturalidade:", naturalidade), celula("UF:", uf), celula("Identidade:", rg), celula("Org. Exp.:", orgao_expeditor), celula("Data de Expedição:", data_expedicao), ""],
        [celula("CPF:", cpf), "", celula("Nome da Mãe:", nome_mae), "", "", "", "", ""],
        [celula("", ""), "", celula("Nome do Pai:", nome_pai), "", "", "", "", ""],
        [celula("", ""), "", celula("Nome do Responsável:", nome_responsavel), "", "", "", "", ""],
        [celula("Endereço:", endereco), "", "", "", celula("Bairro:", bairro), "", "", ""],
        [celula("Cidade:", cidade), "", celula("Unidade da Federação:", uf_federacao), "", "", celula("CEP:", cep), "", ""]
    ]

    tabela_dados = Table(dados_grid, colWidths=[75, 75, 70, 35, 95, 55, 64, 54])
    tabela_dados.setStyle(TableStyle([
        ("SPAN", (0, 0), (7, 0)), ("SPAN", (0, 1), (1, 1)), ("SPAN", (2, 1), (3, 1)), ("SPAN", (4, 1), (6, 1)),
        ("SPAN", (2, 3), (7, 3)), ("SPAN", (2, 4), (7, 4)), ("SPAN", (2, 5), (7, 5)), ("SPAN", (0, 6), (3, 6)),
        ("SPAN", (4, 6), (7, 6)), ("SPAN", (0, 7), (1, 7)), ("SPAN", (2, 7), (4, 7)), ("SPAN", (5, 7), (7, 7)),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(tabela_dados)

    obs_content = [
        Paragraph("<b>Observações:</b>", style_label),
        Paragraph("• Turno Matutino: Aulas de 8h00min às 12h00min.", style_obs),
        Paragraph("• Turno Vespertino: Aulas de 13h30min às 17h30min.", style_obs),
        Paragraph("• Turno Noturno: Aulas de 19h00min às 23h00min.", style_obs),
        Paragraph("• Declaração válida por 30 dias.", style_obs),
        Paragraph("• Início do 1º Semestre: 12/02/2026 – Término: 10/07/2026.", style_obs),
        Paragraph("• Início do 2º Semestre: 28/07/2026 – Término: 22/12/2026.", style_obs),
        Paragraph("• <b>Observação: O(a) aluno(a) está regularmente matriculado(a).</b>", style_obs),
    ]
    tabela_obs = Table([[obs_content]], colWidths=[PAGE_WIDTH])
    tabela_obs.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black), ("BOTTOMPADDING", (0, 0), (-1, -1), 80)]))
    story.append(tabela_obs)

    data_atual = datetime.now().strftime("%d/%m/%Y")
    tabela_rodape = Table([[Paragraph(f"<b>PLANALTINA-DF,</b> {data_atual}", style_obs), ""],
                           [Paragraph("_____________________________________________________<br/><b>Secretário(a) Escolar</b>", ParagraphStyle("Sig", fontName="Helvetica", fontSize=8, alignment=1)), ""]],
                          colWidths=[PAGE_WIDTH / 2, PAGE_WIDTH / 2])
    tabela_rodape.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("BOX", (0, 0), (-1, -1), 1, colors.black), ("ALIGN", (0, 1), (-1, -1), "CENTER")]))
    story.append(tabela_rodape)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 6. PASSES E RENOVAÇÕES (TURMA / UNIFICADO)
# ============================================================

def gerar_pdf_passes_turma_unificado(df_turma, turma_nome=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"PASSES ESTUDANTIS - TURMA: {turma_nome}", styles["Heading1"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def gerar_pdf_renovacao_matricula(dados_aluno):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph("FICHA DE RENOVAÇÃO DE MATRÍCULA", styles["Heading1"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def gerar_pdf_renovacao_turma_unificado(df_turma):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=22, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = [Paragraph("RENOVAÇÕES DE MATRÍCULA - TURMA UNIFICADA", styles["Heading1"])]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
