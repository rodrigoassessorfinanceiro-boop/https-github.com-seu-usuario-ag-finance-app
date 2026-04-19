import streamlit as st
import os
import pandas as pd
import PyPDF2
import time
from agent import criar_agente, gerar_titulo_curto
from db import marcar_como_onboarded, add_message, get_session_messages, create_session, get_user_sessions, get_onboarding_profile, log_activity

if "logado" not in st.session_state or not st.session_state.logado:
    st.switch_page("app.py")

current_key = os.environ.get("GOOGLE_API_KEY")

with st.sidebar:
    st.header("⚙️ Configurações da Conta")
    if st.button("🚪 Sair com segurança", use_container_width=True):
        st.session_state.logado = False
        st.session_state.user_info = None
        st.session_state.current_session_id = None
        st.switch_page("app.py")
        
    if st.session_state.user_info.get("is_admin"):
        st.markdown("---")
        st.page_link("pages/1_Admin_Dashboard.py", label="🛡️ Painel Admin", icon="👑")

# Carregar sessões se logado e não inicializado
if "current_session_id" not in st.session_state:
    ss = get_user_sessions(st.session_state.user_info['id'])
    if ss:
        st.session_state.current_session_id = ss[0][0]
        st.session_state.mensagens = get_session_messages(ss[0][0])
    else:
        st.session_state.current_session_id = None
        st.session_state.mensagens = []

# --- ONBOARDING ---
if not st.session_state.user_info.get('onboarded', False):
    st.title("🎯 Setup Inicial de Finanças")
    st.markdown("<p style='text-align: center; font-style: italic; color: #6B7280; font-size: 0.9em; margin-bottom: 20px;'>Somos um assistente virtual que ajuda a resolver a sua vida financeira!</p>", unsafe_allow_html=True)
    st.markdown("Para personalizarmos sua experiência, conte-me um pouco sobre seu padrão de gastos ou suba sua primeira fatura.")
    
    with st.container():
        gastos_texto = st.text_area("Descreva seus gastos ou orçamento atual:", height=100, placeholder="Ex: Ganho 5000, pago 1500 de aluguel e 300 de luz...")
        st.markdown("**Ou se preferir, suba uma fatura/extrato abaixo:**")
        uploaded_onboard = st.file_uploader("Fatura Inicial (CSV, Excel ou PDF)", type=["csv", "xls", "xlsx", "pdf"], key="onb_file")
        
        if st.button("Enviar e Começar 🚀", type="primary", use_container_width=True):
            if not current_key:
                st.error("⚠️ Defina a variável GOOGLE_API_KEY no arquivo `.env` para o agente funcionar.")
            else:
                texto_final = "Aqui está meu panorama inicial financeiro:\n" + gastos_texto + "\n"
                
                if uploaded_onboard:
                    extensao = uploaded_onboard.name.split('.')[-1].lower()
                    conteudo_extraido = ""
                    try:
                        if extensao == 'csv':
                            conteudo_extraido = uploaded_onboard.getvalue().decode("utf-8")
                        elif extensao in ['xls', 'xlsx']:
                            df = pd.read_excel(uploaded_onboard)
                            conteudo_extraido = df.to_csv(index=False)
                        elif extensao == 'pdf':
                            pdf_reader = PyPDF2.PdfReader(uploaded_onboard)
                            for page in pdf_reader.pages:
                                text = page.extract_text()
                                if text:
                                    conteudo_extraido += text + "\n"
                        texto_final += f"E aqui está o conteúdo da minha fatura '{uploaded_onboard.name}':\n```\n{conteudo_extraido}\n```\n"
                    except Exception as e:
                        st.error(f"Erro ao ler arquivo: {e}")
                        st.stop()
                        
                texto_final += "\nAnalise esses dados e me dê as boas-vindas com um breve resumo do que você entendeu, perguntando o que podemos fazer a seguir!"
                
                with st.spinner("🧠 Estudando seu padrão financeiro..."):
                    try:
                        ag_temp = criar_agente(api_key=current_key, model_name="gemini-2.5-flash")
                        resposta = ag_temp.invoke({"input": texto_final, "history": []})
                        
                        texto_res = resposta.get("output", "Tudo certo! Como começamos?")
                        st.session_state.mensagens = [
                            {"role": "user", "content": texto_final},
                            {"role": "assistant", "content": texto_res}
                        ]
                        
                        sid = create_session(st.session_state.user_info['id'], "🏠 Meu Perfil Setup")
                        st.session_state.current_session_id = sid
                        add_message(sid, st.session_state.user_info['id'], "user", texto_final)
                        add_message(sid, st.session_state.user_info['id'], "assistant", texto_res)
                        
                        marcar_como_onboarded(st.session_state.user_info['id'])
                        st.session_state.user_info['onboarded'] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro com a IA: {e}")
    st.stop()


# --- APP PRINCIPAL ---
st.title("💰 AG Finance")
st.markdown("<p style='text-align: center; font-style: italic; color: #6B7280; font-size: 0.9em; margin-bottom: 20px;'>Somos um assistente virtual que ajuda a resolver a sua vida financeira!</p>", unsafe_allow_html=True)
st.markdown(f"Bem-vindo novamente, **{st.session_state.user_info['name']}**! Como posso ajudar suas finanças hoje?")

