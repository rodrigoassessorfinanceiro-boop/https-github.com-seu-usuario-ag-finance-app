import streamlit as st
import os
import pandas as pd
import PyPDF2
import time
from agent import criar_agente, gerar_titulo_curto
from db import marcar_como_onboarded, update_onboarding_data, add_message, get_session_messages, create_session, get_user_sessions, get_onboarding_profile, log_activity

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
        st.markdown("Preencha 3 dados rápidos para a inteligência configurar o seu painel:")
        val_renda = st.number_input("1. Qual é a sua Renda Mensal (Líquida)? R$", min_value=0.0, step=100.0, format="%.2f")
        val_gastos = st.number_input("2. Qual o valor base dos seus Gastos Fixos mensais? R$", min_value=0.0, step=100.0, format="%.2f")
        val_obj = st.selectbox("3. Qual o seu principal Objetivo Financeiro?", ["Quitar Dívidas", "Criar Reserva de Emergência", "Investir e Multiplicar Patrimônio", "Comprar Imóvel / Veículo", "Outro"])
        
        st.markdown("**Opcional:** Suba sua fatura/extrato atual:")
        uploaded_onboard = st.file_uploader("Fatura (CSV, Excel ou PDF)", type=["csv", "xls", "xlsx", "pdf"], key="onb_file")
        
        if st.button("Enviar e Começar 🚀", type="primary", use_container_width=True):
            if not current_key:
                st.error("⚠️ Defina a variável GOOGLE_API_KEY no arquivo `.env` para o agente funcionar.")
            else:
                if val_renda <= 0:
                    st.warning("⚠️ Insira uma renda maior que zero para continuarmos.")
                    st.stop()
                    
                texto_final = f"Aqui está meu panorama inicial financeiro estruturado:\n- Renda Mensal Líquida: R$ {val_renda:.2f}\n- Gastos Fixos Atuais: R$ {val_gastos:.2f}\n- Objetivo Principal: {val_obj}\n\n"
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
                        
                        update_onboarding_data(st.session_state.user_info['id'], val_renda, val_gastos, val_obj)
                        st.session_state.user_info['onboarded'] = True
                        st.session_state.user_info['renda_mensal'] = val_renda
                        st.session_state.user_info['gastos_fixos'] = val_gastos
                        st.session_state.user_info['objetivo_fin'] = val_obj
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ocorreu um erro com a IA: {e}")
    st.stop()


# --- APP PRINCIPAL ---
st.title("💰 AG Finance")
st.markdown("<p style='text-align: center; font-style: italic; color: #6B7280; font-size: 0.9em; margin-bottom: 20px;'>Somos um assistente virtual que ajuda a resolver a sua vida financeira!</p>", unsafe_allow_html=True)
st.markdown(f"Bem-vindo novamente, **{st.session_state.user_info['name']}**! Como posso ajudar suas finanças hoje?")

if st.session_state.get("aviso_inatividade"):
    dias = st.session_state.aviso_inatividade
    st.toast(f"👋 Que bom ter você de volta! Fazia {dias} dias que não nos víamos.", icon="🎉")
    st.info(f"**Notificamos sua ausência!** Percebemos que você ficou {dias} dias sem acessar a plataforma. O seu Inteligência Artificial sentiu sua falta, vamos colocar as finanças em dia!")
    st.balloons()
    st.session_state.aviso_inatividade = False

renda = st.session_state.user_info.get('renda_mensal', 0.0)
gastos = st.session_state.user_info.get('gastos_fixos', 0.0)
obj = st.session_state.user_info.get('objetivo_fin', 'Nenhum')

if renda > 0:
    st.markdown("### 📊 Seu Painel Financeiro")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Renda", f"R$ {renda:,.2f}")
    c2.metric("Gastos", f"R$ {gastos:,.2f}")
    
    pct = (gastos / renda) * 100
    if pct > 60:
        c3.metric("Renda Comprometida", f"🔴 {pct:.1f}%")
    else:
        c3.metric("Renda Comprometida", f"🟢 {pct:.1f}%")
        
    score_val = 0
    if pct <= 50:
        score_val = 800 + ((50 - pct) / 50.0) * 200
    elif pct <= 100:
        score_val = 800 - ((pct - 50) / 50.0) * 800
    else:
        score_val = 0
    score_val = max(0, min(1000, int(score_val)))
    
    if score_val >= 800:
        cat_score = "🌟 Excelente"
    elif score_val >= 500:
        cat_score = "👍 Bom"
    elif score_val >= 300:
        cat_score = "⚠️ Atenção"
    else:
        cat_score = "🚨 Crítico"
        
    c4.metric("Score Financeiro", f"{score_val}", cat_score, delta_color="off")
    st.markdown("---")

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
    
    st.markdown("---")
    st.markdown("### 📄 Relatórios Avançados")
    btn_pdf = st.button("📥 Receber Plano Financeiro (PDF)", use_container_width=True, type="primary")

