"""
API.py — Camada de conectividade com APIs externas.

Fornece funções de busca de preços via Binance e AwesomeAPI.
Não contém lógica de negócio; apenas faz requisições e retorna valores.
"""
import requests
import logging

logger = logging.getLogger(__name__)

ENDPOINTS = {
    "binance": "https://api1.binance.com/api/v3/ticker/price",
    "awesome": "https://economia.awesomeapi.com.br/last/"
}

def buscar_preco_binance(simbolo: str) -> float | None:
    """Busca o preço de um par na Binance. Ex: 'BTCBRL'. Retorna float ou None."""
    url = ENDPOINTS["binance"]
    params = {"symbol": simbolo.upper()}
    
    try:
        resposta = requests.get(url, params=params, timeout=5)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            return float(dados["price"])
        else:
            logger.warning(f"Binance retornou status {resposta.status_code} para {simbolo}")
            return None
            
    except Exception as e:
        logger.error(f"Erro na API Binance: {e}")
        return None
    
def buscar_preco_awesome(simbolo):
    """
    Busca o preço na AwesomeAPI.
    Atenção: A AwesomeAPI usa pares separados por hífen. Ex: 'BTC-USD' (Bitcoin para Dólar) ou 'BTC-BRL' (Bitcoin para Real).
    """
    url = ENDPOINTS["awesome"] + simbolo.upper()
    
    try:
        resposta = requests.get(url, timeout=5)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            chave = list(dados.keys())[0]  # Ex: 'BTCUSD'
            return float(dados[chave]["bid"])
        else:
            logger.warning(f"AwesomeAPI retornou status {resposta.status_code} para {simbolo}")
            return None
            
    except Exception as e:
        logger.error(f"Erro na API AwesomeAPI: {e}")
        return None


