import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from langchain.tools import tool
from dotenv import load_dotenv
import requests

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# FERRAMENTAS
# ─────────────────────────────────────────────

@tool
def calculadora_juros_compostos(aporte_mensal: float, taxa_juros_anual: float, anos: int = 0, meses: int = 0, detalhar_tabela: bool = False) -> str:
    """
    Calcula o montante final de um investimento com aportes mensais e juros compostos.
    Use quando o usuário perguntar sobre simulações de investimento, aposentadoria ou crescimento de patrimônio.
    O parâmetro taxa_juros_anual deve ser em % (ex: 10 para 10% a.a.).
    Forneça o período em 'anos', 'meses' ou ambos.
    Se o usuário solicitar evolução "mês a mês", passe detalhar_tabela=True.
    """
    if aporte_mensal <= 0 or taxa_juros_anual <= 0 or (anos <= 0 and meses <= 0):
        return "Valores inválidos: aporte, taxa e tempo (anos/meses) devem ser maiores que zero."
    
    taxa_mensal = (1 + taxa_juros_anual / 100) ** (1 / 12) - 1
    meses_totais = (anos * 12) + meses
    
    montante = 0.0
    tabela_texto = ""
    
    if detalhar_tabela:
        tabela_texto += "\n\n**Evolução Mês a Mês detalhada:**\n| Mês | Aporte Acumulado | Juros do Mês | Montante Acumulado |\n|---|---|---|---|\n"
        
    for i in range(1, meses_totais + 1):
        montante = (montante + aporte_mensal) * (1 + taxa_mensal)
        if detalhar_tabela and i <= 240:  # Limite lógico de 20 anos na tabela
            juros_acumulado = montante - (aporte_mensal * i)
            tabela_texto += f"| {i} | R$ {aporte_mensal*i:,.2f} | R$ {juros_acumulado:,.2f} | R$ {montante:,.2f} |\n"

    total_investido = aporte_mensal * meses_totais
    rendimento = montante - total_investido
    
    resumo = (
        f"📊 **Simulação de {meses_totais} meses**\n"
        f"- Aporte mensal: R$ {aporte_mensal:,.2f}\n"
        f"- Taxa: {taxa_juros_anual:.2f}% a.a. ({taxa_mensal*100:.3f}% a.m.)\n"
        f"- Total investido: R$ {total_investido:,.2f}\n"
        f"- Rendimento (Juros): R$ {rendimento:,.2f}\n"
        f"- **Montante final: R$ {montante:,.2f}**"
    )
    
    if detalhar_tabela:
        if meses_totais > 240:
             tabela_texto += "\n*(A tabela foi limitada aos primeiros 240 meses para não estourar a tela)*\n"
        resumo += tabela_texto
        
    return resumo

@tool
def buscar_cotacao_moeda(moeda: str) -> str:
    """
    Busca a cotação atual de qualquer moeda em relação ao Real (BRL).
    Use o código ISO 4217 da moeda (ex: USD, EUR, GBP, JPY, ARS, BTC, ETH).
    """
    try:
        m = moeda.upper().strip()
        resp = requests.get(
            f"https://economia.awesomeapi.com.br/json/last/{m}-BRL",
            timeout=5
        )
        if resp.status_code == 200:
            dados = resp.json()
            chave = f"{m}BRL"
            if chave in dados:
                d = dados[chave]
                valor = float(d['bid'])
                variacao = float(d.get('pctChange', 0))
                sinal = "🔺" if variacao >= 0 else "🔻"
                return (
                    f"💱 **{m}/BRL** → R$ {valor:,.4f}\n"
                    f"{sinal} Variação hoje: {variacao:+.2f}%"
                )
        return f"Moeda '{m}' não encontrada. Verifique o código ISO (ex: USD, EUR, GBP)."
    except requests.Timeout:
        return "Serviço de câmbio indisponível no momento. Tente novamente."
    except Exception as e:
        logger.error(f"Erro cotação {moeda}: {e}")
        return f"Erro ao buscar cotação: {e}"