with st.sidebar:
    st.markdown("---")
    api_key = st.text_input("Google Gemini API Key (Opcional):", type="password")
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        current_key = api_key
        
    modelo_escolhido = st.selectbox(
        "Escolha qual inteligência usar:",
        ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-pro"]
    )
        
    st.markdown("---")
    st.markdown("### 📂 Seus Históricos")
    
    if st.button("➕ Nova Consulta", use_container_width=True, type="primary"):
        st.session_state.current_session_id = None
        st.session_state.mensagens = []
        st.rerun()
        
    for sess in get_user_sessions(st.session_state.user_info['id']):
        s_id, s_title = sess[0], sess[1]
        btn_type = "primary" if s_id == st.session_state.get('current_session_id') else "secondary"
        if st.button(f"📄 {s_title}", key=f"sbtn_{s_id}", use_container_width=True, type=btn_type):
            st.session_state.current_session_id = s_id
            st.session_state.mensagens = get_session_messages(s_id)
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Análise de Extratos")
    uploaded_file = st.file_uploader("Suba sua fatura/extrato", type=["csv", "xls", "xlsx", "pdf"])

if not current_key:
    st.warning("⚠️ Insira sua **API Key do Google Gemini** no menu lateral ou no arquivo `.env` para conversar.")
    st.stop()

try:
    if "agente" not in st.session_state or st.session_state.get("modelo_atual") != modelo_escolhido:
        st.session_state.agente = criar_agente(api_key=current_key, model_name=modelo_escolhido)
        st.session_state.modelo_atual = modelo_escolhido
except Exception as e:
    st.error(f"Erro ao inicializar o agente: {e}")
    st.stop()

# PROCESSAR ARQUIVO NOVO DO SIDEBAR
if uploaded_file is not None and getattr(st.session_state, "ultimo_arquivo", None) != uploaded_file.name:
    st.session_state.ultimo_arquivo = uploaded_file.name
    
    conteudo_extraido = ""
    extensao = uploaded_file.name.split('.')[-1].lower()
    
    with st.spinner("Lendo e extraindo dados do arquivo..."):
        try:
            if extensao == 'csv':
                conteudo_extraido = uploaded_file.getvalue().decode("utf-8")
            elif extensao in ['xls', 'xlsx']:
                df = pd.read_excel(uploaded_file)
                conteudo_extraido = df.to_csv(index=False)
            elif extensao == 'pdf':
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        conteudo_extraido += text + "\n"
                        
            mensagem_invisivel = f"Aqui está o meu extrato financeiro:\n\n```\n{conteudo_extraido}\n```\n\nAnalise meus gastos, organize por categorias e mostre totais se possível."
            
            if st.session_state.current_session_id is None:
                sid = create_session(st.session_state.user_info['id'], "📊 Leitura de Fatura")
                st.session_state.current_session_id = sid

            st.session_state.mensagens.append({"role": "user", "content": mensagem_invisivel})
            add_message(st.session_state.current_session_id, st.session_state.user_info['id'], "user", mensagem_invisivel)
            
            resposta = st.session_state.agente.invoke({"input": mensagem_invisivel})
            texto_resposta = resposta.get("output", "Desculpe, deu erro na leitura.")
            st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
            add_message(st.session_state.current_session_id, st.session_state.user_info['id'], "assistant", texto_resposta)
            log_activity(st.session_state.user_info['id'], "Leitura de Fatura PDF/Planilha")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# EXIBIR MENSAGENS
for msg in st.session_state.mensagens:
    texto_chat = msg["content"]
    if isinstance(texto_chat, list):
        texto_chat = texto_chat[0].get("text", str(texto_chat))
    else:
        texto_chat = str(texto_chat)
        
    if texto_chat.startswith("Aqui está o meu extrato financeiro"):
        texto_chat = "📁 *(Arquivo de extrato lido pela IA)*"
        
    with st.chat_message(msg["role"]):
        st.markdown(texto_chat)

user_input = st.chat_input("Pergunte algo ou faça simulações de investimento!")

if user_input:
    if st.session_state.get("current_session_id") is None:
        tit = gerar_titulo_curto(user_input, api_key=current_key)
        sid = create_session(st.session_state.user_info['id'], tit)
        st.session_state.current_session_id = sid

    st.session_state.mensagens.append({"role": "user", "content": user_input})
    add_message(st.session_state.current_session_id, st.session_state.user_info['id'], "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analisando as informações financeiras..."):
            try:
                historico_ai = st.session_state.mensagens[:-1]
                
                # Global Biological Memory Injection
                biomem = get_onboarding_profile(st.session_state.user_info['id'])
                if biomem and not any("MEMÓRIA GLOBAL DO USUÁRIO" in m['content'] for m in historico_ai):
                    historico_ai.insert(0, {"role": "user", "content": biomem})
                    historico_ai.insert(1, {"role": "assistant", "content": "Memória Ativa: Entendido! Carreguei todo o seu histórico de faturas e gastos iniciais da nossa conversa mestra."})
                    
                resposta = st.session_state.agente.invoke({
                    "input": user_input,
                    "history": historico_ai
                })
                texto_resposta = resposta.get("output", "Desculpe, não consegui processar isso.")
                st.markdown(texto_resposta)
                st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                add_message(st.session_state.current_session_id, st.session_state.user_info['id'], "assistant", texto_resposta)
                log_activity(st.session_state.user_info['id'], "Chat LLM Agente")
            except Exception as e:
                st.error(f"Ocorreu um erro durante a resposta: {e}")
