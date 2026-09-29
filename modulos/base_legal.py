import streamlit as st
from modulos.conexao import executar_query

def renderizar_modulo_base_legal():
    st.subheader("⚖️ Central de Gestão - Base Legal e Competências por Turma")
    st.markdown("Consulte, edite ou acrescente novas diretrizes legais e matrizes curriculares aplicadas por turma e sigla.")
    
    aba_bl_consulta, aba_bl_novo = st.tabs(["🔍 Consultar e Editar Existentes", "➕ Acrescentar Nova Base Legal"])
    
    with aba_bl_consulta:
        try:
            df_base_legal = executar_query("SELECT * FROM TB_BASE_LEGAL")
            if df_base_legal.empty:
                st.info("A tabela TB_BASE_LEGAL está vazia. Utilize a aba ao lado para acrescentar registos.")
            else:
                pesquisa_bl = st.text_input("Filtrar por Sigla ou Turma:", key="filtro_bl")
                df_filtrado = df_base_legal
                if pesquisa_bl:
                    df_filtrado = df_base_legal[
                        df_base_legal['sigla'].str.contains(pesquisa_bl, case=False, na=False) | 
                        df_base_legal['turma'].str.contains(pesquisa_bl, case=False, na=False)
                    ]
                
                df_bl_editado = st.data_editor(df_filtrado, use_container_width=True, key="editor_base_legal")
                
                if st.button("💾 Guardar Alterações da Base Legal"):
                    with st.spinner("A atualizar base de dados..."):
                        atualizados_bl = 0
                        for _, row in df_bl_editado.iterrows():
                            reg_id = row.get('id')
                            if reg_id:
                                sql_upd_bl = """
                                    UPDATE TB_BASE_LEGAL 
                                    SET sigla = %s, turma = %s, base_legal = %s, competencias_habilidades = %s 
                                    WHERE id = %s
                                """
                                executar_query(
                                    sql_upd_bl, 
                                    params=(row.get('sigla'), row.get('turma'), row.get('base_legal'), row.get('competencias_habilidades'), reg_id), 
                                    fetch=False
                                )
                                atualizados_bl += 1
                        st.success(f"Sucesso! {atualizados_bl} registos atualizados em TB_BASE_LEGAL.")
                        st.rerun()
        except Exception as e:
            st.error(f"Erro ao aceder à tabela TB_BASE_LEGAL: {e}")
            
    with aba_bl_novo:
        st.markdown("### Registar Nova Base Legal e Competências para Turma/Sigla")
        with st.form("form_nova_base_legal"):
            col_nb1, col_nb2 = st.columns(2)
            with col_nb1:
                nova_sigla = st.text_input("Sigla (ex: TEN):").strip()
            with col_nb2:
                nova_turma = st.text_input("Turma (ex: 26201A):").strip()
                
            nova_base_legal_txt = st.text_area("Base Legal:")
            novas_competencias_txt = st.text_area("Competências / Habilidades:")
            
            if st.form_submit_button("➕ Inserir Novo Registo"):
                if nova_sigla and nova_turma:
                    try:
                        sql_ins_bl = """
                            INSERT INTO TB_BASE_LEGAL (sigla, turma, base_legal, competencias_habilidades) 
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                base_legal = VALUES(base_legal), 
                                competencias_habilidades = VALUES(competencias_habilidades)
                        """
                        executar_query(sql_ins_bl, params=(nova_sigla, nova_turma, nova_base_legal_txt, novas_competencias_txt), fetch=False)
                        st.success(f"Base legal para a turma {nova_turma} (Sigla: {nova_sigla}) inserida/atualizada com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao inserir dados na base de dados: {e}")
                else:
                    st.warning("Os campos 'Sigla' e 'Turma' são obrigatórios.")
