import streamlit as st
from datetime import date
from modulos.conexao import executar_query

def renderizar_modulo_notas():
    st.subheader("📋 Matriz de Notas e Avaliações")
    perfil_atual = st.session_state.get("perfil", "professor")
    email_atual = st.session_state.get("email_utilizador", "")
    
    try:
        if perfil_atual == "admin":
            query_notas = "SELECT matricula, turma, iduc, av1, av2, av3, soma, recup FROM TB_AVALIACOES LIMIT 35"
            df_diario = executar_query(query_notas)
        else:
            query_notas = """
                SELECT AV.matricula, AV.turma, AV.iduc, AV.av1, AV.av2, AV.av3, AV.soma, AV.recup 
                FROM TB_AVALIACOES AV
                JOIN TB_PROFESSORES P ON AV.turma = P.turma AND AV.iduc = P.iduc
                WHERE P.e_mail = %s
            """
            df_diario = executar_query(query_notas, params=(email_atual,))
            
        if df_diario.empty:
            st.info("Não existem avaliações associadas às suas turmas/disciplinas.")
        else:
            df_diario_editado = st.data_editor(
                df_diario, 
                use_container_width=True, 
                key="editor_diario_notas",
                disabled=["matricula", "turma", "iduc"]
            )
            
            if st.button("💾 Guardar Notas em TB_AVALIACOES"):
                atualizados = 0
                for _, row in df_diario_editado.iterrows():
                    mat = row.get('matricula')
                    if mat:
                        sql_upd = """
                            UPDATE TB_AVALIACOES 
                            SET av1 = %s, av2 = %s, av3 = %s, soma = %s, recup = %s 
                            WHERE matricula = %s AND turma = %s AND iduc = %s
                        """
                        executar_query(
                            sql_upd, 
                            params=(
                                row.get('av1', 0), 
                                row.get('av2', 0), 
                                row.get('av3', 0), 
                                row.get('soma', 0), 
                                row.get('recup', 0), 
                                mat,
                                row.get('turma'),
                                row.get('iduc')
                            ), 
                            fetch=False
                        )
                        atualizados += 1
                st.success(f"Sucesso! {atualizados} registos de avaliações atualizados.")
    except Exception as e:
        st.error(f"Erro ao gerir avaliações: {e}")


