import streamlit as st
import time
from dotenv import load_dotenv
from db import init_db, create_user, verify_login
from streamlit_option_menu import option_menu

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

opcao_menu = option_menu(
    menu_title=None,
    options=["Quem Somos", "Contato", "Login"],
    icons=["book", "envelope", "box-arrow-in-right"],
    menu_icon="cast",
    default_index=2,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "transparent", "box-shadow": "none"},
        "icon": {"color": "#FFA500", "font-size": "18px"},
        "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#222"},
        "nav-link-selected": {"background-color": "#1E90FF"},
    }
)

if opcao_menu == "Login":
    st.title("💰 AG Finance - Acesso Premium")
    st.markdown("<p style='text-align: center; font-style: italic; color: #6B7280; font-size: 0.9em; margin-bottom: 20px;'>Somos um assistente virtual que ajuda a resolver a sua vida financeira!</p>", unsafe_allow_html=True)
    st.markdown("Crie sua conta ou faça login para acessar a inteligência financeira mais avançada do mercado.")
    
    tab_login, tab_cadastro = st.tabs(["🔒 Entrar", "💳 Cadastre-se"])
    
    with tab_login:
        email_login = st.text_input("E-mail ou Nome de Usuário")
        senha_login = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Acessar Plataforma"):
            sucesso, user = verify_login(email_login, senha_login)
            if sucesso:
                st.session_state.logado = True
                st.session_state.aviso_inatividade = False
                
                if user.get("last_login"):
                    from datetime import datetime
                    try:
                        last_login_dt = datetime.strptime(user["last_login"], "%Y-%m-%d %H:%M:%S")
                        dias_ausente = (datetime.utcnow() - last_login_dt).days
                        if dias_ausente >= 3:
                            st.session_state.aviso_inatividade = dias_ausente
                    except Exception:
                        pass
                        
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
                import unicodedata
                import re
                nfkd_form = unicodedata.normalize('NFKD', nome_cad)
                clean_name = u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()
                parts = re.findall(r'[a-z0-9]+', clean_name)
                if len(parts) >= 2:
                    username_formatado = f"{parts[0]}.{parts[-1]}"
                elif len(parts) == 1:
                    username_formatado = parts[0]
                else:
                    username_formatado = "usuario"
                    
                with st.spinner("💳 Processando pagamento na operadora..."):
                    time.sleep(2)
                    sucesso, msg = create_user(nome_cad, email_cad, senha_cad, telefone_cad, endereco_cad, username_formatado)
                if sucesso:
                    st.success(f"🎉 Pagamento Aprovado! Seu usuário de Acesso é: {username_formatado}")
                    time.sleep(1.5)
                    _, user = verify_login(email_cad, senha_cad)
                    st.session_state.logado = True
                    st.session_state.user_info = user
                    st.switch_page("pages/2_Chat_Agente.py")
                else:
                    st.error(msg)
                    
elif opcao_menu == "Quem Somos":
    st.title("📖 Quem Somos")
    st.markdown("""
    ### A Maior Inteligência Artificial Financeira do Brasil
    
    A **AG Finance** nasceu com a missão de democratizar o acesso ao conhecimento e à gestão financeira de alta performance. 
    Acreditamos que todos merecem um "Economista Chefe" super inteligente focado no crescimento de seu patrimônio, e é por isso que desenvolvemos essa plataforma.
    
    #### Nossos Pilares
    * **Segurança:** Seus dados são protegidos e simulados em um ambiente de alto controle.
    * **Inteligência:** Modelos generativos que analisam faturas e extratos nas entrelinhas.
    * **Simplicidade:** Adeus planilhas confusas. Olá ao chat dinâmico.
    
    _Junte-se à revolução financeira e crie sua conta hoje mesmo!_
    """)
    if st.button("Criar minha conta agorinha!"):
        # Pular pro login
        # Streamlit rerun isn't strictly necessary since button re-runs the script but it doesn't change sidebar state easily
        st.info("Para criar sua conta, selecione 'Login / Cadastro' no menu ao lado e aproveite.")

elif opcao_menu == "Contato":
    st.title("✉️ Fale Conosco")
    st.markdown("Precisando de ajuda, suporte técnico ou tem uma proposta de parceria? Deixe sua mensagem abaixo.")
    
    with st.form("contato_form"):
        nome_contato = st.text_input("Seu Nome")
        email_contato = st.text_input("Seu E-mail")
        assunto = st.selectbox("Assunto", ["Dúvida Geral", "Suporte Financeiro", "Bug no Sistema", "Parceria"])
        mensagem = st.text_area("Sua Mensagem")
        
        if st.form_submit_button("Enviar Mensagem"):
            if not nome_contato or not email_contato or not mensagem:
                st.warning("Por favor, preencha todos os campos corretamente.")
            else:
                st.success("Sua mensagem foi recebida com sucesso! Nossa equipe retornará em até 24 horas úteis.")
st.stop()
