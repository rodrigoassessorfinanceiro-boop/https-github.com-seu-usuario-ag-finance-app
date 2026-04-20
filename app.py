import streamlit as st
import time
from dotenv import load_dotenv
from db import init_db, create_user, verify_login, update_onboarding_data

load_dotenv(override=True)
init_db()

st.set_page_config(page_title="AG Finanças", layout="wide", initial_sidebar_state="collapsed")

# -------------------------
# CSS CUSTOM (ESTILO SAFRA PREMIUM)
# -------------------------
CSS = """
<style>
/* ── BASE ─────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: #0B1F3A !important;
}
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(160deg, #0B1F3A 0%, #0F2847 50%, #132F5C 100%) !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}
section[data-testid="stSidebar"] {
    background: #081629 !important;
    border-right: 1px solid rgba(212,175,55,0.12) !important;
}

/* ── TIPOGRAFIA ───────────────────────────── */
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #FFFFFF !important;
    letter-spacing: -0.3px;
}
p, li, label, span {
    color: #C9D1E3 !important;
}

/* ── CLASSES UTILITÁRIAS ──────────────────── */
.gold { color: #D4AF37 !important; font-weight: 600; }
.muted { color: #8FA4C8 !important; }

.big-title {
    font-size: clamp(28px, 4vw, 44px);
    font-weight: 800;
    color: #FFFFFF !important;
    line-height: 1.15;
    letter-spacing: -0.5px;
}
.big-title .accent { color: #D4AF37; }

.subtitle {
    font-size: 16px;
    color: #8FA4C8 !important;
    line-height: 1.6;
    margin-top: 8px;
}

/* ── BADGE ────────────────────────────────── */
.badge-free {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(212,175,55,0.10);
    border: 1px solid rgba(212,175,55,0.30);
    color: #D4AF37 !important;
    font-size: 12px;
    font-weight: 600;
    padding: 5px 14px;
    border-radius: 20px;
    margin-bottom: 18px;
    letter-spacing: 0.3px;
}
.badge-free::before {
    content: "";
    width: 6px; height: 6px;
    background: #D4AF37;
    border-radius: 50%;
}

/* ── CARDS ────────────────────────────────── */
.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.card:hover {
    border-color: rgba(212,175,55,0.18);
}
.card-gold {
    background: rgba(212,175,55,0.06);
    border: 1px solid rgba(212,175,55,0.20);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 12px;
}
.card-week {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 3px solid #D4AF37;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.card-week .week-tag {
    font-size: 11px;
    color: #D4AF37 !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.card-week .week-title {
    font-size: 15px;
    font-weight: 600;
    color: #FFFFFF !important;
    margin-bottom: 3px;
}
.card-week .week-desc {
    font-size: 13px;
    color: #8FA4C8 !important;
    line-height: 1.5;
}

/* ── SCORE ────────────────────────────────── */
.score-wrap {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 20px 0;
}
.score-number {
    font-size: 64px;
    font-weight: 800;
    line-height: 1;
    color: #D4AF37 !important;
}
.score-number.low  { color: #F44336 !important; }
.score-number.mid  { color: #FF9800 !important; }
.score-number.high { color: #4CAF50 !important; }
.score-label {
    font-size: 13px;
    color: #8FA4C8 !important;
    margin-bottom: 6px;
}
.score-objetivo {
    display: inline-block;
    background: rgba(212,175,55,0.10);
    border: 1px solid rgba(212,175,55,0.25);
    color: #D4AF37 !important;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
}

/* ── ALERT ITEMS ──────────────────────────── */
.alert-item {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 11px 15px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #C9D1E3 !important;
}
.alert-item.red   { border-left: 3px solid #F44336; border-radius: 0 10px 10px 0; }
.alert-item.amber { border-left: 3px solid #FF9800; border-radius: 0 10px 10px 0; }

/* ── ECO CARD ─────────────────────────────── */
.eco-highlight {
    background: rgba(212,175,55,0.08);
    border: 1px solid rgba(212,175,55,0.22);
    border-radius: 14px;
    padding: 18px 22px;
    text-align: center;
    margin: 16px 0;
}
.eco-highlight .eco-label {
    font-size: 13px;
    color: #8FA4C8 !important;
    margin-bottom: 4px;
}
.eco-highlight .eco-value {
    font-size: 36px;
    font-weight: 800;
    color: #D4AF37 !important;
}

/* ── BOTÕES ───────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #D4AF37 0%, #B8922A 100%) !important;
    color: #0B1F3A !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 13px 28px !important;
    letter-spacing: 0.2px;
    transition: opacity 0.15s, transform 0.1s !important;
}
.stButton > button:hover {
    opacity: 0.92 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}
.btn-secondary > button {
    background: transparent !important;
    color: #D4AF37 !important;
    border: 1px solid rgba(212,175,55,0.35) !important;
}
.btn-secondary > button:hover {
    background: rgba(212,175,55,0.08) !important;
    opacity: 1 !important;
}

/* ── INPUTS ───────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(212,175,55,0.5) !important;
    box-shadow: 0 0 0 3px rgba(212,175,55,0.08) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label {
    color: #C9D1E3 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    margin-bottom: 5px !important;
}

/* ── RADIO / FORM ─────────────────────────── */
[data-testid="stRadio"] label {
    color: #C9D1E3 !important;
    font-size: 14px !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    color: #FFFFFF !important;
    font-weight: 500 !important;
    margin-bottom: 6px !important;
}

/* ── TABS ─────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    color: #8FA4C8 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-bottom: 2px solid transparent !important;
    padding: 8px 18px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #D4AF37 !important;
    border-bottom-color: #D4AF37 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── PROGRESS BAR ─────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 4px !important;
    height: 4px !important;
}
[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, #D4AF37, #B8922A) !important;
    border-radius: 4px !important;
}

/* ── MENSAGENS (success / error / info) ───── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: rgba(255,255,255,0.03) !important;
}

/* ── DIVIDER ──────────────────────────────── */
hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 20px 0 !important;
}

/* ── SPINNER ──────────────────────────────── */
[data-testid="stSpinner"] {
    color: #D4AF37 !important;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ── COMPONENTES HTML ──────────────────────────
def badge_free(texto="Grátis para começar"):
    return f'<div class="badge-free">{texto}</div>'

def big_title(linha1, accent=""):
    partes = linha1.replace(accent, f'<span class="accent">{accent}</span>') if accent else linha1
    return f'<div class="big-title">{partes}</div>'

def score_display(score, objetivo=""):
    cls = "high" if score >= 70 else ("mid" if score >= 50 else "low")
    obj_html = f'<div class="score-objetivo">{objetivo}</div>' if objetivo else ""
    return f"""
    <div class="score-wrap">
        <div class="score-number {cls}">{score}</div>
        <div>
            <div class="score-label">Saúde financeira · /100</div>
            {obj_html}
        </div>
    </div>
    """

def alert_item(texto, nivel="amber"):
    return f'<div class="alert-item {nivel}">{texto}</div>'

def eco_card(valor, label="Potencial de economia identificado"):
    return f"""
    <div class="eco-highlight">
        <div class="eco-label">{label}</div>
        <div class="eco-value">R$ {valor:,.0f}<span style="font-size:18px;font-weight:500">/mês</span></div>
    </div>
    """

def card_semana(semana, titulo, descricao):
    return f"""
    <div class="card-week">
        <div class="week-tag">{semana}</div>
        <div class="week-title">{titulo}</div>
        <div class="week-desc">{descricao}</div>
    </div>
    """

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
