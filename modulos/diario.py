import streamlit as st
from datetime import date
from modulos.conexao import executar_query

def renderizar_modulo_notas():
    st.subheader("📋 Matriz de Notas e Avaliações")
    perfil_atual = st.session_state.get("perfil", "professor")
    email_atual = st.session_state.get("email_utilizador", "")
    
    try:
        if perfil_atual == "admin":
            query_notas = "SELECT matrícula, turma, iduc, av1, av2, av3, soma, recup FROM TB_AVALIACOES LIMIT 35"
            df_diario = executar_query(query_notas)
        else:
            query_notas = """
                SELECT AV.matrícula, AV.turma, AV.iduc, AV.av1, AV.av2, AV.av3, AV.soma, AV.recup 
                FROM TB_AVALIACOES AV
                JOIN TB_PROFESSORES P ON AV.turma = P.turma AND AV.iduc = P.iduc
                WHERE P.e_mail = %s
            """
            df_diario = executar_query(query_notas, params=(email_atual,))
            
        if df_diario.empty:
            st.info("Não existem avaliações associadas às suas turmas/disciplinas.")
        else:
            df_diario_editado = st.data_editor(df_diario, use_container_width=True, key="editor_diario_notas")
            
            if st.button("💾 Guardar Notas em TB_AVALIACOES"):
                atualizados = 0
                for _, row in df_diario_editado.iterrows():
                    mat = row.get('matrícula')
                    if mat:
                        sql_upd = "UPDATE TB_AVALIACOES SET av1 = %s, av2 = %s, av3 = %s, soma = %s, recup = %s WHERE matrícula = %s"
                        executar_query(sql_upd, params=(row.get('av1', 0), row.get('av2', 0), row.get('av3', 0), row.get('soma', 0), row.get('recup', 0), mat), fetch=False)
                        atualizados += 1
                st.success(f"Sucesso! {atualizados} registos de avaliações atualizados.")
    except Exception as e:
        st.error(f"Erro ao gerir avaliações: {e}")

