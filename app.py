import streamlit as st
import time
from dotenv import load_dotenv
from db import init_db, create_user, verify_login, update_onboarding_data

load_dotenv(override=True)
init_db()

st.set_page_config(page_title="AG Finanças", layout="wide", initial_sidebar_state="collapsed")

# -------------------------
# CSS CUSTOM (ESTILO SAFRA)
# -------------------------
st.markdown("""
<style>
body {
    background-color: #0B1F3A;
}

.main {
    background: linear-gradient(180deg, #0B1F3A 0%, #132F5C 100%);
    color: white;
}

h1, h2, h3 {
    color: #FFFFFF !important;
}

.gold {
    color: #D4AF37 !important;
    font-weight: 600;
}

.big-title {
    font-size: 48px;
    font-weight: 700;
    color: #FFFFFF;
}

.subtitle {
    font-size: 20px;
    color: #C9D1E3;
}

.stButton>button {
    background: linear-gradient(90deg, #D4AF37, #C9A227);
    color: #0B1F3A;
    font-weight: bold;
    border-radius: 10px;
    padding: 12px 24px;
    border: none;
}

.card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
}
</style>
""", unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

if st.session_state.logado:
    st.switch_page("pages/2_Chat_Agente.py")

# -------------------------
# ESTADO
# -------------------------
if "etapa" not in st.session_state:
    st.session_state.etapa = "landing"
if "respostas" not in st.session_state:
    st.session_state.respostas = {}

# -------------------------
# FUNÇÕES DE CÁLCULO
# -------------------------
def calcular_diagnostico(respostas):
    score = 60
    if respostas.get("sobra") == "Não":
        score -= 15
    if respostas.get("divida") == "Sim":
        score -= 15
    economia = score * 10
    return score, economia

# -------------------------
# TELAS
# -------------------------
def landing():
    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown('<div class="big-title">Seu dinheiro some antes do fim do mês?</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Descubra em 2 minutos onde você está perdendo dinheiro</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Fazer diagnóstico gratuito"):
            st.session_state.etapa = "onboarding"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("✔ Rápido  \n✔ Sem planilha  \n✔ 100% confidencial")

    with col2:
        st.image("https://images.unsplash.com/photo-1605902711622-cfb43c44367f")

def onboarding():
    st.markdown('<h2 class="gold">Diagnóstico financeiro</h2>', unsafe_allow_html=True)

    renda = st.selectbox("Renda familiar", ["Até 2k", "2k-5k", "5k-10k", "10k+"])
    sobra = st.radio("Sobra dinheiro?", ["Sim", "Não"])
    divida = st.radio("Tem dívidas?", ["Sim", "Não"])

    if st.button("Ver diagnóstico"):
        st.session_state.respostas = {
            "renda": renda,
            "sobra": sobra,
            "divida": divida
        }
        st.session_state.etapa = "diagnostico"
        st.rerun()

def diagnostico():
    score, economia = calcular_diagnostico(st.session_state.respostas)

    st.markdown('<h2 class="gold">Seu diagnóstico</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-title">{score}/100</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("⚠ Falta de controle financeiro")
    st.write("⚠ Gastos elevados")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"💰 Você pode economizar R$ {economia}/mês")

    if st.button("Quero melhorar"):
        st.session_state.etapa = "plano"
        st.rerun()

def plano():
    st.markdown('<h2 class="gold">Plano de 30 dias</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Semana 1 → Anotar gastos")
    st.write("Semana 2 → Cortar despesas")
    st.write("Semana 3 → Ajustar alimentação")
    st.write("Semana 4 → Guardar dinheiro")
    st.markdown('</div>', unsafe_allow_html=True)

    st.progress(0)

    if st.button("Quero acompanhamento"):
        st.session_state.etapa = "paywall"
        st.rerun()

def paywall():
    st.markdown('<h2 class="gold">Continue evoluindo</h2>', unsafe_allow_html=True)
    st.write("✔ Acompanhamento semanal")
    st.write("✔ Alertas automáticos")
    st.write("✔ Plano personalizado")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="big-title">R$ 19/mês</div>', unsafe_allow_html=True)

    tab_cadastro, tab_login = st.tabs(["💳 Criar Conta de Acesso", "🔒 Já tenho conta"])
    
    with tab_cadastro:
        nome_cad = st.text_input("Nome Completo")
        email_cad = st.text_input("Seu E-mail")
        senha_cad = st.text_input("Senha Forte", type="password", key="cad_pass")
        
        if st.button("Assinar agora", key="btn_assinar_cad"):
            if not nome_cad or not email_cad or not senha_cad:
                st.warning("Preencha todos os campos corretamente.")
            else:
                import unicodedata, re
                nfkd_form = unicodedata.normalize('NFKD', nome_cad)
                clean_name = u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()
                parts = re.findall(r'[a-z0-9]+', clean_name)
                username_formatado = f"{parts[0]}.{parts[-1]}" if len(parts) >= 2 else (parts[0] if parts else "usuario")
                    
                with st.spinner("Provisionando seu acesso..."):
                    time.sleep(1)
                    sucesso, msg = create_user(nome_cad, email_cad, senha_cad, "", "", username_formatado)
                
                if sucesso:
                    sucesso_log, user = verify_login(email_cad, senha_cad)
                    if sucesso_log:
                        mapa_renda = {"Até 2k": 2000.0, "2k-5k": 4000.0, "5k-10k": 8000.0, "10k+": 15000.0}
                        renda_num = mapa_renda.get(st.session_state.respostas.get("renda", "5k-10k"), 5000.0)
                        gasto_aprox = renda_num * 0.7 if st.session_state.respostas.get("sobra") == "Não" else (renda_num * 0.5)
                        obj = "Sair das Dívidas" if st.session_state.respostas.get("divida") == "Sim" else "Começar a Investir"
                        
                        update_onboarding_data(user['id'], renda_num, gasto_aprox, obj)
                        user['onboarded'] = True
                        user['renda_mensal'] = renda_num
                        user['gastos_fixos'] = gasto_aprox
                        user['objetivo_fin'] = obj
                        user['dados_funil'] = st.session_state.respostas 
                        
                        st.session_state.logado = True
                        st.session_state.user_info = user
                        st.switch_page("pages/2_Chat_Agente.py")
                else:
                    st.error(msg)
                    
    with tab_login:
        email_login = st.text_input("E-mail ou Usuário", key="login_field")
        senha_login = st.text_input("Senha", type="password", key="login_pass_tab")
        if st.button("Acessar Conta", key="login_btn"):
            sucesso, user = verify_login(email_login, senha_login)
            if sucesso:
                st.session_state.logado = True
                if st.session_state.respostas:
                   user['dados_funil'] = st.session_state.respostas
                st.session_state.user_info = user
                st.switch_page("pages/2_Chat_Agente.py")
            else:
                st.error("Credenciais inválidas.")

# -------------------------
# FLUXO
# -------------------------
if st.session_state.etapa == "landing":
    landing()
elif st.session_state.etapa == "onboarding":
    onboarding()
elif st.session_state.etapa == "diagnostico":
    diagnostico()
elif st.session_state.etapa == "plano":
    plano()
elif st.session_state.etapa == "paywall":
    paywall()
