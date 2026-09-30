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
# -*- coding: utf-8 -*-
import io
import pandas as pd
import streamlit as st

from modulos.conexao import executar_query
from modulos.pdf_generator import (
    gerar_pdf_declaracao_escolaridade,
    gerar_pdf_historico_aluno,
    gerar_pdf_passe_estudantil,
    gerar_pdf_passes_turma_unificado,
    gerar_pdf_renovacao_matricula,
    gerar_pdf_renovacao_turma_unificado,
)


def renderizar_modulo_secretaria():
    st.subheader(
        "🎓 Secretaria Escolar - Motor de Ficha Académica e Documentos"
    )
    st.markdown(
        "Selecione o estudante, escolha o tipo de documento, ajuste os campos específicos se necessário e emita a documentação oficial."
    )

    try:
        df_todos_alunos = executar_query(
            "SELECT matricula, nome, turma FROM TB_PESSOAS"
        )

        if df_todos_alunos is None or df_todos_alunos.empty:
            st.warning("Nenhum aluno encontrado na base de dados.")
            return

        df_todos_alunos["opcao_combo"] = (
            df_todos_alunos["matricula"].astype(str)
            + " - "
            + df_todos_alunos["nome"].astype(str)
        )
        lista_alunos_dropdown = df_todos_alunos["opcao_combo"].tolist()
        aluno_selecionado = st.selectbox(
            "Selecione o Estudante (Matrícula e Nome):", lista_alunos_dropdown
        )

        if aluno_selecionado:
            matricula_busca = aluno_selecionado.split(" - ")[0].strip()
            df_dados_pessoais = executar_query(
                "SELECT * FROM TB_PESSOAS WHERE matricula = %s",
                params=(matricula_busca,),
            )

            if df_dados_pessoais is not None and not df_dados_pessoais.empty:
                st.success(
                    f"Ficha carregada com sucesso para a matrícula: {matricula_busca}"
                )
                aba_ficha, aba_historico = st.tabs(
                    [
                        "📄 Ficha Cadastral (Dados Pessoais)",
                        "📚 Histórico, Edição e Emissão de Documentos",
                    ]
                )

                # -------------------------------------------------------------
                # ABA 1: FICHA CADASTRAL
                # -------------------------------------------------------------
                with aba_ficha:
                    st.markdown(
                        "### Informações Pessoais e Cadastrais do Estudante"
                    )
                    aluno_info = df_dados_pessoais.iloc[0].to_dict()

                    with st.form(key=f"form_ficha_{matricula_busca}"):
                        col_f1, col_f2 = st.columns(2)
                        campos_atualizados = {}
                        chaves = [
                            k
                            for k in aluno_info.keys()
                            if k.lower() != "matricula"
                        ]

                        for i, col_name in enumerate(chaves):
                            val_atual = str(aluno_info.get(col_name, ""))
                            if val_atual in ("None", "nan", "<NA>"):
                                val_atual = ""

                            target_col = col_f1 if i % 2 == 0 else col_f2
                            with target_col:
                                campos_atualizados[col_name] = st.text_input(
                                    f"{col_name.replace('_', ' ').title()}:",
                                    value=val_atual,
                                )

                        if st.form_submit_button(
                            "💾 Guardar Alterações Cadastrais na Base de Dados"
                        ):
                            try:
                                set_clauses = ", ".join(
                                    [f"{k} = %s" for k in campos_atualizados]
                                )
                                sql_upd_cad = f"UPDATE TB_PESSOAS SET {set_clauses} WHERE matricula = %s"
                                params = list(
                                    campos_atualizados.values()
                                ) + [matricula_busca]
                                executar_query(
                                    sql_upd_cad, params=params, fetch=False
                                )
                                st.success(
                                    "Alterações cadastrais guardadas com sucesso!"
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(
                                    f"Erro ao guardar alterações cadastrais: {e}"
                                )

                # -------------------------------------------------------------
                # ABA 2: HISTÓRICO, EDIÇÃO PRÉ-IMPRESSÃO E EMISSÃO
                # -------------------------------------------------------------
                with aba_historico:
                    st.markdown("### Histórico Curricular e Notas Associadas")
                    df_historico_aluno = executar_query(
                        "SELECT * FROM TB_DIARIO WHERE matricula = %s",
                        params=(matricula_busca,),
                    )

                    if df_historico_aluno is None or df_historico_aluno.empty:
                        st.info("Não existem registos curriculares na TB_DIARIO para este aluno.")
                        df_historico_editado = pd.DataFrame()
                    else:
                        df_historico_editado = st.data_editor(
                            df_historico_aluno,
                            use_container_width=True,
                            key=f"historico_editor_{matricula_busca}",
                        )

                        if st.button("💾 Guardar Alterações do Histórico"):
                            try:
                                atualizados_hist = 0
                                for _, row in df_historico_editado.iterrows():
                                    mat = row.get("matricula")
                                    iduc_val = row.get("iduc")

                                    if mat and iduc_val:
                                        sql_hist = """
                                            UPDATE TB_DIARIO 
                                            SET unidade_curricular = %s, carga_horaria = %s, modulo = %s, faltas = %s 
                                            WHERE matricula = %s AND iduc = %s
                                        """
                                        executar_query(
                                            sql_hist,
                                            params=(
                                                row.get("unidade_curricular"),
                                                row.get("carga_horaria"),
                                                row.get("modulo"),
                                                row.get("faltas"),
                                                mat,
                                                iduc_val,
                                            ),
                                            fetch=False,
                                        )
                                        atualizados_hist += 1
                                st.success(f"Sucesso! {atualizados_hist} registos guardados.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao guardar histórico: {e}")

                    st.markdown("---")
                    st.markdown("### 📝 Editor Personalizado e Emissão de Documentos")
                    st.info("Selecione o documento oficial abaixo. Todos os dados virão pré-preenchidos em campos editáveis para revisão.")

                    tipo_documento = st.selectbox(
                        "Selecione o Documento a Emitir:",
                        [
                            "Renovação de Matrícula",
                            "Passe Estudantil",
                            "Declaração de Escolaridade", 
                            "Declaração de Conclusão", 
                            "Histórico Escolar Oficial"
                        ]
                    )

                    dados_originais = df_dados_pessoais.iloc[0].to_dict()

                    with st.form(key=f"form_edicao_doc_{matricula_busca}"):
                        st.markdown(f"**A ajustar parâmetros para:** `{tipo_documento}`")
                        
                        # Bloco 1: Dados Pessoais Básicos
                        st.markdown("##### 👤 Identificação Pessoal")
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            edit_nome = st.text_input("Nome Completo:", value=str(dados_originais.get("nome", "")))
                            edit_curso = st.text_input("Curso:", value=str(dados_originais.get("curso", "TÉCNICO EM ENFERMAGEM")))
                            edit_turma = st.text_input("Turma / Turno:", value=str(dados_originais.get("turma", "")))
                            edit_rg = st.text_input("Identidade (RG):", value=str(dados_originais.get("identidade", dados_originais.get("rg", ""))))
                            edit_orgao = st.text_input("Órgão Expeditor / UF:", value=str(dados_originais.get("orgao_expeditor", dados_originais.get("orgao", ""))))
                        
                        with col_ed2:
                            edit_cpf = st.text_input("CPF:", value=str(dados_originais.get("cpf", "")))
                            edit_nasc = st.text_input("Data de Nascimento:", value=str(dados_originais.get("data_nascimento", dados_originais.get("dt_nascimento", ""))))
                            edit_sexo = st.text_input("Sexo:", value=str(dados_originais.get("sexo", "")))
                            edit_dt_exp = st.text_input("Data de Expedição (RG):", value=str(dados_originais.get("data_expedicao", "")))
                            edit_data_emissao = st.text_input("Data do Documento:", value="29/09/2026")

                        # Bloco 2: Filiação e Naturalidade
                        st.markdown("##### 👨‍👩‍👧 Filiação e Origem")
                        col_fili1, col_fili2, col_fili3 = st.columns(3)
                        with col_fili1:
                            edit_mae = st.text_input("Nome da Mãe:", value=str(dados_originais.get("nome_mae", dados_originais.get("mae", ""))))
                        with col_fili2:
                            edit_pai = st.text_input("Nome do Pai:", value=str(dados_originais.get("nome_pai", dados_originais.get("pai", ""))))
                        with col_fili3:
                            edit_responsavel = st.text_input("Nome do Responsável:", value=str(dados_originais.get("nome_responsavel", "")))

                        col_orig1, col_orig2, col_orig3 = st.columns(3)
                        with col_orig1:
                            edit_nacionalidade = st.text_input("Nacionalidade:", value=str(dados_originais.get("nacionalidade", "BRASILEIRA")))
                        with col_orig2:
                            edit_naturalidade = st.text_input("Naturalidade:", value=str(dados_originais.get("naturalidade", "")))
                        with col_orig3:
                            edit_uf_nat = st.text_input("UF Naturalidade:", value=str(dados_originais.get("uf", dados_originais.get("uf_nascimento", "DF"))))

                        # Bloco 3: Endereço Completo (Essencial para Passes e Declarações)
                        st.markdown("##### 🏠 Endereço")
                        col_end1, col_end2 = st.columns(2)
                        with col_end1:
                            edit_endereco = st.text_input("Endereço (Logradouro / Número / Bloco):", value=str(dados_originais.get("endereco", "")))
                            edit_cidade = st.text_input("Cidade:", value=str(dados_originais.get("cidade", "PLANALTINA")))
                        with col_end2:
                            edit_bairro = st.text_input("Bairro:", value=str(dados_originais.get("bairro", "")))
                            col_uf_cep1, col_uf_cep2 = st.columns(2)
                            with col_uf_cep1:
                                edit_uf_end = st.text_input("UF Endereço:", value=str(dados_originais.get("uf_endereco", "DF")))
                            with col_uf_cep2:
                                edit_cep = st.text_input("CEP:", value=str(dados_originais.get("cep", "")))

                        # Bloco 4: Observações e Instruções Dinâmicas
                        st.markdown("##### 📋 Observações / Instruções")
                        if tipo_documento == "Renovação de Matrícula":
                            edit_observacao_doc = st.text_area(
                                "Instruções da Ficha de Renovação:",
                                value=(
                                    "1. Deseja renovar a matrícula para o 2º semestre de 2026? [ X ] Sim [  ] Não\n"
                                    "2. Está cursando o Ensino Médio atualmente? [ X ] Sim [  ] Não\n"
                                    "A renovação de matrícula não é automática, portanto, o estudante que não efetiva-la perderá o direito à vaga."
                                ),
                                height=80
                            )
                        elif tipo_documento == "Passe Estudantil":
                            edit_observacao_doc = st.text_area(
                                "Observações do Passe Estudantil:",
                                value="Declaração válida por 30 dias para efeitos de Passe Estudantil.",
                                height=60
                            )
                        else:
                            edit_observacao_doc = st.text_area(
                                "Observações do Documento:",
                                value="Documento emitido conforme registos da instituição.",
                                height=60
                            )

                        botao_gerar_editado = st.form_submit_button("✨ Gerar PDF com Dados Editados")

                    if botao_gerar_editado:
                        dados_customizados = dados_originais.copy()
                        dados_customizados["nome"] = edit_nome
                        dados_customizados["curso"] = edit_curso
                        dados_customizados["turma"] = edit_turma
                        dados_customizados["identidade"] = edit_rg
                        dados_customizados["rg"] = edit_rg
                        dados_customizados["orgao_expeditor"] = edit_orgao
                        dados_customizados["cpf"] = edit_cpf
                        dados_customizados["data_nascimento"] = edit_nasc
                        dados_customizados["sexo"] = edit_sexo
                        dados_customizados["data_expedicao"] = edit_dt_exp
                        dados_customizados["data_emissao"] = edit_data_emissao
                        dados_customizados["nome_mae"] = edit_mae
                        dados_customizados["nome_pai"] = edit_pai
                        dados_customizados["nome_responsavel"] = edit_responsavel
                        dados_customizados["nacionalidade"] = edit_nacionalidade
                        dados_customizados["naturalidade"] = edit_naturalidade
                        dados_customizados["uf"] = edit_uf_nat
                        dados_customizados["endereco"] = edit_endereco
                        dados_customizados["bairro"] = edit_bairro
                        dados_customizados["cidade"] = edit_cidade
                        dados_customizados["cep"] = edit_cep
                        dados_customizados["observacao"] = edit_observacao_doc

                        if tipo_documento == "Renovação de Matrícula":
                            pdf_bytes_gerado = gerar_pdf_renovacao_matricula(dados_customizados)
                            nome_ficheiro = f"renovacao_matricula_{matricula_busca}.pdf"

                        elif tipo_documento == "Passe Estudantil":
                            pdf_bytes_gerado = gerar_pdf_passe_estudantil(dados_customizados)
                            nome_ficheiro = f"passe_estudantil_{matricula_busca}.pdf"

                        elif tipo_documento == "Declaração de Escolaridade":
                            pdf_bytes_gerado = gerar_pdf_declaracao_escolaridade(dados_customizados)
                            nome_ficheiro = f"declaracao_escolaridade_{matricula_busca}.pdf"

                        elif tipo_documento == "Declaração de Conclusão":
                            pdf_bytes_gerado = gerar_pdf_declaracao_escolaridade(dados_customizados)
                            nome_ficheiro = f"declaracao_conclusao_{matricula_busca}.pdf"

                        else:
                            df_para_pdf = df_historico_editado if not df_historico_editado.empty else df_historico_aluno
                            pdf_bytes_gerado = gerar_pdf_historico_aluno(df_para_pdf, dados_customizados)
                            nome_ficheiro = f"historico_oficial_{matricula_busca}.pdf"

                        st.success(f"Documento '{tipo_documento}' gerado com sucesso!")
                        st.download_button(
                            label=f"📥 Descarregar {tipo_documento} (PDF)",
                            data=pdf_bytes_gerado,
                            file_name=nome_ficheiro,
                            mime="application/pdf",
                            use_container_width=True,
                        )

                    st.markdown("---")
                    st.markdown("### 📚 Emissão Unificada em Lote (Turma Inteira)")
                    
                    turma_atual = dados_originais.get("turma")
                    if turma_atual:
                        st.info(f"Turma detetada para emissão em lote: **{turma_atual}**")
                        
                        col_lote1, col_lote2 = st.columns(2)
                        with col_lote1:
                            if st.button("🚀 Gerar Passes de Toda a Turma (PDF Único)", use_container_width=True):
                                with st.spinner("A consolidar passes da turma..."):
                                    df_turma = executar_query("SELECT * FROM TB_PESSOAS WHERE turma = %s", params=(turma_atual,))
                                    if df_turma is not None and not df_turma.empty:
                                        pdf_unificado_bytes = gerar_pdf_passes_turma_unificado(df_turma)
                                        st.success("PDF de passes unificado com sucesso!")
                                        st.download_button(
                                            label="📥 Descarregar Passes Unificados da Turma",
                                            data=pdf_unificado_bytes,
                                            file_name=f"passes_turma_{str(turma_atual).replace('/', '-')}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True,
                                        )
                        with col_lote2:
                            if st.button("🚀 Gerar Fichas de Renovação da Turma (PDF Único)", use_container_width=True):
                                with st.spinner("A consolidar fichas de renovação da turma..."):
                                    df_turma = executar_query("SELECT * FROM TB_PESSOAS WHERE turma = %s", params=(turma_atual,))
                                    if df_turma is not None and not df_turma.empty:
                                        pdf_renovacao_unificado = gerar_pdf_renovacao_turma_unificado(df_turma)
                                        st.success("PDF de renovações unificado com sucesso!")
                                        st.download_button(
                                            label="📥 Descarregar Renovações Unificadas da Turma",
                                            data=pdf_renovacao_unificado,
                                            file_name=f"renovacoes_turma_{str(turma_atual).replace('/', '-')}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True,
                                        )
                    else:
                        st.warning("O aluno selecionado não possui turma associada.")

    except Exception as e:
        st.error(f"Erro ao executar o motor da secretaria: {e}")
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
