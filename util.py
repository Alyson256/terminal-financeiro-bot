"""
util.py — Utilitários, persistência e compiladores de texto.

Contém: constantes de configuração, funções de I/O (JSON),
formatadores de mensagem e compiladores do Hub Automático.
"""
import logging
import json
import feedparser
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from functools import lru_cache
import time
import threading
import requests

from apifinanceira import buscar_preco_hgbrasil, buscar_preco_coingecko

logger = logging.getLogger(__name__)

lock_io = threading.Lock()

# --- Configuração de Cache e Timeouts ---
CACHE_PRECO_SECONDS = 60  # 1 minuto (mais agressivo para preços em tempo real)
API_TIMEOUT_SECONDS = 2  # Reduzido de 5 para 2 segundos (otimizado)
FEEDPARSER_TIMEOUT_SECONDS = 3  # Reduzido de 10 para 3 segundos

# --- Estrutura Escalável de Alertas ---

class AlertaAtivo:
    """Classe para padronizar alertas de diferentes tipos de ativos."""
    
    def __init__(self, usuario_id: str, moeda: str, valor_alvo: float, tipo: str = "cripto"):
        """
        Args:
            usuario_id: ID do usuário no Telegram
            moeda: Símbolo do ativo (BTC, USD, PETR4)
            valor_alvo: Valor a ser monitorado
            tipo: Tipo de ativo ("cripto", "fiat", "acao")
        """
        self.usuario_id = usuario_id
        self.moeda = moeda
        self.valor_alvo = valor_alvo
        self.tipo = tipo
        self.criado_em = datetime.now(timezone.utc).isoformat()
    
    def para_dict(self) -> Dict[str, Any]:
        """Converte alerta para dicionário (para JSON)."""
        return {
            'usuario_id': self.usuario_id,
            'moeda': self.moeda,
            'valor_alvo': self.valor_alvo,
            'tipo': self.tipo,
            'criado_em': self.criado_em
        }
    
    @classmethod
    def de_dict(cls, dados: Dict[str, Any]) -> 'AlertaAtivo':
        """Reconstrói alerta a partir de dicionário."""
        return cls(
            dados['usuario_id'],
            dados['moeda'],
            dados['valor_alvo'],
            dados.get('tipo', 'cripto')
        )


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
    "noticias": "📰 */noticias*\n\nAbre um painel de acesso rápido para puxar as últimas 5 manchetes das principais fontes financeiras (G1, Livecoins etc).",
    "bolsas": "💹 */bolsas*\n\nMostra as principais bolsas de valores e seus índices."
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

def salvar_memoria(alertas: Dict[str, Any]) -> None:
    """Salva alertas em disco com tratamento de erro específico."""
    with lock_io:
        try:
            alertas_copy = alertas.copy()
            with open('memoria_alertas.json', 'w', encoding='utf-8') as arquivo:
                json.dump(alertas_copy, arquivo, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"❌ Erro de I/O ao salvar alertas: {e}")
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao salvar alertas: {e}")

def carregar_preferencias() -> Dict[str, Any]:
    """Carrega preferências do usuário com validação."""
    try:
        with open('preferencias_usuarios.json', 'r', encoding='utf-8') as arquivo:
            prefs = json.load(arquivo)
            # Validação de estrutura mínima
            if not isinstance(prefs, dict):
                logger.warning("Preferências corrompidas, resetando")
                return {}
            return prefs
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao decodificar preferências: {e}")
        return {}
    except Exception as e:
        logger.error(f"❌ Erro ao carregar preferências: {e}")
        return {}

def salvar_preferencias(prefs: Dict[str, Any]) -> None:
    """Salva preferências do usuário com tratamento de erro específico."""
    with lock_io:
        try:
            prefs_copy = prefs.copy()
            with open('preferencias_usuarios.json', 'w', encoding='utf-8') as arquivo:
                json.dump(prefs_copy, arquivo, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"❌ Erro de I/O ao salvar preferências: {e}")
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao salvar preferências: {e}")

def buscar_preco_ativo(moeda: str, tipo: str = "cripto") -> Optional[float]:
    """
    Busca preço de ativo com roteamento inteligente.
    
    Args:
        moeda: Símbolo da moeda (BTC, USD, etc)
        tipo: Tipo de ativo ("cripto", "fiat" ou "acao")
    
    Returns:
        Preço em float ou None se indisponível
    """
    MOEDAS_FIAT = {"USD", "EUR", "GBP", "JPY", "ARS", "CHF", "AUD", "CAD", "CNY", "MXN"}
    
    try:
        if tipo == "fiat" or moeda.upper() in MOEDAS_FIAT:
            return buscar_preco_hgbrasil(moeda)
        elif tipo == "cripto":
            preco = buscar_preco_coingecko(moeda)
            # HG Brasil também tem cotação do Bitcoin como fallback, podemos tentar se CoinGecko falhar
            if not preco and moeda.upper() == 'BTC':
                preco = buscar_preco_hgbrasil('BTC')
            return preco
        # Tipo "acao" será implementado com API de bolsa
        elif tipo == "acao":
            logger.warning(f"Tipo 'acao' ainda não implementado para {moeda}")
            return None
    except Exception as e:
        logger.error(f"Erro ao buscar preço de {moeda} ({tipo}): {e}")
        return None


def compilar_jornal(chat_id: str, pref: Dict[str, Any]) -> str:
    """
    Compila jornal com notícias RSS e cotações de moedas favoritas.
    
    Returns:
        String formatada com notícias e cotações
    """
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

    texto = speak_jornal() + "\n"
    
    try:
        # Timeout otimizado: 3s para feeds RSS
        resposta = requests.get(url, timeout=3)
        feed = feedparser.parse(resposta.text)
        if feed.bozo:  # Aviso do feedparser sobre problemas
            logger.warning(f"Feed RSS pode estar malformado: {url}")
        
        noticia_count = 0
        for noticia in feed.entries[:3]:
            try:
                texto += f"🔹 {noticia.get('title', 'Sem título')} {noticia.get('link', '')}\n"
                noticia_count += 1
            except AttributeError as e:
                logger.warning(f"Erro ao processar notícia: {e}")
                continue
        
        if noticia_count == 0:
            texto += "⚠️ Nenhuma notícia disponível no momento.\n"
    except Exception as e:
        logger.error(f"Erro ao buscar RSS de {nome_fonte}: {e}")
        texto += "⚠️ Módulo de notícias indisponível hoje.\n"
        
    moedas = pref.get('moedas', [])
    if moedas:
        texto += "\n *Suas Moedas Favoritas:*\n"
        for m in moedas:
            tipo = pref.get('moedas_tipos', {}).get(m, 'cripto')  # Novo: tipo de moeda
            preco = buscar_preco_ativo(m, tipo)
            if preco:
                texto += f"• {m}: R$ {preco:.2f}\n"
            else:
                texto += f"• {m}: indisponível hoje.\n"
    return texto

def compilar_radar(pref: Dict[str, Any]) -> Optional[str]:
    """
    Compila radar de mercado com cotações em tempo real.
    
    Returns:
        String formatada com preços ou None se sem moedas
    """
    moedas = pref.get('moedas', [])
    if not moedas:
        return None
    
    texto = "📡 *RADAR DE MERCADO (90 min)*\n\n"
    for m in moedas:
        tipo = pref.get('moedas_tipos', {}).get(m, 'cripto')  # Novo: tipo de moeda
        preco = buscar_preco_ativo(m, tipo)
        if preco:
            texto += f"• {m}: R$ {preco:.2f}\n"
        else:
            texto += f"• {m}: indisponível.\n"
    return texto
