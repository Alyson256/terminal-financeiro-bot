"""
util.py — Utilitários, persistência e compiladores de texto.

Contém: constantes de configuração, funções de I/O (JSON),
formatadores de mensagem e compiladores do Hub Automático.
"""
import logging
import json
import feedparser
from datetime import datetime, timedelta, timezone

from API import buscar_preco_binance, buscar_preco_awesome

logger = logging.getLogger(__name__)

# --- Fontes RSS disponíveis no Hub ---

FONTES_NOTICIAS = {
    "g1_economia": {
        "nome": "G1 Economia (Geral)",
        "url": "https://g1.globo.com/rss/g1/economia/"
    },
    "livecoins": {
        "nome": "Livecoins (Cripto)",
        "url": "https://livecoins.com.br/feed/"
    },
    "criptofacil": {
        "nome": "CriptoFácil",
        "url": "https://www.criptofacil.com/feed/"
    },
    "cointelegraph": {
        "nome": "CoinTelegraph",
        "url": "https://br.cointelegraph.com/rss"
    }
}


# --- Formatação e utilidades ---

def speak():
    """Retorna uma saudação baseada na hora do dia (horário de Brasília)."""
    hora_atual = (datetime.now(timezone.utc) - timedelta(hours=3)).hour
    if hora_atual <= 12:
        return "Tenha um excelente dia! ☀️"
    elif hora_atual <= 18:
        return "Boa tarde! 🌤️"
    else:
        return "Boa noite! 🌙"

def formatar_variacao(variacao_str):
    """
    Formata a variação percentual com emojis.
    """
    try:
        valor_limpo = str(variacao_str).replace(',', '.')
        valor = float(valor_limpo)
        if valor > 0:
            return f"🟢 +{valor_limpo}%"
        elif valor < 0:
            return f"🔴 {valor_limpo}%"
        else:
            return f"⚪ {valor_limpo}%"
    except (ValueError, AttributeError) as e:
        logger.error(f"Erro ao formatar variação: {e}")
        return f"{variacao_str}%"

TEXTO_AJUDA = '''  Consultas de Cotações:
/cotar [MOEDA] - Busca cotação de qualquer moeda
/fiat - Moedas nacionais (USD, EUR, GBP, JPY)
/cripto - Criptomoedas (BTC, ETH, LTC, DOGE)

⚙️ Hub Automático Pessoal:
/automatico - Abre o painel interativo de Jornal e Radar
/automoeda [SIGLA] - Cola uma moeda no seu radar

🚨 Alertas de Preço:
/alerta [MOEDA] [VALOR] - Ex: /alerta BTC 350000
/alertas - Lista seus alertas ativos
/excluir [MOEDA] - Remove um alerta

📰 Notícias:
/noticias - Menu de notícias do mercado

❓ Outros:
/ajuda - Mostra este menu
/sobre - Informações do bot
/explicar - Explica o funcionamento dos comandos do bot
/start - Menu principal
'''

MANUAL_COMANDOS = {
    "cotar": "🔍 */cotar [MOEDA]*\n\nBusca o preço em tempo real conectando as APIs adequadas (Cripto ou Fiat).\n💡 Exemplo prático: `/cotar BTC` ou `/cotar EUR`.",
    "automatico": "⚙️ */automatico*\n\nAbre o Painel Interativo.\nNele você liga e desliga o *Jornal Matinal* (que envia notícias com suas moedas no horário agendado) e o *Radar* (que envia o preço das suas moedas a cada 90 mins).",
    "automoeda": "🪙 */automoeda [MOEDA]*\n\nAssocia uma moeda de sua escolha às suas rotinas do /automatico. \n💡 Exemplo: `/automoeda ETH`.",
    "alerta": "🚨 */alerta [MOEDA] [VALOR]*\n\nCria um vigilante silencioso. O bot fica rastreando e avisa APENAS quando a moeda bater naquele alvo exato.\n💡 Exemplo: `/alerta BTC 350000`.",
    "alertas": "📋 */alertas*\n\nLista de forma enxuta todos os seus alertas ativos.",
    "excluir": "🗑️ */excluir [MOEDA]*\n\nApaga imediatamente um alerta e para de rastreá-lo.",
    "noticias": "📰 */noticias*\n\nAbre um painel de acesso rápido para puxar as últimas 5 manchetes das principais fontes financeiras (G1, Livecoins etc)."
}



