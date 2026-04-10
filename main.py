"""
Terminal Financeiro — Bot Telegram para monitoramento financeiro em tempo real.

Verso: 2.2.1 | Autor: Alyson | Licença: MIT
Arquitetura: main.py (roteamento) → util.py (lógica) → API.py (conectividade)
"""

import os
import time
import json
import logging
import threading
import atexit
from dotenv import load_dotenv

import telebot
import requests
import feedparser
import API
import util
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import ExceptionHandler

from API import buscar_preco_binance, buscar_preco_awesome
from util import FONTES_NOTICIAS, speak, formatar_variacao, TEXTO_AJUDA, carregar_alertas, salvar_memoria, carregar_preferencias, salvar_preferencias, compilar_jornal, compilar_radar, MANUAL_COMANDOS, buscar_preco_ativo

# ======================================
#-------CONFIGURAÇÃO E SETUP--------
# ======================================

load_dotenv()

CHAVE_API = os.getenv("CHAVE_API")

if not CHAVE_API:
    raise ValueError("CHAVE_API não encontrada. Crie um arquivo .env com CHAVE_API=<seu_token>")

class NetworkExceptionHandler(ExceptionHandler):
    """Captura erros de rede do pyTelegramBotAPI evitando quebra do loop de polling."""
    def handle(self, exception):
        logger.error(f"Erro de rede capturado: {exception}")
        return True

