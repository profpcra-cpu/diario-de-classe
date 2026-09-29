import io
import pandas as pd
import streamlit as st

from modulos.conexao import executar_query
from modulos.pdf_generator import (
    gerar_pdf_declaracao_escolaridade,
    gerar_pdf_historico_aluno,
    gerar_pdf_passe_estudantil,
    gerar_pdf_passes_turma_unificado,
    # Se tiver uma função específica para conclusão, importe-a aqui também:
    # gerar_pdf_declaracao_conclusao, 
)


def renderizar_modulo_secretaria():
    st.subheader(
        "🎓 Secretaria Escolar - Motor de Ficha Académica e Documentos"
    )
    st.markdown(
        "Selecione o estudante, escolha o tipo de documento, efetue edições pontuais se necessário e emita a documentação oficial."
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
                    st.markdown("### 📝 Editor Personalizado de Documentos (Pré-Impressão)")
                    st.info("Selecione o tipo de documento e ajuste os campos que deseja modificar antes de gerar o ficheiro final PDF.")

                    # Seleção do documento que deseja ajustar e emitir
                    tipo_documento = st.selectbox(
                        "Selecione o Documento a Emitir:",
                        [
                            "Declaração de Escolaridade", 
                            "Passe Estudantil", 
                            "Declaração de Conclusão", 
                            "Histórico Escolar Oficial"
                        ]
                    )

                    dados_originais = df_dados_pessoais.iloc[0].to_dict()

                    # Formulário de Edição Dinâmica dos Campos do Documento
                    with st.form(key=f"form_edicao_doc_{matricula_busca}"):
                        st.markdown(f"**A ajustar dados para:** {tipo_documento}")
                        
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            edit_nome = st.text_input("Nome Completo:", value=str(dados_originais.get("nome", "")))
                            edit_curso = st.text_input("Curso:", value=str(dados_originais.get("curso", "TÉCNICO EM ENFERMAGEM")))
                            edit_turma = st.text_input("Turma / Turno:", value=str(dados_originais.get("turma", "")))
                            edit_rg = st.text_input("Identidade (RG):", value=str(dados_originais.get("identidade", "")))
                        
                        with col_ed2:
                            edit_cpf = st.text_input("CPF:", value=str(dados_originais.get("cpf", "")))
                            edit_nasc = st.text_input("Data de Nascimento:", value=str(dados_originais.get("data_nascimento", "")))
                            edit_sexo = st.text_input("Sexo:", value=str(dados_originais.get("sexo", "")))
                            edit_data_emissao = st.text_input("Data do Documento:", value="29/09/2026")

                        # Campo de texto customizado para observações ou corpo principal (ex: Carga horária total ou texto de conclusão)
                        edit_observacao = st.text_area(
                            "Texto / Observações / Carga Horária Específica:",
                            value=f"O(a) aluno(a) acima supracitado(a) concluiu o referido curso, sendo a carga horária total de horas."
                        )

                        botao_gerar_editado = st.form_submit_button("✨ Gerar PDF com Dados Editados")

                    # Ação executada após submeter o formulário de edição
                    if botao_gerar_editado:
                        # Criar dicionário consolidado com as alterações feitas pelo utilizador
                        dados_customizados = dados_originais.copy()
                        dados_customizados["nome"] = edit_nome
                        dados_customizados["curso"] = edit_curso
                        dados_customizados["turma"] = edit_turma
                        dados_customizados["identidade"] = edit_rg
                        dados_customizados["cpf"] = edit_cpf
                        dados_customizados["data_nascimento"] = edit_nasc
                        dados_customizados["sexo"] = edit_sexo
                        dados_customizados["data_emissao"] = edit_data_emissao
                        dados_customizados["observacao"] = edit_observacao

                        df_para_pdf = (
                            df_historico_editado
                            if not df_historico_editado.empty
                            else df_historico_aluno
                        )

                        # Direciona para a função de PDF correspondente utilizando os dados ajustados
                        if tipo_documento == "Declaração de Escolaridade":
                            pdf_bytes_gerado = gerar_pdf_declaracao_escolaridade(dados_customizados)
                            nome_ficheiro = f"declaracao_escolaridade_{matricula_busca}.pdf"

                        elif tipo_documento == "Passe Estudantil":
                            pdf_bytes_gerado = gerar_pdf_passe_estudantil(dados_customizados)
                            nome_ficheiro = f"passe_estudantil_{matricula_busca}.pdf"

                        elif tipo_documento == "Declaração de Conclusão":
                            # Se tiveres a função de conclusão criada, chame-a aqui. 
                            # Exemplo: pdf_bytes_gerado = gerar_pdf_declaracao_conclusao(dados_customizados)
                            # Caso contrário, pode usar provisoriamente uma base ou adaptar:
                            pdf_bytes_gerado = gerar_pdf_declaracao_escolaridade(dados_customizados) 
                            nome_ficheiro = f"declaracao_conclusao_{matricula_busca}.pdf"

                        else:  # Histórico Escolar Oficial
                            pdf_bytes_gerado = gerar_pdf_historico_aluno(df_para_pdf, dados_customizados)
                            nome_ficheiro = f"historico_oficial_{matricula_busca}.pdf"

                        st.success(f"Documento '{tipo_documento}' gerado com sucesso com base nas edições efetuadas!")
                        
                        st.download_button(
                            label=f"📥 Descarregar {tipo_documento} (PDF)",
                            data=pdf_bytes_gerado,
                            file_name=nome_ficheiro,
                            mime="application/pdf",
                            use_container_width=True,
                        )

                    # ---------------------------------------------------------
                    # EMISSÃO UNIFICADA EM LOTE (POR TURMA)
                    # ---------------------------------------------------------
                    st.markdown("---")
                    st.markdown("### 📚 Emissão Unificada em Lote (Turma Inteira)")
                    
                    turma_atual = dados_originais.get("turma")
                    if turma_atual:
                        st.info(f"Turma detetada para emissão unificada: **{turma_atual}**")
                        
                        if st.button("🚀 Gerar PDF Único com Passes de Toda a Turma", use_container_width=True):
                            with st.spinner("A consolidar os documentos de todos os alunos num único PDF..."):
                                df_turma = executar_query(
                                    "SELECT * FROM TB_PESSOAS WHERE turma = %s",
                                    params=(turma_atual,)
                                )
                                
                                if df_turma is not None and not df_turma.empty:
                                    pdf_unificado_bytes = gerar_pdf_passes_turma_unificado(df_turma)
                                    st.success(f"PDF unificado gerado com sucesso! {len(df_turma)} alunos incluídos.")
                                    
                                    st.download_button(
                                        label=f"📥 Descarregar PDF Único da Turma {turma_atual}",
                                        data=pdf_unificado_bytes,
                                        file_name=f"passes_unificados_turma_{str(turma_atual).replace('/', '-')}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True,
                                    )
                                else:
                                    st.warning("Não foram encontrados outros alunos para esta turma.")
                    else:
                        st.warning("O aluno selecionado não possui uma turma associada no cadastro.")

    except Exception as e:
        st.error(f"Erro ao executar o motor da secretaria: {e}")