if btn_pdf:
    if not current_key:
        st.sidebar.error("Precisa de API Key para gerar o PDF!")
    else:
        with st.spinner("🧠 Gerando plano de ação financeiro personalizado..."):
            try:
                ag_temp = criar_agente(api_key=current_key, model_name="gemini-2.5-flash")
                prompt_pdf = f"Gere um Plano Financeiro resumido em puro texto simples (sem markdown pesado e estritamente SEM EMOJIS). O usuário ganha {renda}, gasta fixo {gastos} e o objetivo é {obj}. Divida em 3 tópicos: 1. Diagnóstico, 2. Plano de Ação em Passos, 3. Dica Final."
                resposta_pdf = ag_temp.invoke({"input": prompt_pdf, "history": []}).get("output", "")
                
                # Substituir qualquer emoji que ele ainda insista em gerar (cleanup basico)
                texto_limpo = resposta_pdf.encode('latin-1', 'replace').decode('latin-1')
                
                from fpdf import FPDF
                class PDF(FPDF):
                    def header(self):
                        self.set_font('Helvetica', 'B', 15)
                        self.cell(0, 10, 'AG Finance - Plano Financeiro de Acao', border=False, align='C')
                        self.ln(20)
                
                pdf = PDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Helvetica", size=12)
                pdf.multi_cell(0, 10, texto_limpo)
                
                pdf_bytes = pdf.output()
                st.sidebar.success("PDF Gerado sob medida!")
                st.sidebar.download_button(label="Baixar Plano.pdf", data=pdf_bytes, file_name="Seu_Plano_Financeiro_AG.pdf", mime="application/pdf", type="primary")
            except Exception as e:
                st.sidebar.error(f"Erro ao gerar PDF (instale a lib fpdf2 no servidor): {e}")

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

st.markdown("💡 **Apostas Seguras (Clique para perguntar):**")
c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)
btn_clicado = None
if c_b1.button("📉 Cortar Gastos", use_container_width=True, help="Como reduzir meus gastos atuais?"):
    btn_clicado = "Listar 3 dicas práticas para reduzir meus gastos atuais com base no meu objetivo financeiro."
if c_b2.button("🏆 Meu Objetivo", use_container_width=True, help="Como atingir meu objetivo principal?"):
    btn_clicado = f"Como posso atingir meu objetivo '{obj}' de forma mais rápida?"
if c_b3.button("🚨 Ver Faturas", use_container_width=True, help="Avalie minhas faturas inseridas e dê dicas."):
    btn_clicado = "Analise profundamente minhas faturas e extratos armazenados na memória e aponte os maiores drenos de dinheiro."
if c_b4.button("📈 Investir Sobra", use_container_width=True, help="Onde devo aplicar meu dinheiro?"):
    btn_clicado = "Diga as 2 melhores formas de aplicar R$300 reais por mês com segurança."
if c_b5.button("💼 Regra Ideal", use_container_width=True, help="Regra Orçamentária"):
    btn_clicado = "O que é a regra 50-30-20 e como eu a aplicaria aos meus ganhos atuais?"

st.markdown("💬 **Opções de Envio Adicionais:**")
c_chat_opt1, c_chat_opt2 = st.columns(2)
with c_chat_opt1:
    file_input_chat = st.file_uploader("Anexar Fatura", type=["csv", "xls", "xlsx", "pdf"], label_visibility="collapsed")
with c_chat_opt2:
    audio_input = st.audio_input("Ou grave sua dúvida", label_visibility="collapsed")

user_input = st.chat_input("Pergunte algo ou faça simulações de investimento!")

