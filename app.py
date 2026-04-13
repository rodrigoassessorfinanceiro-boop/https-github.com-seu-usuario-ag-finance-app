import streamlit as st
import time
from dotenv import load_dotenv
from db import init_db, create_user, verify_login

load_dotenv(override=True)
init_db()

st.set_page_config(page_title="AG Finance", page_icon="💰", layout="centered", initial_sidebar_state="expanded")

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# Se já estiver logado, levamos para a tela principal (O Agente)
if st.session_state.logado:
    st.switch_page("pages/2_Chat_Agente.py")

st.title("💰 AG Finance - Acesso Premium")
st.markdown("<p style='text-align: center; font-style: italic; color: #6B7280; font-size: 0.9em; margin-bottom: 20px;'>Somos um assistente virtual que ajuda a resolver a sua vida financeira!</p>", unsafe_allow_html=True)
st.markdown("Crie sua conta ou faça login para acessar a inteligência financeira mais avançada do mercado.")

tab_login, tab_cadastro, tab_devel = st.tabs(["🔒 Entrar", "💳 Cadastre-se", "🛠️ Teste Rápido (Dev)"])

with tab_login:
    email_login = st.text_input("E-mail corporativo ou pessoal")
    senha_login = st.text_input("Senha", type="password", key="login_pass")
    if st.button("Acessar Plataforma"):
        sucesso, user = verify_login(email_login, senha_login)
        if sucesso:
            st.session_state.logado = True
            st.session_state.user_info = user
            st.switch_page("pages/2_Chat_Agente.py")
        else:
            st.error("Credenciais inválidas. Tente novamente.")
            
with tab_cadastro:
    st.subheader("1. Dados para a Conta")
    nome_cad = st.text_input("Nome Completo")
    email_cad = st.text_input("Crie um E-mail de acesso")
    telefone_cad = st.text_input("Número de Telefone (WhatsApp)")
    endereco_cad = st.text_input("Endereço Completo")
    senha_cad = st.text_input("Crie uma Senha Forte", type="password", key="cad_pass")
    
    st.markdown("---")
    st.subheader("2. Checkout Seguro Integrado")
    st.markdown("<small style='color:#a1a1aa;'><i>Simulação de pagamento: Esteja à vontade para usar dados fictícios.</i></small>", unsafe_allow_html=True)
    num_cartao = st.text_input("Número do Cartão de Crédito", placeholder="✓ ✓ ✓ ✓   ✓ ✓ ✓ ✓   ✓ ✓ ✓ ✓   ✓ ✓ ✓ ✓")
    col1, col2 = st.columns(2)
    validade = col1.text_input("Validade", placeholder="MM/AA")
    cvc = col2.text_input("CVC", type="password", placeholder="***")
    
    if st.button("Concluir Assinatura AG Finance", type="primary", use_container_width=True):
        if not nome_cad or not email_cad or not telefone_cad or not endereco_cad or not senha_cad or not num_cartao or not validade or not cvc:
            st.warning("⚠️ Preencha todos os campos do formulário.")
        else:
            with st.spinner("💳 Processando pagamento na operadora..."):
                time.sleep(2)
                sucesso, msg = create_user(nome_cad, email_cad, senha_cad, telefone_cad, endereco_cad)
            if sucesso:
                st.success("🎉 Pagamento Aprovado! Bem-vindo(a) à AG Finance.")
                time.sleep(1.5)
                _, user = verify_login(email_cad, senha_cad)
                st.session_state.logado = True
                st.session_state.user_info = user
                st.switch_page("pages/2_Chat_Agente.py")
            else:
                st.error(msg)
                
with tab_devel:
    st.subheader("Atalho de Desenvolvimento")
    st.info("Pule as etapas de cadastro para verificar imediatamente como o aplicativo reage aos dois tipos de conta.")
    col_dev1, col_dev2 = st.columns(2)
    
    if col_dev1.button("👨‍💼 Entrar como Comum", type="secondary", use_container_width=True):
        create_user("Tester Comum", "comum@ag.bot", "123456", "11988887777", "Rua do Teste, 123")
        _, temp_user = verify_login("comum@ag.bot", "123456")
        st.session_state.logado = True
        st.session_state.user_info = temp_user
        st.switch_page("pages/2_Chat_Agente.py")
        
    if col_dev2.button("👑 Entrar como Admin", type="primary", use_container_width=True):
        create_user("Mestre Admin", "admin@ag.bot", "123456", "11911112222", "Av. dos Admins, 456")
        import sqlite3
        conn = sqlite3.connect("users.db")
        try:
            conn.execute("UPDATE users SET is_admin = 1 WHERE email = 'admin@ag.bot'")
            conn.commit()
        except:
            pass
        conn.close()
        
        _, temp_user = verify_login("admin@ag.bot", "123456")
        if temp_user:
            temp_user['is_admin'] = True
        st.session_state.logado = True
        st.session_state.user_info = temp_user
        st.switch_page("pages/2_Chat_Agente.py")

st.stop()
