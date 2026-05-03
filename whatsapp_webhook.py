import os
import logging
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Importar lógicas do nosso app
from db import DB_FILE, get_onboarding_profile, add_message, get_session_messages
from agent import criar_agente
import sqlite3

load_dotenv(override=True)

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Configurações do Meta WhatsApp API
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "agfinance_secreto")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

def get_user_by_phone(phone: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tenta buscar pelo número exato ou com/sem o '+'
    cursor.execute("SELECT id, name, renda_mensal, gastos_fixos, objetivo_fin FROM users WHERE phone LIKE ?", (f"%{phone}%",))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "id": user[0],
            "name": user[1],
            "renda_mensal": user[2],
            "gastos_fixos": user[3],
            "objetivo_fin": user[4]
        }
    return None

def send_whatsapp_message(to_phone: str, text: str):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("Faltam credenciais do WhatsApp no .env")
        return

    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code != 200:
        print(f"Erro ao enviar mensagem: {resp.text}")

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Endpoint para validação do Webhook no painel da Meta."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Token inválido", 403
    return "Hello WhatsApp Bot", 200

@app.route("/webhook", methods=["POST"])
def webhook_events():
    """Recebe mensagens do WhatsApp."""
    data = request.json
    
    if data.get("object"):
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for msg in value["messages"]:
                        sender_phone = msg.get("from") # Número de quem enviou
                        msg_type = msg.get("type")
                        
                        if msg_type == "text":
                            text_body = msg.get("text", {}).get("body", "")
                            
                            print(f"Mensagem recebida de {sender_phone}: {text_body}")
                            
                            # 1. Identificar Usuário
                            user_info = get_user_by_phone(sender_phone)
                            if not user_info:
                                send_whatsapp_message(
                                    sender_phone, 
                                    "Olá! Não encontrei seu número cadastrado na AG Finance. Por favor, acesse o painel web, faça login e cadastre seu número de celular (com DDD) no seu perfil!"
                                )
                                continue
                                
                            # 2. Buscar ou Criar Sessão do WhatsApp
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute("SELECT id FROM chat_sessions WHERE user_id = ? AND title = 'WhatsApp' ORDER BY id DESC LIMIT 1", (user_info["id"],))
                            sess = cursor.fetchone()
                            if sess:
                                session_id = sess[0]
                            else:
                                cursor.execute("INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)", (user_info["id"], "WhatsApp"))
                                session_id = cursor.lastrowid
                                conn.commit()
                            conn.close()
                            
                            # 3. Salvar mensagem do usuário
                            add_message(session_id, user_info["id"], "user", text_body)
                            
                            # 4. Invocando o Agente IA
                            historico = get_session_messages(session_id)
                            # Pega as ultimas 6 mensagens para manter o contexto sem estourar limites no WhatsApp
                            historico_recente = historico[-6:] if len(historico) > 6 else historico
                            
                            try:
                                agente = criar_agente(model_name="gemini-2.5-flash")
                                resposta = agente.invoke({
                                    "input": text_body,
                                    "history": historico_recente,
                                    "user_info": user_info,
                                    "global_memory": get_onboarding_profile(user_info['id'])
                                })
                                texto_resposta = resposta.get("output", "Desculpe, tive um problema ao processar.")
                            except Exception as e:
                                print(f"Erro IA: {e}")
                                texto_resposta = "Ocorreu um erro no servidor ao gerar a resposta."

                            # 5. Salvar resposta da IA e enviar
                            add_message(session_id, user_info["id"], "assistant", texto_resposta)
                            send_whatsapp_message(sender_phone, texto_resposta)

        return jsonify({"status": "ok"}), 200

    return jsonify({"status": "error"}), 404

if __name__ == "__main__":
    print("Iniciando Webhook do WhatsApp na porta 5000...")
    app.run(host="0.0.0.0", port=5000)