# --- Persistência em disco (JSON) ---

def carregar_alertas() -> dict:
    """Carrega alertas do disco. Reseta para vazio se o arquivo estiver corrompido."""
    try:
        with open('memoria_alertas.json', 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read().strip()
            if not conteudo:
                return {}
            return json.loads(conteudo)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"memoria_alertas.json corrompido, resetando: {e}")
        return {}
    except Exception as e:
        logger.error(f"Erro ao carregar alertas: {e}")
        return {}

def salvar_memoria(alertas):
    try:
        with open('memoria_alertas.json', 'w', encoding='utf-8') as arquivo:
            json.dump(alertas, arquivo, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Erro ao salvar alertas: {e}")

def carregar_preferencias():
    try:
        with open('preferencias_usuarios.json', 'r', encoding='utf-8') as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar preferencias: {e}")
        return {}

def salvar_preferencias(prefs):
    try:
        with open('preferencias_usuarios.json', 'w', encoding='utf-8') as arquivo:
            json.dump(prefs, arquivo, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ Erro ao salvar preferencias: {e}")

def buscar_preco_ativo(moeda: str) -> float | None:
    """
    Roteamento inteligente de preço: tenta Binance apenas para criptos;
    moedas fiat (4 letras e pares conhecidos) vão direto para AwesomeAPI.
    """
    MOEDAS_FIAT = {"USD", "EUR", "GBP", "JPY", "ARS", "CHF", "AUD", "CAD", "CNY", "MXN"}
    if moeda.upper() in MOEDAS_FIAT:
        return buscar_preco_awesome(moeda + "-BRL")
    preco = buscar_preco_binance(moeda + "BRL")
    if not preco:
        preco = buscar_preco_awesome(moeda + "-BRL")
    return preco


def compilar_jornal(chat_id: str, pref: dict) -> str:
    fonte_chave = pref.get('jornal_fonte', 'g1_economia')
    url = FONTES_NOTICIAS.get(fonte_chave, FONTES_NOTICIAS['g1_economia'])['url']
    nome_fonte = FONTES_NOTICIAS.get(fonte_chave, FONTES_NOTICIAS['g1_economia'])['nome']
    
    def speak_jornal():
        hora_atual = (datetime.now(timezone.utc) - timedelta(hours=3)).hour
        if hora_atual <= 12:
            return "Aqui estão as notícias para começar seu dia! ☀️"
        elif hora_atual <= 18:
            return "Vamos dar uma olhada nas notícias do dia? 🌤️"
        else:
            return "Confira as últimas notícias para fechar seu dia bem informado! 🌙"

    try:
        feed = feedparser.parse(url)
        for noticia in feed.entries[:3]:
            texto += f"🔹 {noticia.title} {noticia.link}\n"
    except:
        texto += "⚠️ Módulo de notícias indisponível hoje.\n"
        
    moedas = pref.get('moedas', [])
    if moedas:
        texto += "\n *Suas Moedas Favoritas:*\n"
        for m in moedas:
            preco = buscar_preco_ativo(m)
            if preco:
                texto += f"• {m}: R$ {preco:.2f}\n"
            else:
                texto += f"• {m}: indisponível hoje.\n"
    return texto

def compilar_radar(pref):
    moedas = pref.get('moedas', [])
    if not moedas:
        return None
    
    texto = "📡 *RADAR DE MERCADO (90 min)*\n\n"
    for m in moedas:
        preco = buscar_preco_ativo(m)
        if preco:
            texto += f"• {m}: R$ {preco:.2f}\n"
    return texto