@tool
def buscar_taxa_selic() -> str:
    """
    Busca a Taxa Selic Meta atual no Banco Central do Brasil.
    Use quando o usuário perguntar sobre a taxa básica de juros, rendimento de
    renda fixa atrelada ao CDI/Selic, ou comparações com investimentos.
    """
    try:
        resp = requests.get(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
            timeout=5
        )
        if resp.status_code == 200:
            dados = resp.json()
            if dados and 'valor' in dados[0]:
                taxa = float(dados[0]['valor'])
                data = dados[0]['data']
                taxa_mensal = (1 + taxa / 100) ** (1 / 12) - 1
                return (
                    f"🏦 **Taxa Selic Meta** (BCB)\n"
                    f"- Anual: **{taxa:.2f}% a.a.**\n"
                    f"- Equivalente mensal: {taxa_mensal*100:.3f}% a.m.\n"
                    f"- Atualizada em: {data}"
                )
        return "Falha ao acessar o Banco Central. Tente novamente."
    except requests.Timeout:
        return "API do Banco Central indisponível. Tente novamente."
    except Exception as e:
        logger.error(f"Erro Selic: {e}")
        return f"Erro: {e}"

@tool
def calcular_orcamento_50_30_20(renda_mensal: float) -> str:
    """
    Aplica a regra de orçamento 50/30/20 para uma renda mensal.
    Use quando o usuário perguntar como distribuir o salário, montar um orçamento
    ou controlar gastos mensais.
    """
    if renda_mensal <= 0:
        return "Renda deve ser positiva."
    necessidades = renda_mensal * 0.50
    desejos = renda_mensal * 0.30
    investimento = renda_mensal * 0.20
    return (
        f"📋 **Regra 50/30/20 para R$ {renda_mensal:,.2f}**\n\n"
        f"| Categoria | % | Valor |\n"
        f"|---|---|---|\n"
        f"| 🏠 Necessidades (moradia, alimentação, transporte) | 50% | R$ {necessidades:,.2f} |\n"
        f"| 🎯 Desejos (lazer, roupas, restaurantes) | 30% | R$ {desejos:,.2f} |\n"
        f"| 💰 Investimentos e reserva de emergência | 20% | R$ {investimento:,.2f} |"
    )

@tool
def calcular_reserva_emergencia(gasto_mensal: float, meses: int = 6) -> str:
    """
    Calcula o valor ideal de reserva de emergência.
    Use quando o usuário perguntar sobre segurança financeira, quanto guardar
    para emergências ou por onde começar a investir.
    O parâmetro meses representa quantos meses de cobertura (padrão: 6).
    """
    if gasto_mensal <= 0:
        return "Gasto mensal deve ser positivo."
    meses = max(3, min(meses, 12))
    total = gasto_mensal * meses
    return (
        f"🛡️ **Reserva de Emergência**\n"
        f"- Gastos mensais: R$ {gasto_mensal:,.2f}\n"
        f"- Cobertura: {meses} meses\n"
        f"- **Meta: R$ {total:,.2f}**\n\n"
        f"📌 Onde guardar: Tesouro Selic, CDB com liquidez diária ou conta remunerada."
    )

TOOLS = [
    calculadora_juros_compostos,
    buscar_cotacao_moeda,
    buscar_taxa_selic,
    calcular_orcamento_50_30_20,
    calcular_reserva_emergencia,
]

TOOL_MAP = {t.name: t for t in TOOLS}

# ─────────────────────────────────────────────
# AGENTE
# ─────────────────────────────────────────────