bot = telebot.TeleBot(CHAVE_API, exception_handler=NetworkExceptionHandler())

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('terminal_financeiro.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

VERSAO = "2.2.1"
DATA_ATUALIZACAO = "09/04/2026"
LOCK_FILE = 'bot.lock'


# --- Estado global carregado do disco ---
alertas_ativos = carregar_alertas()
preferencias_ativas = carregar_preferencias()

def motor_de_alertas():
    """Thread de background: processa alertas one-shot, jornal matinal e radar periodico."""
    logger.info("Motor de alertas iniciado.")
    tempo_decorrido = 0 
    
    while True:
        time.sleep(60)
        tempo_decorrido += 1
        
        try:
            from datetime import datetime, timezone, timedelta
            fuso_br = timezone(timedelta(hours=-3))
            agora = datetime.now(fuso_br)
            hora_atual_str = agora.strftime("%H:%M")
            data_atual_str = agora.strftime("%Y-%m-%d")
            
            for chat_id, pref in preferencias_ativas.items():
                if pref.get('jornal_ativo', False):
                    hora_alvo = pref.get('jornal_hora', '08:00')
                    ultimo_envio = pref.get('jornal_ultimo_envio', '')
                    if hora_atual_str == hora_alvo and ultimo_envio != data_atual_str:
                        try:
                            bot.send_message(chat_id, compilar_jornal(chat_id, pref), parse_mode="Markdown")
                            pref['jornal_ultimo_envio'] = data_atual_str  # só marca após envio ok
                            salvar_preferencias(preferencias_ativas)
                            logger.info(f"Jornal enviado para {chat_id}")
                        except Exception as e:
                            logger.error(f"Erro ao enviar Jornal para {chat_id}: {e}")
            
            if tempo_decorrido >= 90:
                for chat_id, pref in preferencias_ativas.items():
                    if pref.get('radar_ativo', False):
                        texto_radar = compilar_radar(pref)
                        if texto_radar:
                            try:
                                bot.send_message(chat_id, texto_radar, parse_mode="Markdown")
                            except: pass
                tempo_decorrido = 0
                
            if alertas_ativos:
                ocorreu_mudanca = False
                for chat_id in list(alertas_ativos.keys()):
                    alertas_do_usuario = alertas_ativos[chat_id]
                    alertas_restantes = []
                    
                    for alerta in alertas_do_usuario:
                        moeda = alerta['moeda']
                        valor_alvo = alerta['valor']
                        direcao = alerta.get('direcao')
                        
                        preco_atual = buscar_preco_ativo(moeda)
                        if not preco_atual:
                            alertas_restantes.append(alerta)
                            continue
                            
                        if not direcao:
                            direcao = "SUBINDO" if valor_alvo > preco_atual else "CAINDO"
                            alerta['direcao'] = direcao
                        
                        alvo_atingido = (direcao == "SUBINDO" and preco_atual >= valor_alvo) or \
                                        (direcao == "CAINDO" and preco_atual <= valor_alvo)
                        
                        if alvo_atingido:
                            icone = "🟢" if direcao == "SUBINDO" else "🔴"
                            texto = (f"{icone} *ALERTA:* A moeda *{moeda}* atingiu o alvo!\n"
                                     f"Alvo: R$ {valor_alvo:.2f} | Atual: R$ {preco_atual:.2f}")
                            try:
                                bot.send_message(chat_id, texto, parse_mode="Markdown")
                                ocorreu_mudanca = True
                            except:
                                alertas_restantes.append(alerta)
                        else:
                            alertas_restantes.append(alerta)
                    alertas_ativos[chat_id] = alertas_restantes
                if ocorreu_mudanca:
                    salvar_memoria(alertas_ativos)
        except Exception as e:
            logger.error(f"Erro no ciclo do motor: {e}")
            time.sleep(5)

def remover_lock():
    """Remove o arquivo de lock ao encerrar o processo."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

atexit.register(remover_lock)

# --- Interface do usuário ---

def enviar_pergunta(chat_id):
    texto = "Posso ajudar com mais alguma coisa? 🤔\nUtilize /ajuda para ver os comandos e funcionalidades disponíveis."
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(" Mais buscas", callback_data="mais"))
    menu.add(InlineKeyboardButton(" Sair", callback_data="nao"))
    bot.send_message(chat_id, texto, reply_markup=menu)

def desenhar_menu_principal(chat_id, texto_personalizado):
    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(" Moedas Nacionais (Fiat)", callback_data="fiat"))
    menu.add(InlineKeyboardButton(" Criptomoedas", callback_data="cripto"))
    menu.add(InlineKeyboardButton(" Modo Automático", callback_data="automatico"))
    menu.add(InlineKeyboardButton(" Notícias", callback_data="noticias"))
    bot.send_message(chat_id, texto_personalizado, reply_markup=menu)


# --- Handlers de comandos ---

@bot.message_handler(commands=['start'])
def saudacao(mensagem):
    chat_id = mensagem.chat.id
    texto = f"Olá! 👋 O seu Terminal Financeiro Pessoal está online.\n{speak()}\n\nEscolha uma opção:"
    desenhar_menu_principal(chat_id, texto)

@bot.message_handler(commands=['alerta'])
def criar_alerta(mensagem):
    args = mensagem.text.split()
    if len(args) != 3:
        bot.send_message(mensagem.chat.id, " Use: /alerta [MOEDA] [VALOR]\nEx: /alerta BTC 350000")
        return
    
    moeda = args[1].upper()
    try:
        valor_limpo = args[2].replace(',', '.')
        valor = float(valor_limpo)
    except ValueError:
        bot.send_message(mensagem.chat.id, "⚠️ Valor inválido. Informe apenas números.")
        return
    
    chat_id = mensagem.chat.id
    bot.send_message(chat_id, "Validando preço e montando alerta... ")
    
    preco_atual = buscar_preco_binance(moeda + "BRL")
    if not preco_atual:
        preco_atual = buscar_preco_awesome(moeda + "-BRL")
        
    if not preco_atual:
        bot.send_message(chat_id, f"❌ Não localizamos a moeda '{moeda}' hoje. Verifique se a sigla está correta.")
        return
        
    direcao = "SUBINDO" if valor > preco_atual else "CAINDO"
    
    alerta = {"moeda": moeda, "valor": valor, "direcao": direcao, "preco_base": preco_atual}
    
    if str(chat_id) not in alertas_ativos:
        alertas_ativos[str(chat_id)] = []
    
    alertas_ativos[str(chat_id)].append(alerta)
    salvar_memoria(alertas_ativos)
    
    texto_sucesso = f"✅ Alerta ativado para {moeda}!\n\nAtual: R$ {preco_atual:.2f}\nNotificarei quando estiver *{direcao}* o alvo de R$ {valor:.2f}"
    bot.send_message(chat_id, texto_sucesso, parse_mode="Markdown")


@bot.message_handler(commands=['alertas'])
def listar_alertas(mensagem):
    chat_id = mensagem.chat.id
    alertas_usuario = alertas_ativos.get(str(chat_id), [])
    
    if not alertas_usuario:
        bot.send_message(chat_id, "Você não tem alertas ativos. Use /alerta para criar um novo alerta.")
        return
    
    texto = " Seus Alertas Ativos:\n\n"
    for alerta in alertas_usuario:
        texto += f"🔔 {alerta['moeda']} - R$ {alerta['valor']}\n"
    bot.send_message(chat_id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['excluir'])
def excluir_alerta(mensagem):
    args = mensagem.text.split()
    if len(args) != 2:
        bot.send_message(mensagem.chat.id, "⚠️ Use: /excluir [MOEDA]\nEx: /excluir BTC")
        return
    
    moeda_para_remover = args[1].upper()
    chat_id = str(mensagem.chat.id)
    
    if chat_id not in alertas_ativos or not alertas_ativos[chat_id]:
        bot.send_message(mensagem.chat.id, "Você não tem alertas ativos para excluir.")
        return
    
    tamanho_original = len(alertas_ativos[chat_id])
    
    alertas_ativos[chat_id] = [
        a for a in alertas_ativos[chat_id] if a['moeda'] != moeda_para_remover
    ]
    
    if len(alertas_ativos[chat_id]) < tamanho_original:
        salvar_memoria(alertas_ativos)
        bot.send_message(mensagem.chat.id, f"🗑️ Todos os alertas para *{moeda_para_remover}* foram removidos com sucesso!", parse_mode="Markdown")
    else:
        bot.send_message(mensagem.chat.id, f"⚠️ Você não possui alertas aguardando para a moeda {moeda_para_remover}.")

@bot.message_handler(commands=['sobre'])
def comando_sobre(mensagem):
    texto = f"""🤖 *Terminal Financeiro v{VERSAO}* 🤖\n
*Desenvolvido por:* Alyson
*Última atualização:* {DATA_ATUALIZACAO}\n
Bot modularizado para consultas em tempo real.\n📚 Para começar, clique em /start"""
    bot.send_message(mensagem.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['help', 'ajuda'])
def comando_ajuda(mensagem):
    bot.send_message(mensagem.chat.id, TEXTO_AJUDA, parse_mode="Markdown")

@bot.message_handler(commands=['explicar', 'manual'])
def comando_explicar(mensagem):
    args = mensagem.text.split()
    if len(args) < 2:
        bot.send_message(mensagem.chat.id, "⚠️ Use: /explicar [comando]\nExemplo: /explicar alerta")
        return
    
    cmd_alvo = args[1].lower().replace('/', '')
    if cmd_alvo in MANUAL_COMANDOS:
        bot.send_message(mensagem.chat.id, MANUAL_COMANDOS[cmd_alvo], parse_mode="Markdown")
    else:
        bot.send_message(mensagem.chat.id, f"❌ Não encontrei manual para '{cmd_alvo}'. Digite /ajuda para ver as funções.")

@bot.message_handler(commands=['cotar'])
def busca_livre(mensagem):
    args = mensagem.text.split()
    if len(args) < 2:
        bot.send_message(mensagem.chat.id, "⚠️ Use: /cotar [MOEDA]\nEx: /cotar BTC ou /cotar USD")
        return
    
    moeda = args[1].upper()
    chat_id = mensagem.chat.id
    bot.send_message(chat_id, f"Buscando '{moeda}'...")

    # Fallback: Binance -> AwesomeAPI
    preco_atual = buscar_preco_binance(moeda + "BRL")
    fonte = "Binance"
    
    if not preco_atual:
        preco_atual = buscar_preco_awesome(moeda + "-BRL")
        fonte = "AwesomeAPI"
    
    if preco_atual:
        texto = f"🔎 *Busca Livre ({fonte})*\nMoeda: {moeda}\nValor: R$ {preco_atual:.2f}"
        bot.send_message(chat_id, texto, parse_mode="Markdown")
        threading.Timer(2.0, enviar_pergunta, args=[chat_id]).start()
    else:
        bot.send_message(chat_id, f"❌ Moeda '{moeda}' não encontrada na base de dados. Tente usar a sigla oficial (ex: USD, EUR).")

def desenhar_painel_automatico(chat_id, rescrever_mensagem_id=None):
    str_id = str(chat_id)
    if str_id not in preferencias_ativas:
        preferencias_ativas[str_id] = {'jornal_ativo': False, 'jornal_hora': '08:00', 'jornal_fonte': 'g1_economia', 'radar_ativo': False, 'moedas': []}
        salvar_preferencias(preferencias_ativas)
        
    pref = preferencias_ativas[str_id]
    
    st_jornal = "🟢 ON" if pref.get('jornal_ativo', False) else "🔴 OFF"
    st_radar = "🟢 ON" if pref.get('radar_ativo', False) else "🔴 OFF"
    hora = pref.get('jornal_hora', '08:00')
    fonte = FONTES_NOTICIAS.get(pref.get('jornal_fonte', 'g1_economia'), {}).get('nome', 'Fonte')
    qtd_moedas = len(pref.get('moedas', []))

    texto = "Hub Automático\n_Gerencie suas automações em tempo real:_"

    menu = InlineKeyboardMarkup()
    menu.add(InlineKeyboardButton(f"Jornal: {st_jornal}", callback_data="tg_jornal"))
    menu.add(InlineKeyboardButton(f"Hr: {hora}", callback_data="tg_hora"), InlineKeyboardButton(f"Ft: {fonte}", callback_data="tg_fonte"))
    menu.add(InlineKeyboardButton(f"Radar (90m): {st_radar}", callback_data="tg_radar"))
    menu.add(InlineKeyboardButton(f"Moedas ({qtd_moedas})", callback_data="dummy_moedas"))
    menu.add(InlineKeyboardButton("Fechar painel", callback_data="fechar_painel"))
    
    texto_rodape = texto + "\n\n_Dica: Para colocar moedas no radar, digite `/automoeda [SIGLA]`._"

    if rescrever_mensagem_id:
        try:
            bot.edit_message_text(texto_rodape, chat_id, rescrever_mensagem_id, reply_markup=menu, parse_mode="Markdown")
        except: pass
    else:
        bot.send_message(chat_id, texto_rodape, reply_markup=menu, parse_mode="Markdown")

@bot.message_handler(commands=['automatico'])
def modo_automatico(mensagem):
    desenhar_painel_automatico(mensagem.chat.id)

@bot.message_handler(commands=['automoeda'])
def comando_automoeda(mensagem):
    args = mensagem.text.split()
    if len(args) != 2:
        bot.send_message(mensagem.chat.id, "⚠️ Use: /automoeda [SIGLA]\nEx: /automoeda BTC")
        return
    
    sigla = args[1].upper()
    str_id = str(mensagem.chat.id)
    if str_id not in preferencias_ativas:
        desenhar_painel_automatico(mensagem.chat.id)
        
    if sigla not in preferencias_ativas[str_id]['moedas']:
        preferencias_ativas[str_id]['moedas'].append(sigla)
        salvar_preferencias(preferencias_ativas)
        bot.send_message(mensagem.chat.id, f"✅ Moeda {sigla} acoplada! Use /automatico para gerenciar.")
    else:
        bot.send_message(mensagem.chat.id, "⚠️ Essa moeda já pulsa no seu radar.")


@bot.message_handler(commands=['noticias'])
def menu_noticias(mensagem):
    markup = InlineKeyboardMarkup()
    for chave, dados in FONTES_NOTICIAS.items():
        markup.add(InlineKeyboardButton(dados["nome"], callback_data=f"news_{chave}"))
    bot.send_message(mensagem.chat.id, "📰 *Central de Notícias*\n\nEscolha uma fonte:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def resposta_botoes(call):
    """Roteador central de todos os callbacks de botões inline."""
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.warning(f"Erro ao responder callback query: {e}")
    
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
    except Exception as e:
        logger.debug(f"Aviso de interface (Markup): {e}")
    
    comando = call.data
    chat_id = call.message.chat.id
    
    
    if comando == "mais":
        desenhar_menu_principal(chat_id, "Qual vai ser a próxima busca?")
        
    elif comando == "automatico":
        desenhar_painel_automatico(chat_id)
        
    elif comando == "noticias":
        menu_noticias(call.message)
        
    elif comando == "fiat":
        bot.send_message(chat_id, "Buscando moedas nacionais... ")
        try:
            dados = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL,JPY-BRL", timeout=5).json()
            texto = f"*Cotações Nacionais (Fiat)*\n\n💵 Dólar: R$ {dados['USDBRL']['bid']}\n💶 Euro: R$ {dados['EURBRL']['bid']}\n💷 Libra: R$ {dados['GBPBRL']['bid']}\n💴 JPY: R$ {dados['JPYBRL']['bid']}"
            bot.send_message(chat_id, texto, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Erro buscar Fiat: {e}")
            bot.send_message(chat_id, "❌ Erro ao buscar moedas Fiat.")
        threading.Timer(3.0, enviar_pergunta, args=[chat_id]).start()
        
    elif comando == "cripto":
        bot.send_message(chat_id, "Buscando principais criptos...")
        try:
            dados = requests.get("https://economia.awesomeapi.com.br/last/ETH-BRL,BTC-BRL,DOGE-BRL,LTC-BRL", timeout=5).json()
            texto = f"🪙 *Principais Criptomoedas*\n\n♦️ Ethereum: R$ {dados['ETHBRL']['bid']}\n₿ Bitcoin: R$ {dados['BTCBRL']['bid']}\nŁ Litecoin: R$ {dados['LTCBRL']['bid']}\n🐕 Dogecoin: R$ {dados['DOGEBRL']['bid']}"
            bot.send_message(chat_id, texto, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Erro ao buscar Cripto: {e}")
            bot.send_message(chat_id, "❌ Erro ao buscar Criptos.")
        threading.Timer(3.0, enviar_pergunta, args=[chat_id]).start()

    elif comando.startswith("news_"):
        chave = comando.replace("news_", "")
        url = FONTES_NOTICIAS[chave]["url"]
        bot.send_message(chat_id, f"Buscando as últimas de {FONTES_NOTICIAS[chave]['nome']}... ⏳")
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                bot.send_message(chat_id, "⚠️ Fonte indisponível no momento.")
                return

            texto = f"📰 *{FONTES_NOTICIAS[chave]['nome']}*\n\n"
            for noticia in feed.entries[:5]:
                texto += f"🔹 *{noticia.title}*\n🔗 [Ler a matéria]({noticia.link})\n\n"
            bot.send_message(chat_id, texto, parse_mode="Markdown", disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Erro RSS: {e}")
            bot.send_message(chat_id, "❌ Falha ao ler notícias.")
        threading.Timer(3.0, enviar_pergunta, args=[chat_id]).start()
    elif comando == "nao":
        bot.send_message(chat_id, "Até a próxima! 👋")
        
    elif comando == "tg_jornal":
        str_id = str(chat_id)
        preferencias_ativas[str_id]['jornal_ativo'] = not preferencias_ativas[str_id].get('jornal_ativo', False)
        salvar_preferencias(preferencias_ativas)
        desenhar_painel_automatico(chat_id, call.message.message_id)
        
    elif comando == "tg_radar":
        str_id = str(chat_id)
        preferencias_ativas[str_id]['radar_ativo'] = not preferencias_ativas[str_id].get('radar_ativo', False)
        salvar_preferencias(preferencias_ativas)
        desenhar_painel_automatico(chat_id, call.message.message_id)
        
    elif comando == "tg_hora":
        str_id = str(chat_id)
        hora_atual_conf = preferencias_ativas[str_id].get('jornal_hora', '08:00')
        ordem = ['06:00', '07:00', '08:00', '09:00', '12:00', '15:00', '18:00', '21:00']
        idx = ordem.index(hora_atual_conf) if hora_atual_conf in ordem else 0
        prox_idx = (idx + 1) % len(ordem)
        preferencias_ativas[str_id]['jornal_hora'] = ordem[prox_idx]
        salvar_preferencias(preferencias_ativas)
        desenhar_painel_automatico(chat_id, call.message.message_id)
        
    elif comando == "tg_fonte":
        str_id = str(chat_id)
        fonte_atual = preferencias_ativas[str_id].get('jornal_fonte', 'g1_economia')
        chaves = list(FONTES_NOTICIAS.keys())
        idx = chaves.index(fonte_atual) if fonte_atual in chaves else 0
        prox_idx = (idx + 1) % len(chaves)
        preferencias_ativas[str_id]['jornal_fonte'] = chaves[prox_idx]
        salvar_preferencias(preferencias_ativas)
        desenhar_painel_automatico(chat_id, call.message.message_id)
        
    elif comando == "fechar_painel":
        if comando == "fechar_painel":
            desenhar_menu_principal(chat_id, "Hub fechado. O que deseja consultar agora?")
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            bot.send_message(chat_id, "Hub fechado. Use /automatico para reabrir.")

    elif comando == "dummy_moedas":
        bot.send_message(chat_id, "Use o comando /automoeda [SIGLA] no chat para acoplar moedas ao motor.")
        
    else:
        bot.send_message(chat_id, "Comando ausente da interface, tente /ajuda.") 
    


# --- Entrypoint ---

if __name__ == "__main__":
    if os.path.exists(LOCK_FILE):
        logger.error("Já existe uma instância do bot rodando!")
        exit(1)
        
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
        
    logger.info(f"Terminal Financeiro v{VERSAO} iniciado!")
    logger.info("Aguardando mensagens...")
    threading.Thread(target=motor_de_alertas, daemon=True).start()
    try:
        bot.infinity_polling(timeout=60, skip_pending=True)
    except KeyboardInterrupt:
        logger.info(" Bot interrompido.")
    finally:
        remover_lock()