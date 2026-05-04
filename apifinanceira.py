import requests
import logging
import os
from dotenv import load_dotenv
from cachetools import cached, TTLCache

# Carrega as variáveis do .env (necessário para testes locais)
load_dotenv()

# Instâncias de cache (100 itens, expiram em 60 segundos)
cache_fiat = TTLCache(maxsize=100, ttl=60)
cache_cripto = TTLCache(maxsize=100, ttl=60)

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

@cached(cache=cache_fiat)
def buscar_preco_hgbrasil(simbolo: str) -> float | None:
    """Busca o preço de moedas Fiat na HG Brasil."""
    url = "https://api.hgbrasil.com/finance"
    chave_api = os.getenv('HG_API_KEY')
    
    moeda_limpa = simbolo.upper().replace('BRL', '').replace('-', '').strip()
    
    parametros = {
        'key': chave_api,
        'format': 'json',
        'fields': 'only_results,currencies'
    }
    
    try:
        resposta = requests.get(url, params=parametros, timeout=5) 
        
        if resposta.status_code == 200:
            dados = resposta.json()
            
            if 'currencies' in dados:
                if moeda_limpa in dados['currencies']:
                    return float(dados['currencies'][moeda_limpa]['buy'])
            
            logger.warning(f"Moeda {moeda_limpa} não encontrada na HG Brasil.")
            return None
        else:
            logger.warning(f"HG Brasil retornou erro {resposta.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Erro na comunicação com HG Brasil: {e}")
        return None



@cached(cache=cache_cripto)
def buscar_preco_coingecko(simbolo: str) -> float | None:
    """
    Busca o preço na CoinGecko autenticada.
    """
    simbolo_limpo = simbolo.upper().replace('BRL', '').replace('-', '').strip()
    
    mapa_moedas = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'DOGE': 'dogecoin',
        'LTC': 'litecoin',
        'MATIC': 'matic-network',
        'SOL': 'solana'
    }
    
    id_moeda = mapa_moedas.get(simbolo_limpo)
    
    if not id_moeda:
        logger.warning(f"Sigla '{simbolo_limpo}' não está mapeada para a CoinGecko.")
        return None

    url = "https://api.coingecko.com/api/v3/simple/price"
    
    # Puxa a nova chave do cofre .env
    chave_api_cg = os.getenv('COINGECKO_API_KEY')
    
    parametros = {
        'ids': id_moeda,
        'vs_currencies': 'brl'
    }
    
    cabecalhos = {
        'x-cg-demo-api-key': chave_api_cg
    }
    
    try:
        resposta = requests.get(url, params=parametros, headers=cabecalhos, timeout=5)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            
            if id_moeda in dados and 'brl' in dados[id_moeda]:
                return float(dados[id_moeda]['brl'])
                
            logger.warning(f"Preço de {id_moeda} não retornado pela CoinGecko.")
            return None
        else:
            logger.warning(f"CoinGecko retornou erro {resposta.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Erro na comunicação com CoinGecko: {e}")
        return None