class AgenteFinanceiro:
    MAX_ITERATIONS = 5  # proteção contra loop infinito

    def __init__(self, api_key=None, model_name="gemini-2.5-flash"):
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Google API Key não fornecida.")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=key,
            temperature=0.2,
        ).bind_tools(TOOLS)

    def _build_system_prompt(self, user_info: dict | None) -> str:
        base = (
            "Você é a **AG Finance**, uma assistente financeira pessoal inteligente e elegante.\n\n"
            "## Suas capacidades\n"
            "- Planejamento financeiro pessoal e orçamento\n"
            "- Simulações de investimento com juros compostos\n"
            "- Cotações de moedas em tempo real\n"
            "- Taxa Selic e renda fixa\n"
            "- Análise de extratos e faturas (tabelas markdown por categoria)\n"
            "- Regras de orçamento (50/30/20, reserva de emergência)\n\n"
            "## Regras\n"
            "1. Responda sempre em Português claro, usando Markdown (negrito, listas, tabelas).\n"
            "2. Para cálculos exatos com taxas e prazos, USE as ferramentas disponíveis.\n"
            "3. Seja EXTREMAMENTE conciso e vá direto ao ponto. Suas respostas devem ser curtas e objetivas.\n"
            "4. Quando receber um extrato ou fatura, categorize os gastos em tabela markdown.\n"
            "5. Nunca invente valores — use as ferramentas para dados em tempo real.\n"
            "6. NUNCA se alongue em explicações não solicitadas. Seja breve e sucinto.\n"
        )

        if user_info:
            renda = user_info.get("renda_mensal", 0)
            gastos = user_info.get("gastos_fixos", 0)
            objetivo = user_info.get("objetivo_fin", "")
            nome = user_info.get("name", "").split()[0]

            perfil = f"\n## Perfil do usuário — {nome}\n"
            if renda > 0:
                perfil += f"- Renda mensal: R$ {renda:,.2f}\n"
                if gastos > 0:
                    sobra = renda - gastos
                    perfil += f"- Gastos fixos estimados: R$ {gastos:,.2f} (sobra ~R$ {sobra:,.2f}/mês)\n"
            if objetivo:
                perfil += f"- Objetivo financeiro: {objetivo}\n"
            perfil += "\nPersonalize suas respostas com base neste perfil quando relevante.\n"
            base += perfil

        return base

    def invoke(self, inputs: dict) -> dict:
        user_input = inputs.get("input", "")
        history = inputs.get("history", [])
        user_info = inputs.get("user_info", None)

        messages = [("system", self._build_system_prompt(user_info))]
        for msg in history:
            role = "human" if msg["role"] == "user" else "ai"
            messages.append((role, msg["content"]))
        messages.append(("human", user_input))

        for iteration in range(self.MAX_ITERATIONS):
            response = self.llm.invoke(messages)
            messages.append(response)

            if not (hasattr(response, "tool_calls") and response.tool_calls):
                break  # sem mais ferramentas, resposta final

            for tool_call in response.tool_calls:
                nome = tool_call["name"]
                if nome in TOOL_MAP:
                    try:
                        output = TOOL_MAP[nome].invoke(tool_call["args"])
                    except Exception as e:
                        output = f"Erro ao executar {nome}: {e}"
                    messages.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
                else:
                    messages.append(ToolMessage(content=f"Ferramenta '{nome}' não encontrada.", tool_call_id=tool_call["id"]))
        else:
            logger.warning("Agente atingiu MAX_ITERATIONS sem resposta final.")
            return {"output": "Desculpe, não consegui processar sua solicitação. Tente reformular a pergunta."}

        texto_final = response.content
        if isinstance(texto_final, list):
            texto_final = "\n".join(
                item["text"] if isinstance(item, dict) and "text" in item else str(item)
                for item in texto_final
            )
        return {"output": str(texto_final)}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def criar_agente(api_key=None, model_name="gemini-2.5-flash") -> AgenteFinanceiro:
    return AgenteFinanceiro(api_key, model_name)

def gerar_titulo_curto(mensagem: str, api_key: str = None) -> str:
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return "Nova Consulta"
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=key, temperature=0.3)
        resp = llm.invoke([
            ("system", "Resuma a mensagem em até 4 palavras em português. Retorne APENAS o título, sem aspas, pontuação ou markdown."),
            ("human", mensagem)
        ])
        titulo = resp.content.strip()
        if isinstance(titulo, list):
            titulo = titulo[0].get("text", "Consulta") if titulo else "Consulta"
        return str(titulo)[:35]
    except Exception as e:
        logger.warning(f"Erro ao gerar título: {e}")
        return "Consulta Finanças"
