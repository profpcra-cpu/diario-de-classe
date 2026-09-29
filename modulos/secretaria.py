import pandas as pd
import streamlit as st

from modulos.conexao import executar_query
from modulos.pdf_generator import (
    gerar_pdf_declaracao_escolaridade,
    gerar_pdf_historico_aluno,
    gerar_pdf_passe_estudantil,  # <--- Importado a nova função do passe estudantil
)


def renderizar_modulo_secretaria():
    st.subheader(
        "🎓 Secretaria Escolar - Motor de Ficha Académica e Documentos"
    )
    st.markdown(
        "Selecione o estudante para consultar a ficha cadastral unificada, histórico curricular e emitir documentos oficiais."
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
                        "📚 Histórico e Emissão de Documentos",
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
                            "💾 Guardar Alterações Cadastrais"
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
                # ABA 2: HISTÓRICO E EMISSÃO DE DOCUMENTOS
                # -------------------------------------------------------------
                with aba_historico:
                    st.markdown(
                        "### Histórico Curricular e Notas Associadas (TB_DIARIO)"
                    )
                    df_historico_aluno = executar_query(
                        "SELECT * FROM TB_DIARIO WHERE matricula = %s",
                        params=(matricula_busca,),
                    )

                    if (
                        df_historico_aluno is None
                        or df_historico_aluno.empty
                    ):
                        st.info(
                            "Não existem registos curriculares na TB_DIARIO para este aluno."
                        )
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
                                for (
                                    _,
                                    row,
                                ) in df_historico_editado.iterrows():
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
                                st.success(
                                    f"Sucesso! {atualizados_hist} registos guardados."
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao guardar histórico: {e}")

                    st.markdown("---")
                    st.markdown(
                        "### 🖨️ Central de Emissão de Documentos Académicos"
                    )

                    dados_dict = df_dados_pessoais.iloc[0].to_dict()
                    df_para_pdf = (
                        df_historico_editado
                        if not df_historico_editado.empty
                        else df_historico_aluno
                    )

                    # Organizado em 3 colunas para acomodar os botões de emissão
                    col_doc1, col_doc2, col_doc3 = st.columns(3)

                    with col_doc1:
                        # Emissão de Declaração de Escolaridade
                        pdf_dec_bytes = gerar_pdf_declaracao_escolaridade(
                            dados_dict
                        )
                        st.download_button(
                            label="📜 Descarregar Declaração de Escolaridade (PDF)",
                            data=pdf_dec_bytes,
                            file_name=f"declaracao_{matricula_busca}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                    with col_doc2:
                        # Emissão de Passe Estudantil
                        pdf_passe_bytes = gerar_pdf_passe_estudantil(
                            dados_dict
                        )
                        st.download_button(
                            label="🚌 Descarregar Passe Estudantil (PDF)",
                            data=pdf_passe_bytes,
                            file_name=f"passe_estudantil_{matricula_busca}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                    with col_doc3:
                        # Emissão de Histórico Escolar
                        pdf_hist_bytes = gerar_pdf_historico_aluno(
                            df_para_pdf, dados_dict
                        )
                        st.download_button(
                            label="🎓 Descarregar Histórico Escolar Oficial (PDF)",
                            data=pdf_hist_bytes,
                            file_name=f"historico_{matricula_busca}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

    except Exception as e:
        st.error(f"Erro ao executar o motor da secretaria: {e}")
