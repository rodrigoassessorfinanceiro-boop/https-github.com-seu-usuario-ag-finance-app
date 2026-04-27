import streamlit as st
import time
import re
import unicodedata
from dotenv import load_dotenv
from db import init_db, create_user, verify_login, update_onboarding_data

load_dotenv(override=True)
init_db()

st.set_page_config(page_title="AG Finanças", layout="wide", initial_sidebar_state="collapsed")

# ─────────────────────────────────────────────
# CSS (preservado do seu arquivo)
# ─────────────────────────────────────────────
CSS = """
<style>
html, body, [data-testid="stAppViewContainer"] { background: #021B38 !important; }
[data-testid="stAppViewContainer"] > .main { background: linear-gradient(135deg, #021B38 0%, #05366D 100%) !important; }
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { background: #01142A !important; border-right: 1px solid rgba(223,161,79,0.12) !important; }
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 { color: #FFFFFF !important; letter-spacing: -0.3px; }
p, li, label, span { color: #C9D1E3 !important; }
.gold { color: #DFA14F !important; font-weight: 600; }
.muted { color: #8FA4C8 !important; }
.big-title { font-size: clamp(28px, 4vw, 44px); font-weight: 800; color: #FFFFFF !important; line-height: 1.15; letter-spacing: -0.5px; }
.big-title .accent { color: #DFA14F; }
.subtitle { font-size: 16px; color: #8FA4C8 !important; line-height: 1.6; margin-top: 8px; }
.badge-free { display: inline-flex; align-items: center; gap: 6px; background: rgba(223,161,79,0.10); border: 1px solid rgba(223,161,79,0.30); color: #DFA14F !important; font-size: 12px; font-weight: 600; padding: 5px 14px; border-radius: 20px; margin-bottom: 18px; letter-spacing: 0.3px; }
.badge-free::before { content: ""; width: 6px; height: 6px; background: #DFA14F; border-radius: 50%; }
.card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 20px 22px; margin-bottom: 12px; transition: border-color 0.2s; }
.card:hover { border-color: rgba(223,161,79,0.18); }
.card-gold { background: rgba(223,161,79,0.06); border: 1px solid rgba(223,161,79,0.20); border-radius: 14px; padding: 20px 22px; margin-bottom: 12px; }
.card-week { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-left: 3px solid #DFA14F; border-radius: 0 12px 12px 0; padding: 14px 18px; margin-bottom: 10px; }
.card-week .week-tag { font-size: 11px; color: #DFA14F !important; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.card-week .week-title { font-size: 15px; font-weight: 600; color: #FFFFFF !important; margin-bottom: 3px; }
.card-week .week-desc { font-size: 13px; color: #8FA4C8 !important; line-height: 1.5; }
.score-wrap { display: flex; align-items: center; gap: 20px; padding: 20px 0; }
.score-number { font-size: 64px; font-weight: 800; line-height: 1; color: #DFA14F !important; }
.score-number.low  { color: #F44336 !important; }
.score-number.mid  { color: #FF9800 !important; }
.score-number.high { color: #4CAF50 !important; }
.score-label { font-size: 13px; color: #8FA4C8 !important; margin-bottom: 6px; }
.score-objetivo { display: inline-block; background: rgba(223,161,79,0.10); border: 1px solid rgba(223,161,79,0.25); color: #DFA14F !important; font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 20px; }
.alert-item { display: flex; align-items: center; gap: 12px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 11px 15px; margin-bottom: 8px; font-size: 13px; color: #C9D1E3 !important; }
.alert-item.red   { border-left: 3px solid #F44336; border-radius: 0 10px 10px 0; }
.alert-item.amber { border-left: 3px solid #FF9800; border-radius: 0 10px 10px 0; }
.eco-highlight { background: rgba(223,161,79,0.08); border: 1px solid rgba(223,161,79,0.22); border-radius: 14px; padding: 18px 22px; text-align: center; margin: 16px 0; }
.eco-highlight .eco-label { font-size: 13px; color: #8FA4C8 !important; margin-bottom: 4px; }
.eco-highlight .eco-value { font-size: 36px; font-weight: 800; color: #DFA14F !important; }
.stButton > button { background: linear-gradient(135deg, #DFA14F 0%, #C58C41 100%) !important; color: #021B38 !important; font-weight: 700 !important; font-size: 14px !important; border: none !important; border-radius: 10px !important; padding: 13px 28px !important; letter-spacing: 0.2px; transition: opacity 0.15s, transform 0.1s !important; }
.stButton > button:hover { opacity: 0.92 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) scale(0.98) !important; }
.btn-secondary > button { background: transparent !important; color: #DFA14F !important; border: 1px solid rgba(223,161,79,0.35) !important; }
.btn-secondary > button:hover { background: rgba(223,161,79,0.08) !important; opacity: 1 !important; }
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div > div, [data-testid="stTextArea"] textarea { background: #FFFFFF !important; border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 10px !important; color: #000000 !important; font-size: 14px !important; padding: 10px 14px !important; transition: border-color 0.2s !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: rgba(223,161,79,0.5) !important; box-shadow: 0 0 0 3px rgba(223,161,79,0.08) !important; }
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label, [data-testid="stSelectbox"] label { color: #C9D1E3 !important; font-size: 13px !important; font-weight: 500 !important; margin-bottom: 5px !important; }
[data-testid="stRadio"] label { color: #C9D1E3 !important; font-size: 14px !important; }
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; font-weight: 500 !important; margin-bottom: 6px !important; }
[data-testid="stTabs"] [role="tab"] { color: #8FA4C8 !important; font-size: 13px !important; font-weight: 500 !important; border-bottom: 2px solid transparent !important; padding: 8px 18px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #DFA14F !important; border-bottom-color: #DFA14F !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid rgba(255,255,255,0.08) !important; }
[data-testid="stProgress"] > div > div { background: rgba(255,255,255,0.08) !important; border-radius: 4px !important; height: 4px !important; }
[data-testid="stProgress"] > div > div > div { background: linear-gradient(90deg, #DFA14F, #C58C41) !important; border-radius: 4px !important; }
[data-testid="stAlert"] { border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.08) !important; background: rgba(255,255,255,0.03) !important; }
hr { border-color: rgba(255,255,255,0.08) !important; margin: 20px 0 !important; }
[data-testid="stSpinner"] { color: #DFA14F !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# COMPONENTES HTML
# ─────────────────────────────────────────────
def badge_free(texto="Grátis para começar"):
    return f'<div class="badge-free">{texto}</div>'

def big_title(linha1, accent=""):
    partes = linha1.replace(accent, f'<span class="accent">{accent}</span>') if accent else linha1
    return f'<div class="big-title">{partes}</div>'

def score_display(score, objetivo=""):
    cls = "high" if score >= 70 else ("mid" if score >= 50 else "low")
    obj_html = f'<div class="score-objetivo">🎯 {objetivo}</div>' if objetivo else ""
    return f"""<div class="score-wrap">
        <div class="score-number {cls}">{score}</div>
        <div><div class="score-label">Saúde financeira · /100</div>{obj_html}</div>
    </div>"""

def alert_item(texto, nivel="amber"):
    return f'<div class="alert-item {nivel}">{texto}</div>'

def eco_card(valor, label="Potencial de economia identificado"):
    return f"""<div class="eco-highlight">
        <div class="eco-label">{label}</div>
        <div class="eco-value">R$ {valor:,.0f}<span style="font-size:18px;font-weight:500">/mês</span></div>
    </div>"""

def card_semana(semana, titulo, descricao):
    return f"""<div class="card-week">
        <div class="week-tag">{semana}</div>
        <div class="week-title">{titulo}</div>
        <div class="week-desc">{descricao}</div>
    </div>"""

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {"logado": False, "user_info": None, "etapa": "landing", "respostas": {}}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.logado and st.session_state.user_info:
    st.switch_page("pages/2_Chat_Agente.py")

# ─────────────────────────────────────────────
# DIAGNÓSTICO — cálculo real
# ─────────────────────────────────────────────
MAPA_RENDA = {"Até 2k": 2000, "2k-5k": 3500, "5k-10k": 7500, "10k+": 15000}

def calcular_diagnostico(respostas: dict) -> dict:
    renda = MAPA_RENDA.get(respostas.get("renda", "2k-5k"), 3500)
    score = 100
    alertas = []

    if respostas.get("sobra") == "Não":
        score -= 20
        alertas.append(("red", "Você não consegue guardar dinheiro no fim do mês"))
    if respostas.get("divida") == "Sim":
        score -= 20
        alertas.append(("red", "Dívidas ativas consomem parte da sua renda"))
    if respostas.get("reserva") == "Não":
        score -= 15
        alertas.append(("amber", "Sem reserva de emergência — qualquer imprevisto vira dívida"))
    if respostas.get("investimento") == "Não":
        score -= 10
        alertas.append(("amber", "Dinheiro parado perde valor para a inflação"))

    score = max(score, 25)
    fator = 0.08 + (0.17 * (1 - score / 100))
    economia = round(renda * fator / 50) * 50

    if respostas.get("divida") == "Sim":
        objetivo = "Sair das Dívidas"
    elif respostas.get("sobra") == "Não":
        objetivo = "Equilibrar o Orçamento"
    elif respostas.get("investimento") == "Não":
        objetivo = "Começar a Investir"
    else:
        objetivo = "Acelerar o Patrimônio"

    return {
        "score": score,
        "alertas": alertas,
        "economia": economia,
        "renda": renda,
        "gasto_estimado": renda * 0.80 if respostas.get("sobra") == "Não" else renda * 0.60,
        "objetivo": objetivo,
    }

# ─────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────
def _username_from_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    clean = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()
    parts = re.findall(r"[a-z0-9]+", clean)
    return f"{parts[0]}.{parts[-1]}" if len(parts) >= 2 else (parts[0] if parts else "usuario")

def _fazer_cadastro(nome, email, senha, key=""):
    """Cadastra, loga e redireciona. Retorna False em caso de erro."""
    if not nome or not email or not senha:
        st.warning("Preencha todos os campos.")
        return False
    if len(senha) < 6:
        st.warning("A senha deve ter pelo menos 6 caracteres.")
        return False
    with st.spinner("Criando sua conta..."):
        time.sleep(0.5)
        sucesso, msg = create_user(nome, email, senha, "", "", _username_from_name(nome))
    if not sucesso:
        st.error(msg)
        return False
    ok, user = verify_login(email, senha)
    if ok:
        dados = st.session_state.get("_diagnostico") or calcular_diagnostico(st.session_state.respostas)
        update_onboarding_data(user["id"], dados["renda"], dados["gasto_estimado"], dados["objetivo"])
        user.update({
            "onboarded": True,
            "renda_mensal": dados["renda"],
            "gastos_fixos": dados["gasto_estimado"],
            "objetivo_fin": dados["objetivo"],
        })
        if st.session_state.respostas:
            user["dados_funil"] = st.session_state.respostas
        st.session_state.logado = True
        st.session_state.user_info = user
        for key in ["current_session_id", "mensagens"]:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("pages/2_Chat_Agente.py")
    return True

def _form_login(suffix: str = ""):
    email = st.text_input("E-mail ou usuário", key=f"login_email_{suffix}")
    senha = st.text_input("Senha", type="password", key=f"login_senha_{suffix}")
    if st.button("Entrar →", use_container_width=True, key=f"login_btn_{suffix}"):
        ok, user = verify_login(email, senha)
        if ok:
            if st.session_state.respostas:
                user["dados_funil"] = st.session_state.respostas
            st.session_state.logado = True
            st.session_state.user_info = user
            for key in ["current_session_id", "mensagens"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("pages/2_Chat_Agente.py")
        else:
            st.error("E-mail ou senha incorretos.")

# ─────────────────────────────────────────────
# TELA 1 — LANDING
# ─────────────────────────────────────────────
def landing():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(badge_free("Planejamento financeiro com IA"), unsafe_allow_html=True)
        st.markdown(big_title("Seu dinheiro some antes do fim do mês?"), unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Descubra em 2 minutos onde você está perdendo dinheiro e receba um plano personalizado.</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Fazer diagnóstico grátis", use_container_width=True):
                st.session_state.etapa = "onboarding"
                st.rerun()
        with col_btn2:
            if st.button("Já tenho conta", use_container_width=True, type="secondary"):
                st.session_state.etapa = "login"
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="muted" style="font-size:13px;line-height:2.2">✔ Rápido &nbsp;&nbsp; ✔ Sem planilha &nbsp;&nbsp; ✔ 100% confidencial</div>', unsafe_allow_html=True)
    with col2:
        st.image("https://images.unsplash.com/photo-1605902711622-cfb43c44367f", use_container_width=True)

# ─────────────────────────────────────────────
# TELA 2 — ONBOARDING (5 perguntas reais)
# ─────────────────────────────────────────────
def onboarding():
    st.markdown('<h2 class="gold">Diagnóstico financeiro</h2>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">4 perguntas rápidas — menos de 2 minutos.</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("form_onboarding"):
        renda = st.selectbox("Qual é sua renda familiar mensal?", ["Até 2k", "2k-5k", "5k-10k", "10k+"])
        sobra = st.radio("Sobra dinheiro no fim do mês?", ["Sim", "Não"], horizontal=True)
        divida = st.radio("Você tem dívidas ativas? (cartão, empréstimo, cheque especial)", ["Sim", "Não"], horizontal=True)
        reserva = st.radio("Você tem reserva de emergência? (3+ meses de gastos guardados)", ["Sim", "Não"], horizontal=True)
        investimento = st.radio("Você investe algum valor regularmente?", ["Sim", "Não"], horizontal=True)
        enviado = st.form_submit_button("Ver meu diagnóstico →", use_container_width=True)

    if enviado:
        st.session_state.respostas = {
            "renda": renda, "sobra": sobra, "divida": divida,
            "reserva": reserva, "investimento": investimento,
        }
        st.session_state.etapa = "diagnostico"
        st.rerun()

# ─────────────────────────────────────────────
# TELA 3 — DIAGNÓSTICO (helpers visuais ativos)
# ─────────────────────────────────────────────
def diagnostico():
    dados = calcular_diagnostico(st.session_state.respostas)
    st.session_state["_diagnostico"] = dados

    st.markdown('<h2 class="gold">Seu diagnóstico financeiro</h2>', unsafe_allow_html=True)

    # Score com cor por faixa + badge de objetivo
    st.markdown(score_display(dados["score"], dados["objetivo"]), unsafe_allow_html=True)

    # Alertas por gravidade (vermelho / âmbar)
    if dados["alertas"]:
        for nivel, texto in dados["alertas"]:
            st.markdown(alert_item(texto, nivel), unsafe_allow_html=True)
    else:
        st.markdown(alert_item("Sua situação está acima da média — hora de acelerar o patrimônio.", "amber"), unsafe_allow_html=True)

    # Economia potencial baseada na renda real
    st.markdown(eco_card(dados["economia"]), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Ver meu plano personalizado →", use_container_width=True):
        st.session_state.etapa = "plano"
        st.rerun()

# ─────────────────────────────────────────────
# TELA 4 — PLANO (card_semana + personalizado)
# ─────────────────────────────────────────────
def plano():
    dados = st.session_state.get("_diagnostico") or calcular_diagnostico(st.session_state.respostas)
    objetivo = dados.get("objetivo", "Organizar as finanças")
    economia = dados.get("economia", 300)
    respostas = st.session_state.respostas

    st.markdown('<h2 class="gold">Plano de 30 dias</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">Personalizado para: <strong style="color:#DFA14F">{objetivo}</strong></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if respostas.get("divida") == "Sim":
        semanas = [
            ("Semana 1", "Mapeie suas dívidas", "Liste todas: valor, juros e vencimento. Priorize as de maior taxa de juros."),
            ("Semana 2", "Corte o supérfluo", "Identifique os 3 maiores gastos evitáveis e redirecione para amortização."),
            ("Semana 3", "Negocie e quite", "Entre em contato com credores — a maioria aceita desconto para pagamento à vista."),
            ("Semana 4", "Monte sua reserva", "Com a dívida controlada, guarde R$ 50/dia numa conta separada."),
        ]
    elif respostas.get("sobra") == "Não":
        semanas = [
            ("Semana 1", "Mapeie os gastos", "Anote tudo que gasta por 7 dias — sem julgamento, só observação."),
            ("Semana 2", "Identifique os vazamentos", "Encontre os 3 gastos que mais pesam e que você poderia reduzir agora."),
            ("Semana 3", "Aplique o 50/30/20", "50% necessidades, 30% desejos, 20% investimento e reserva."),
            ("Semana 4", "Automatize a poupança", "Configure débito automático para separar o valor antes de gastar."),
        ]
    elif respostas.get("investimento") == "Não":
        semanas = [
            ("Semana 1", "Monte a reserva de emergência", "6 meses de gastos no Tesouro Selic ou CDB com liquidez diária."),
            ("Semana 2", "Conheça seu perfil", "Faça o teste de suitability para descobrir qual tipo de investimento combina com você."),
            ("Semana 3", "Primeiro investimento", "Comece com R$ 30 no Tesouro Direto — o importante é criar o hábito."),
            ("Semana 4", "Automatize o aporte", "Configure transferência automática todo dia de pagamento."),
        ]
    else:
        semanas = [
            ("Semana 1", "Audite os investimentos", "Levante o que tem e onde está. Calcule o rendimento real de cada ativo."),
            ("Semana 2", "Diversifique a carteira", "Distribua entre renda fixa, fundos e renda variável conforme seu perfil."),
            ("Semana 3", "Aumente o aporte", "Defina uma meta de aporte mensal crescente: +10% a cada trimestre."),
            ("Semana 4", "Revise e projete", "Simule seu patrimônio daqui 10 e 20 anos com os novos aportes."),
        ]

    for sem, titulo, desc in semanas:
        st.markdown(card_semana(sem, titulo, desc), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card-gold" style="text-align:center;padding:22px">
        <div style="color:#8FA4C8;font-size:13px;margin-bottom:6px">Com acompanhamento personalizado você pode economizar</div>
        <div style="color:#DFA14F;font-size:34px;font-weight:800">R$ {economia:,.0f}<span style="font-size:20px;font-weight:500">/mês</span></div>
        <div style="color:#8FA4C8;font-size:12px;margin-top:4px">calculado com base no seu perfil financeiro</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Experimentar grátis →", use_container_width=True):
            st.session_state.etapa = "cadastro_free"
            st.rerun()
    with col2:
        if st.button("Plano completo — R$ 19/mês", use_container_width=True, type="secondary"):
            st.session_state.etapa = "paywall"
            st.rerun()

# ─────────────────────────────────────────────
# TELA 5 — CADASTRO FREEMIUM
# ─────────────────────────────────────────────
FREE_LIMIT = 5

def cadastro_free():
    st.markdown('<h2 class="gold">Criar sua conta gratuita</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">As primeiras <strong style="color:#DFA14F">{FREE_LIMIT} conversas</strong> com sua assistente financeira são por nossa conta.</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    tab_cad, tab_login = st.tabs(["✨ Criar conta", "🔒 Já tenho conta"])

    with tab_cad:
        nome = st.text_input("Nome completo", key="free_nome")
        email = st.text_input("E-mail", key="free_email")
        senha = st.text_input("Senha (mín. 6 caracteres)", type="password", key="free_senha")
        if st.button("Criar conta e começar →", use_container_width=True, key="free_btn"):
            _fazer_cadastro(nome, email, senha, "free")

    with tab_login:
        _form_login("free")

# ─────────────────────────────────────────────
# TELA 6 — PAYWALL
# ─────────────────────────────────────────────
def paywall():
    st.markdown('<h2 class="gold">Acesso completo</h2>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    for col, (feat, desc) in zip([col1, col2, col3], [
        ("✔ Conversas ilimitadas", "Sem limite de mensagens"),
        ("✔ Memória financeira", "Lembra seus dados e histórico"),
        ("✔ Simulações avançadas", "Investimentos, metas, aposentadoria"),
    ]):
        with col:
            st.markdown(f'<div class="card" style="text-align:center"><div style="color:#DFA14F;font-size:15px;font-weight:600">{feat}</div><div style="color:#8FA4C8;font-size:13px;margin-top:4px">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;padding:28px 0 8px"><div style="color:#8FA4C8;font-size:14px">Acesso completo por apenas</div><div style="color:#fff;font-size:52px;font-weight:800;line-height:1.1">R$ 19<span style="font-size:22px;font-weight:500">/mês</span></div><div style="color:#8FA4C8;font-size:13px;margin-top:4px">Cancele quando quiser</div></div>', unsafe_allow_html=True)

    tab_cad, tab_login = st.tabs(["💳 Assinar agora", "🔒 Já tenho conta"])

    with tab_cad:
        nome = st.text_input("Nome completo", key="pay_nome")
        email = st.text_input("E-mail", key="pay_email")
        senha = st.text_input("Senha", type="password", key="pay_senha")
        if st.button("Assinar por R$ 19/mês", use_container_width=True, key="pay_btn"):
            _fazer_cadastro(nome, email, senha, "pay")

    with tab_login:
        _form_login("pay")

# ─────────────────────────────────────────────
# TELA 7 — LOGIN DIRETO
# ─────────────────────────────────────────────
def login():
    st.markdown('<h2 class="gold">Acessar sua conta</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _form_login("direct")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Voltar", type="secondary"):
        st.session_state.etapa = "landing"
        st.rerun()

# ─────────────────────────────────────────────
# ROTEADOR
# ─────────────────────────────────────────────
ROTAS = {
    "landing":       landing,
    "onboarding":    onboarding,
    "diagnostico":   diagnostico,
    "plano":         plano,
    "cadastro_free": cadastro_free,
    "paywall":       paywall,
    "login":         login,
}

ROTAS.get(st.session_state.etapa, landing)()