def renderizar_modulo_diario_frequencia():
    st.subheader("📖 Diário de Classe Dinâmico por Data")
    perfil_atual = st.session_state.get("perfil", "professor")
    email_atual = st.session_state.get("email_utilizador", "")
    
    # 1. Busca turmas e IDUCs autorizados na TB_PROFESSORES
    if perfil_atual == "admin":
        df_turmas = executar_query("SELECT DISTINCT turma FROM TB_PROFESSORES")
        df_iducs = executar_query("SELECT DISTINCT iduc FROM TB_PROFESSORES")
    else:
        df_turmas = executar_query("SELECT DISTINCT turma FROM TB_PROFESSORES WHERE e_mail = %s", params=(email_atual,))
        df_iducs = executar_query("SELECT DISTINCT iduc FROM TB_PROFESSORES WHERE e_mail = %s", params=(email_atual,))

    lista_turmas = df_turmas['turma'].tolist() if not df_turmas.empty else []
    lista_iducs = df_iducs['iduc'].tolist() if not df_iducs.empty else []

    if not lista_turmas:
        st.warning("Não tem turmas associadas ao seu e-mail na tabela `TB_PROFESSORES`.")
        return

    col_turma, col_iduc, col_data_nova = st.columns([2, 2, 2])
    with col_turma:
        turma_diario = st.selectbox("Turma Ativa:", lista_turmas)
    with col_iduc:
        iduc_diario = st.selectbox("Unidade Curricular (IDUC):", lista_iducs) if lista_iducs else st.text_input("IDUC:", "TE024")
    with col_data_nova:
        nova_data_aula = st.date_input("Adicionar Nova Data de Aula:", value=date.today())
        
    if st.button("➕ Registar Nova Aula"):
        try:
            sql_nova_aula = "INSERT INTO TB_DIARIO (turma, iduc, data, aulas_previstas) VALUES (%s, %s, %s, %s)"
            executar_query(sql_nova_aula, params=(turma_diario, iduc_diario, str(nova_data_aula), 4), fetch=False)
            st.success(f"Aula do dia {nova_data_aula} registrada com sucesso na TB_DIARIO!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao registar aula em TB_DIARIO: {e}")
            
    st.markdown("---")
    tab1, tab2 = st.tabs(["📝 Procedimentos e Competências", "👥 Matriz de Frequência por Datas"])
    
    with tab1:
        st.markdown("### Registo Pedagógico da Aula Selecionada")
        proc_init, comp_init = "", ""
        
        # Consulta de registros pedagógicos nas tabelas TB_PROCEDIMENTOS e TB_COMPETENCIAS
        try:
            sql_p = "SELECT texto FROM TB_PROCEDIMENTOS WHERE turma = %s AND iduc = %s AND data = %s LIMIT 1"
            df_p = executar_query(sql_p, params=(turma_diario, iduc_diario, str(nova_data_aula)))
            if not df_p.empty:
                proc_init = df_p['texto'].iloc[0] or ""

            sql_c = "SELECT texto FROM TB_COMPETENCIAS WHERE turma = %s AND iduc = %s AND data = %s LIMIT 1"
            df_c = executar_query(sql_c, params=(turma_diario, iduc_diario, str(nova_data_aula)))
            if not df_c.empty:
                comp_init = df_c['texto'].iloc[0] or ""
        except Exception as e_pedagogico:
            st.info("Aguardando preenchimento dos registros pedagógicos para esta aula.")

        procedimentos = st.text_area("Procedimentos Metodológicos adotados:", value=proc_init, key="txt_proc")
        competencias = st.text_area("Competências / Habilidades desenvolvidas:", value=comp_init, key="txt_comp")
        
        if st.button("💾 Guardar Registo Pedagógico"):
            try:
                # Gravação/Atualização em TB_PROCEDIMENTOS
                sql_upd_proc = """
                    INSERT INTO TB_PROCEDIMENTOS (turma, iduc, data, texto) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE texto = VALUES(texto)
                """
                executar_query(sql_upd_proc, params=(turma_diario, iduc_diario, str(nova_data_aula), procedimentos), fetch=False)
                
                # Gravação/Atualização em TB_COMPETENCIAS
                sql_upd_comp = """
                    INSERT INTO TB_COMPETENCIAS (turma, iduc, data, texto) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE texto = VALUES(texto)
                """
                executar_query(sql_upd_comp, params=(turma_diario, iduc_diario, str(nova_data_aula), competencias), fetch=False)
                
                st.success("Procedimentos e Competências gravados com sucesso!")
            except Exception as e:
                st.error(f"Erro ao guardar registro pedagógico: {e}")

    with tab2:
        st.markdown("### Controlo de Presenças")
        try:
            # Lista de estudantes cadastrados da turma via TB_PESSOAS
            df_alunos = executar_query(
                "SELECT matricula, nome FROM TB_PESSOAS WHERE turma = %s AND perfil = 'aluno'", 
                params=(turma_diario,)
            )
            
            if df_alunos.empty:
                # Fallback genérico de alunos
                df_alunos = executar_query("SELECT DISTINCT matricula FROM TB_AVALIACOES WHERE turma = %s", params=(turma_diario,))
            
            if df_alunos.empty:
                st.warning("Nenhum aluno cadastrado encontrado para esta turma.")
            else:
                # Datas de aulas registradas na TB_DIARIO
                df_datas = executar_query(
                    "SELECT DISTINCT data FROM TB_DIARIO WHERE turma = %s AND iduc = %s ORDER BY data", 
                    params=(turma_diario, iduc_diario)
                )
                lista_datas = df_datas['data'].astype(str).tolist() if not df_datas.empty else [str(nova_data_aula)]
                
                df_matriz_freq = df_alunos.copy()
                for d in lista_datas:
                    df_matriz_freq[f"Aula: {d}"] = True
                
                df_editado = st.data_editor(
                    df_matriz_freq, 
                    use_container_width=True, 
                    key="editor_freq_dinamica",
                    disabled=["matricula", "nome"] if "nome" in df_matriz_freq.columns else ["matricula"]
                )
                
                if st.button("💾 Guardar Frequências na TB_FREQUENCIA"):
                    gravados = 0
                    for _, row in df_editado.iterrows():
                        mat = row['matricula']
                        for d in lista_datas:
                            presenca = 1 if row[f"Aula: {d}"] else 0
                            sql_freq = """
                                INSERT INTO TB_FREQUENCIA (matricula, turma, iduc, data, presente)
                                VALUES (%s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE presente = VALUES(presente)
                            """
                            executar_query(sql_freq, params=(mat, turma_diario, iduc_diario, d, presenca), fetch=False)
                            gravados += 1
                    st.success(f"Frequências registradas com sucesso na `TB_FREQUENCIA` ({gravados} lançamentos)!")
        except Exception as e:
            st.error(f"Erro ao processar matriz de frequências: {e}")