texto_audio = None
if audio_input is not None:
    tamanho_audio = len(audio_input.getvalue())
    if st.session_state.get('ultimo_audio_size') != tamanho_audio:
        st.session_state.ultimo_audio_size = tamanho_audio
        with st.spinner("🎙️ Transcrevendo áudio..."):
            try:
                import google.generativeai as genai
                genai.configure(api_key=current_key)
                audio_data = audio_input.getvalue()
                
                modelo_transc = genai.GenerativeModel("gemini-1.5-flash")
                resp_transc = modelo_transc.generate_content([
                    "Responda apenas com a transcrição em texto claro e direto do áudio fornecido em português-br. Se inaudível, responda 'inação'.",
                    {"mime_type": "audio/wav", "data": audio_data}
                ])
                if resp_transc.text and "inação" not in resp_transc.text.lower():
                    texto_audio = resp_transc.text.strip()
                    st.success(f"🗣️ Escutei: {texto_audio}")
            except Exception as e:
                st.error(f"Erro no áudio: {e}")

texto_arquivo = None
if file_input_chat is not None:
    tamanho_arquivo = len(file_input_chat.getvalue())
    if st.session_state.get('ultimo_arquivo_chat_size') != tamanho_arquivo:
        st.session_state.ultimo_arquivo_chat_size = tamanho_arquivo
        with st.spinner("📄 Extraindo dados do arquivo..."):
            conteudo_extraido = ""
            extensao = file_input_chat.name.split('.')[-1].lower()
            try:
                if extensao == 'csv':
                    conteudo_extraido = file_input_chat.getvalue().decode("utf-8")
                elif extensao in ['xls', 'xlsx']:
                    df = pd.read_excel(file_input_chat)
                    conteudo_extraido = df.to_csv(index=False)
                elif extensao == 'pdf':
                    pdf_reader = PyPDF2.PdfReader(file_input_chat)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            conteudo_extraido += text + "\n"
                if conteudo_extraido:
                    texto_arquivo = f"Aqui está o meu extrato anexado '{file_input_chat.name}':\n\n```\n{conteudo_extraido}\n```\n\nAnalise esses dados e dê sugestões financeiras se houver espaço."
                    st.success(f"📎 Anexo lido: {file_input_chat.name}")
            except Exception as e:
                st.error(f"Erro no arquivo: {e}")

entrada_final = user_input or btn_clicado or texto_audio or texto_arquivo

if entrada_final:
    if st.session_state.get("current_session_id") is None:
        tit = gerar_titulo_curto(entrada_final, api_key=current_key)
        sid = create_session(st.session_state.user_info['id'], tit)
        st.session_state.current_session_id = sid

    st.session_state.mensagens.append({"role": "user", "content": entrada_final})
    add_message(st.session_state.current_session_id, st.session_state.user_info['id'], "user", entrada_final)
    with st.chat_message("user"):
        st.markdown(entrada_final)

    with st.chat_message("assistant"):
        with st.spinner("Analisando as informações financeiras..."):
            try:
                historico_ai = st.session_state.mensagens[:-1]
                
                # Global Biological Memory Injection
                biomem = get_onboarding_profile(st.session_state.user_info['id'])
                if biomem and not any("MEMÓRIA GLOBAL DO USUÁRIO" in m['content'] for m in historico_ai):
                    extra_funil = ""
                    if st.session_state.user_info.get("dados_funil"):
                        df = st.session_state.user_info["dados_funil"]
                        extra_funil = f"\n[DADOS DO DIAGNÓSTICO] Pessoas lar: {df.get('pessoas')}, Sobra Mês: {df.get('sobra')}, Dívidas: {df.get('divida')}, Foco: {df.get('gasto')}."
                    
                    historico_ai.insert(0, {"role": "user", "content": biomem + f"\n[METADADOS ATUAIS] Ganho: {renda}, Gasto: {gastos}, Objetivo: {obj}" + extra_funil})
                    historico_ai.insert(1, {"role": "assistant", "content": "Memória Ativa: Entendido! Carreguei todo o seu histórico de faturas e gastos iniciais."})
                    
                resposta = st.session_state.agente.invoke({
                    "input": entrada_final,
                    "history": historico_ai
                })
                texto_resposta = resposta.get("output", "Desculpe, não consegui processar isso.")
                st.markdown(texto_resposta)
                st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                add_message(st.session_state.current_session_id, st.session_state.user_info['id'], "assistant", texto_resposta)
                log_activity(st.session_state.user_info['id'], "Chat LLM Agente")
            except Exception as e:
                st.error(f"Ocorreu um erro durante a resposta: {e}")
