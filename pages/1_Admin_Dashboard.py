import streamlit as st
import pandas as pd
import psutil
from db import get_dashboard_metrics, add_improvement, get_improvements, delete_improvement, toggle_improvement_status, get_top_activities

# Verificação de segurança
if "logado" not in st.session_state or not st.session_state.logado:
    st.switch_page("app.py")

if not st.session_state.user_info.get("is_admin"):
    st.error("Acesso Negado. Você não é um administrador.")
    st.stop()

with st.sidebar:
    st.header("⚙️ Configurações da Conta")
    if st.button("🚪 Sair com segurança", use_container_width=True):
        st.session_state.logado = False
        st.session_state.user_info = None
        st.session_state.current_session_id = None
        st.switch_page("app.py")
    
    st.markdown("---")
    st.page_link("pages/2_Chat_Agente.py", label="💬 Ir para o Chat", icon="🗣️")

st.title("🛡️ Painel de Gestão e Dashboard")
st.markdown("Visão global da plataforma e controle de melhorias.")

tot_us, onb_us, all_us = get_dashboard_metrics()

c1, c2, c3 = st.columns(3)
c1.metric("Total de Cadastros", tot_us)
c2.metric("Assinantes Ativos", tot_us) # MVP: todos do banco local sao assinantes
c3.metric("Onboarding Concluído", onb_us)

st.markdown("---")
st.subheader("🖥️ Monitoramento de Plataforma")
col_cpu, col_ram = st.columns(2)

cpu_percent = psutil.cpu_percent(interval=None) # pega instante
ram_info = psutil.virtual_memory()

# Alert logic 90%
if cpu_percent >= 90.0 or ram_info.percent >= 90.0:
    st.error(f"⚠️ ALERTA CRÍTICO: Capacidade da plataforma operando acima de 90%! (CPU {cpu_percent}% / RAM {ram_info.percent}%)")

col_cpu.metric(label="Uso de Processamento (CPU)", value=f"{cpu_percent}%")
col_ram.metric(label="Uso de Memória (RAM)", value=f"{ram_info.percent}%")

st.markdown("#### 🔥 Atividades de Maior Consumo")
top_acts = get_top_activities()
if top_acts:
    df_acts = pd.DataFrame(top_acts, columns=["Tipo de Atividade (Feature)", "Total de Ocorrências"])
    st.dataframe(df_acts, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum dado de uso registrado ainda pelas atividades do sistema.")

st.markdown("---")
st.subheader("👥 Usuários da Plataforma")
if all_us:
    df_users = pd.DataFrame(all_us, columns=["ID", "Nome", "E-mail", "Assinante", "Onboarded", "Admin?", "Telefone", "Endereço", "Nome de Usuário"])
    st.dataframe(df_users, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🕵️‍♂️ Gestão e Auditoria de Contas")
    user_dict = {f"ID {u[0]} - {u[1]} ({u[8]})": u[0] for u in all_us}
    selected_user_str = st.selectbox("Selecione um usuário para auditar ou gerenciar:", [""] + list(user_dict.keys()))
    
    if selected_user_str:
        user_id = user_dict[selected_user_str]
        st.write(f"**Ações para o usuário ID {user_id}:**")
        
        if st.button("🚨 EXCLUIR CONTA E DADOS", type="primary"):
            from db import delete_user
            delete_user(user_id)
            st.success("Usuário e todo seu histórico foram removidos com sucesso.")
            if user_id == st.session_state.user_info["id"]:
                st.session_state.logado = False
            st.rerun()
                
        st.markdown("#### Histórico de Interações (Auditoria)")
        from db import get_user_sessions, get_session_messages
        sessoes = get_user_sessions(user_id)
        if not sessoes:
            st.info("Este usuário ainda não interagiu com a IA.")
        else:
            for sid, stitle in sessoes:
                with st.expander(f"Sessão {sid}: {stitle}"):
                    msgs = get_session_messages(sid)
                    for m in msgs:
                        if m["role"] == "user":
                            st.markdown(f"**🧑 Usuário:** {m['content']}")
                        else:
                            st.markdown(f"**🤖 IA:** {m['content']}")
else:
    st.info("Nenhum usuário encontrado.")
    
st.markdown("---")
st.subheader("🚀 Roadmap e Gestão de Melhorias")

with st.form("form_imp", clear_on_submit=True):
    colA, colB = st.columns([0.8, 0.2])
    nova_ideia = colA.text_input("Nova Feature, Ideia ou Bug para arrumar:")
    submitted = colB.form_submit_button("Adicionar")
    if submitted and nova_ideia:
        add_improvement(nova_ideia)
        st.rerun()

st.markdown("#### Backlog Atual")
items = get_improvements()
for imp in items:
    with st.container():
        col1, col2, col3, col4 = st.columns([0.1, 0.6, 0.15, 0.15])
        if imp[2] == 'Concluído':
            col1.write("✅")
            col2.write(f"~~{imp[1]}~~")
        else:
            col1.write("⏳")
            col2.write(imp[1])
            
        if col3.button("🔄 Toggle", key=f"tg_{imp[0]}"):
            toggle_improvement_status(imp[0], imp[2])
            st.rerun()
        if col4.button("🗑️ Del", key=f"dl_{imp[0]}"):
            delete_improvement(imp[0])
            st.rerun()
