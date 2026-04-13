import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from langchain.tools import tool
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

@tool
def calculadora_juros_compostos(aporte_mensal: float, taxa_juros_anual: float, anos: int) -> str:
    """
    Calcula o montante final de um investimento com aportes mensais e juros compostos.
    O valor 'taxa_juros_anual' deve estar em porcentagem (ex: 10 para 10%).
    """
    taxa_mensal = (1 + (taxa_juros_anual / 100)) ** (1/12) - 1
    meses = anos * 12
    montante = 0.0

    for _ in range(meses):
        montante += aporte_mensal
        montante *= (1 + taxa_mensal)
        
    return f"O montante estimado após {anos} anos investindo R$ {aporte_mensal:.2f} mensais a {taxa_juros_anual:.2f}% a.a. é de aproximadamente R$ {montante:.2f}."

@tool
def buscar_cotacao_moeda(moeda: str) -> str:
    """
    Busca a cotação atual de uma moeda em relação ao Real (BRL) na internet (ao vivo).
    O parâmetro 'moeda' deve ser uma destas: 'USD' (Dólar), 'EUR' (Euro), ou 'BTC' (Bitcoin).
    """
    try:
        m = moeda.upper()
        if m not in ['USD', 'EUR', 'BTC']:
            return "Moeda não suportada pela interface. Tente USD, EUR ou BTC."
        
        resp = requests.get(f"https://economia.awesomeapi.com.br/json/last/{m}-BRL")
        if resp.status_code == 200:
            dados = resp.json()
            chave = f"{m}BRL"
            if chave in dados:
                valor = float(dados[chave]['bid'])
                return f"A cotação atual em tempo real do {m} frente ao BRL é de R$ {valor:.2f}."
        return "Falha nas pontes de Câmbio."
    except Exception as e:
        return f"Erro de conexão cambial: {e}"

@tool
def buscar_taxa_selic() -> str:
    """
    Busca os indicativos oficiais na API do BCB (Banco Central do Brasil) sobre a atual Taxa Selic Meta Anual consolidada.
    """
    try:
        resp = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json")
        if resp.status_code == 200:
            dados = resp.json()
            if len(dados) > 0 and 'valor' in dados[0]:
                return f"A Taxa Selic Meta atual ditada pelo Banco Central do Brasil é de {dados[0]['valor']}% ao ano (Atualizada pontualmente em {dados[0]['data']})."
        return "Falha nos servidores do Banco Central."
    except Exception as e:
        return f"Erro de conexão com BCB: {e}"

class AgenteFinanceiro:
    def __init__(self, api_key=None, model_name="gemini-2.5-flash"):
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Google API Key não fornecida.")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=key,
            temperature=0.2
        ).bind_tools([calculadora_juros_compostos, buscar_cotacao_moeda, buscar_taxa_selic])
        
    def invoke(self, inputs):
        user_input = inputs.get("input", "")
        history = inputs.get("history", [])
        
        system_prompt = (
            "Você é a AG Finance, uma Economista Chefe e Assistente Pessoal superinteligente.\n"
            "REGRAS DIRETAS (Siga à risca): "
            "1. Você entende de TUDO sobre finanças pessoais: cálculos, inflação (IPCA), taxas de juros (Selic), economia geral e orçamentos. "
            "2. MEMÓRIA ATIVA: O usuário pode digitar gastos pontuais. Lembre-se disso com base no histórico que lhe foi passado. Some os valores quando ele pedir o saldo ou o orçamento mensal. "
            "3. Quando o usuário pedir qualquer simulação matemática exata envolvendo anos/meses e taxas compostas, SEMPRE utilize a calculadora_juros_compostos (tool). "
            "4. Se receber blocos grandes como extratos ou faturas, leia as entrelinhas e atue como analista separando os gastos por categorias (em tabelas markdown limpas). "
            "5. Seja prestativa, elegante, responda em Português limpo utilizando formatação Markdown (negritos, listas e tabelas)."
        )

        messages = [("system", system_prompt)]
        
        for msg in history:
            role = "human" if msg["role"] == "user" else "ai"
            messages.append((role, msg["content"]))
            
        messages.append(("human", user_input))
        
        response = self.llm.invoke(messages)
        messages.append(response)
        
        mapa_ferramentas = {
            'calculadora_juros_compostos': calculadora_juros_compostos,
            'buscar_cotacao_moeda': buscar_cotacao_moeda,
            'buscar_taxa_selic': buscar_taxa_selic
        }

        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                nome_ferramenta = tool_call['name']
                if nome_ferramenta in mapa_ferramentas:
                    output = mapa_ferramentas[nome_ferramenta].invoke(tool_call['args'])
                    messages.append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
            
            response = self.llm.invoke(messages)
            
        texto_final = response.content
        if isinstance(texto_final, list):
            # Limpar qualquer lista de dicts (ex: [{'type': 'text', 'text': 'ola'}]) para string unica
            blocos_texto = []
            for item in texto_final:
                if isinstance(item, dict) and "text" in item:
                    blocos_texto.append(item["text"])
                else:
                    blocos_texto.append(str(item))
            texto_final = "\n".join(blocos_texto)
        else:
            texto_final = str(texto_final)
            
        return {"output": texto_final}

def criar_agente(api_key=None, model_name="gemini-2.5-flash"):
    return AgenteFinanceiro(api_key, model_name)

def gerar_titulo_curto(mensagem: str, api_key: str = None) -> str:
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return "Nova Consulta"
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=key, temperature=0.5)
        resp = llm.invoke([("system", "Você é um gerador de títulos. Resuma a mensagem em 3 palavras. Retorne apenas o título (sem aspas e sem pontuação fina ou hashtags)."), ("human", mensagem)])
        t = resp.content.strip()
        return t[:30] # Limit safety
    except:
        return "Consulta Finanças"