def renderizar_modulo_diario_frequencia():
    st.subheader("📖 Diário de Classe Dinâmico por Data")
    perfil_atual = st.session_state.get("perfil", "professor")
    email_atual = st.session_state.get("email_utilizador", "")
    
    if perfil_atual == "admin":
        df_turmas_permitidas = executar_query("SELECT DISTINCT turma FROM TB_PROFESSORES")
        lista_turmas = df_turmas_permitidas['turma'].tolist() if not df_turmas_permitidas.empty else ["25201A", "26201A"]
        
        df_iducs_permitidos = executar_query("SELECT DISTINCT iduc FROM TB_PROFESSORES")
        lista_iducs = df_iducs_permitidos['iduc'].tolist() if not df_iducs_permitidos.empty else ["TE024"]
    else:
        df_turmas_permitidas = executar_query("SELECT DISTINCT turma FROM TB_PROFESSORES WHERE e_mail = %s", params=(email_atual,))
        lista_turmas = df_turmas_permitidas['turma'].tolist() if not df_turmas_permitidas.empty else []
        
        df_iducs_permitidos = executar_query("SELECT DISTINCT iduc FROM TB_PROFESSORES WHERE e_mail = %s", params=(email_atual,))
        lista_iducs = df_iducs_permitidos['iduc'].tolist() if not df_iducs_permitidos.empty else []

    if not lista_turmas:
        st.warning("Não tem turmas associadas ao seu e-mail na tabela `TB_PROFESSORES`.")
    else:
        col_turma, col_iduc, col_data_nova = st.columns([2, 2, 2])
        with col_turma:
            turma_diario = st.selectbox("Turma Ativa:", lista_turmas)
        with col_iduc:
            iduc_diario = st.selectbox("Unidade Curricular (IDUC):", lista_iducs) if lista_iducs else st.text_input("IDUC:", "TE024")
        with col_data_nova:
            nova_data_aula = st.date_input("Adicionar Nova Data de Aula:", value=date.today())
            
        if st.button("➕ Registar Nova Aula (Criar Coluna de Data)"):
            try:
                sql_nova_data = "INSERT INTO TB_DIARIO (turma, iduc, data, aulas_previstas) VALUES (%s, %s, %s, %s)"
                executar_query(sql_nova_data, params=(turma_diario, iduc_diario, str(nova_data_aula), 4), fetch=False)
                st.success(f"Aula do dia {nova_data_aula} adicionada com sucesso ao diário!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao registar aula: {e}")
                
        st.markdown("---")
        tab1, tab2 = st.tabs(["📝 Procedimentos e Competências", "👥 Matriz de Frequência por Datas"])
        
        with tab1:
            st.markdown("### Registo Pedagógico da Aula Selecionada")
            
            # Carrega registros existentes para a turma/iduc/data selecionados
            proc_val, comp_val = "", ""
            try:
                df_proc = executar_query("SELECT texto FROM TB_PROCEDIMENTOS WHERE turma = %s AND iduc = %s AND data = %s LIMIT 1", params=(turma_diario, iduc_diario, str(nova_data_aula)))
                if not df_proc.empty:
                    proc_val = df_proc['texto'].iloc[0] or ""
                
                df_comp = executar_query("SELECT texto FROM TB_COMPETENCIAS WHERE turma = %s AND iduc = %s AND data = %s LIMIT 1", params=(turma_diario, iduc_diario, str(nova_data_aula)))
                if not df_comp.empty:
                    comp_val = df_comp['texto'].iloc[0] or ""
            except Exception:
                pass

            txt_procedimentos = st.text_area("Procedimentos Metodológicos adotados:", value=proc_val, key="area_proc")
            txt_competencias = st.text_area("Competências / Habilidades desenvolvidas:", value=comp_val, key="area_comp")
            
            if st.button("💾 Guardar Registo Pedagógico"):
                try:
                    sql_p = "INSERT INTO TB_PROCEDIMENTOS (turma, iduc, data, texto) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE texto = VALUES(texto)"
                    executar_query(sql_p, params=(turma_diario, iduc_diario, str(nova_data_aula), txt_procedimentos), fetch=False)
                    
                    sql_c = "INSERT INTO TB_COMPETENCIAS (turma, iduc, data, texto) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE texto = VALUES(texto)"
                    executar_query(sql_c, params=(turma_diario, iduc_diario, str(nova_data_aula), txt_competencias), fetch=False)
                    
                    st.success("Registo pedagógico atualizado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao guardar registro pedagógico: {e}")

        with tab2:
            st.markdown("### Controlo de Presenças com Colunas Dinâmicas de Datas")
            try:
                # Busca alunos com nome e matrícula direto da TB_PESSOAS
                df_alunos = executar_query("SELECT matricula, nome FROM TB_PESSOAS WHERE turma = %s ORDER BY nome", params=(turma_diario,))
                
                # Fallback para o comportamento anterior caso não encontre na TB_PESSOAS
                if df_alunos.empty:
                    df_alunos = executar_query("SELECT DISTINCT matricula, turma FROM TB_DIARIO WHERE turma = %s LIMIT 30", params=(turma_diario,))

                try:
                    df_datas = executar_query("SELECT DISTINCT data FROM TB_DIARIO WHERE turma = %s AND iduc = %s ORDER BY data", params=(turma_diario, iduc_diario))
                    lista_datas = df_datas['data'].astype(str).tolist() if not df_datas.empty else [str(nova_data_aula)]
                except Exception:
                    lista_datas = [str(nova_data_aula)]
                    
                df_matriz_freq = df_alunos.copy()
                for d in lista_datas:
                    df_matriz_freq[f"Aula: {d}"] = True
                    
                df_editado = st.data_editor(df_matriz_freq, use_container_width=True, key="editor_freq_dinamica")
                
                if st.button("💾 Guardar Frequências da Matriz"):
                    try:
                        total_presencas = 0
                        for _, row in df_editado.iterrows():
                            mat = row['matricula']
                            for d in lista_datas:
                                pres = 1 if row[f"Aula: {d}"] else 0
                                sql_f = """
                                    INSERT INTO TB_FREQUENCIA (matricula, turma, iduc, data, presente) 
                                    VALUES (%s, %s, %s, %s, %s) 
                                    ON DUPLICATE KEY UPDATE presente = VALUES(presente)
                                """
                                executar_query(sql_f, params=(mat, turma_diario, iduc_diario, d, pres), fetch=False)
                                total_presencas += 1
                        st.success(f"Todas as frequências por data foram guardadas com sucesso na TB_FREQUENCIA ({total_presencas} registros)!")
                    except Exception as e_freq:
                        st.error(f"Erro ao salvar frequências: {e_freq}")
            except Exception as e:
                st.error(f"Erro ao carregar matriz de frequências: {e}")
