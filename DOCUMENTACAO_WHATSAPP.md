# Guia de Integração Oficial do WhatsApp (Meta Cloud API) para o AG Finance

Este guia acompanha o arquivo `whatsapp_webhook.py` gerado na raiz do projeto, que permite conectar o Agente de Finanças (IA) e o banco de dados diretamente ao WhatsApp.

## Entendendo a Arquitetura

O Streamlit (usado para o frontend web) não é ideal para rodar "Webhooks" (pontos de recebimento contínuo de mensagens de terceiros). Por isso, a integração foi construída usando o framework **Flask**. 

1. O usuário manda uma mensagem via WhatsApp.
2. A Meta (Facebook) faz uma chamada `POST` para o seu Webhook Flask.
3. O script busca o telefone do usuário no banco `db.py`.
4. Envia o histórico e os dados (renda, gastos, saldo) para a Inteligência Artificial (`agent.py`).
5. A IA processa, e o Flask responde de volta para a Meta, que entrega a mensagem final ao usuário.

## Passo a Passo para Colocar no Ar

### 1. Configurar o Meta for Developers (Gratuito)
1. Acesse o [Meta for Developers](https://developers.facebook.com/) e faça login.
2. Crie um novo aplicativo do tipo **"Empresa"** e adicione o produto **"WhatsApp"**.
3. A Meta vai te fornecer três informações cruciais (guarde-as):
   - **Token de Acesso** (Temporário para testes ou Permanente se configurar conta comercial).
   - **Identificador do Número de Telefone (Phone Number ID)**.

### 2. Configurar o Hospedeiro do Webhook
Você precisará de um lugar para deixar o `whatsapp_webhook.py` rodando 24 horas por dia. Como o Streamlit Cloud foca em interface gráfica, use plataformas focadas em APIs e Back-ends Python, como:
- [Render.com](https://render.com) (Gratuito)
- [Railway.app](https://railway.app)
- Heroku

No Render, por exemplo, você cria um novo "Web Service", vincula este mesmo repositório do GitHub e define o comando de inicialização (Start Command) como:
`gunicorn whatsapp_webhook:app`

### 3. Configurar as Variáveis de Ambiente (.env)
No seu servidor de hospedagem (onde o Webhook estiver rodando), configure as seguintes chaves de ambiente:
```env
# Suas chaves atuais de IA (mantenha)
GOOGLE_API_KEY="sua_chave_gemini"

# Novas chaves para WhatsApp
WHATSAPP_TOKEN="seu_token_de_acesso_da_meta"
WHATSAPP_PHONE_NUMBER_ID="seu_identificador_de_telefone"
WHATSAPP_VERIFY_TOKEN="agfinance_secreto_123" # Você inventa essa senha
```

### 4. Configurar a URL de Webhook na Meta
1. Volte ao painel do Meta for Developers.
2. No menu lateral do WhatsApp, clique em **Configuração**.
3. Em "Webhook", clique em **Editar**.
4. URL de retorno (Callback URL): Coloque o endereço do seu servidor acompanhado de `/webhook`. Ex: `https://meu-agfinance-api.onrender.com/webhook`
5. Token de verificação (Verify Token): Coloque exatamente a mesma senha que você definiu no passo anterior (`agfinance_secreto_123`).
6. Clique em **Verificar e Salvar**.
7. Após salvar, clique em "Gerenciar" e marque a caixinha `messages` para receber avisos sempre que alguém enviar uma mensagem.

### 5. Cadastrar Telefones
Lembre-se: Para a IA responder e reconhecer o usuário, o número do telefone de quem enviou a mensagem (com DDD) deve constar no campo de telefone da conta dele na plataforma web do AG Finance.

---
*Documentação gerada pelo Assistente Inteligente para garantir que os passos fiquem armazenados com segurança.*
