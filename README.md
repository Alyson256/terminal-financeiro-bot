# Terminal Financeiro — Bot Telegram

[![PT-BR](https://img.shields.io/badge/Portugu%C3%AAs-PT--BR-green)](README.md)
[![EN](https://img.shields.io/badge/English-EN-blue)](README_en.md)

Bot Telegram modular para monitoramento financeiro em tempo real. Consulte cotações de moedas e criptomoedas, configure alertas de preço personalizados e automatize resumos matinais com feeds de notícias.

![Version](https://img.shields.io/badge/version-2.3.5-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🧪 Como Testar (Beta Testing)

O Terminal Financeiro (v2.3.5) está rodando na nuvem (Google Cloud) e aberto para testes da comunidade! O objetivo agora é estressar o sistema e testar o cache.

1. **Acesse o Bot:**[Clique aqui para abrir no Telegram](https://web.telegram.org/a/#8639694375)
2. **Inicie o Sistema:** Envie o comando `/start`.
3. **Estresse a Máquina:**
   - Teste os botões interativos de `/fiat` e `/cripto`.  
   - Faça buscas livres com `/cotar BTC` ou digite moedas que não existem (ex: `/cotar BLA`) para testar o nosso tratamento de erros.
   - Explore o hub interativo digitando `/automatico` e acople moedas no seu radar com `/automoeda`.
4. **Encontrou um Bug?** Conseguiu quebrar o bot? Ele travou ou não respondeu? Por favor, abra uma **Issue** aqui no repositório com um print da tela ou me envie uma mensagem direta!
  
--

## Recursos V(2.3.5)

- **Cloud-Ready (Hotfixes de Estabilidade)** — Operações de I/O blindadas com `threading.Lock` e *parsers* de requisições isolados com limites de tempo (`timeouts`) para garantir tolerância à falhas em nuvem.
- **Cotações em tempo real** — Moedas Fiat (USD, EUR, GBP, JPY) e criptomoedas via Binance e AwesomeAPI
- **Busca livre** — Qualquer ativo pelo símbolo oficial com fallback automático entre APIs
- **Sistema de alertas** — Notificação one-shot sem perda de dados (proteção contra *Race Conditions*)
- **Hub Automático** — Jornal matinal agendado e radar de mercado a cada 90 minutos
- **Central de notícias** — Feeds RSS de G1, Livecoins, CriptoFácil e CoinTelegraph
- **Manual dinâmico** — Comando `/explicar` com instruções detalhadas por funcionalidade

---

## Instalação

### Pré-requisitos
- Python 3.10 ou superior
- Um bot Telegram criado via [@BotFather](https://t.me/BotFather)

### 1. Clonar o repositório
```bash
git clone https://github.com/AlysonRN/terminal-financeiro.git
cd terminal-financeiro
```

### 2. Criar o ambiente virtual e instalar dependências
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# ou
source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
CHAVE_API=seu_token_do_telegram_aqui
```

### 4. Executar
```bash
python main.py
```

---

## Comandos

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/start` | Menu principal interativo | `/start` |
| `/cotar [MOEDA]` | Cotação de qualquer ativo (cripto ou fiat) | `/cotar ETH` |
| `/fiat` | Cotações das principais moedas nacionais | `/fiat` |
| `/cripto` | Cotações das principais criptomoedas | `/cripto` |
| `/automatico` | Painel do Hub Automático (Jornal + Radar) | `/automatico` |
| `/automoeda [SIGLA]` | Associa uma moeda ao seu radar/jornal | `/automoeda BTC` |
| `/noticias` | Menu de fontes de notícias financeiras | `/noticias` |
| `/alerta [MOEDA] [VALOR]` | Cria alerta de preço | `/alerta BTC 350000` |
| `/alertas` | Lista alertas ativos | `/alertas` |
| `/excluir [MOEDA]` | Remove um alerta | `/excluir BTC` |
| `/explicar [COMANDO]` | Explicação detalhada de um comando | `/explicar automatico` |
| `/ajuda` | Lista todos os comandos | `/ajuda` |
| `/sobre` | Informações da versão | `/sobre` |

---

## Arquitetura

O projeto é dividido em três camadas com responsabilidades bem definidas:

```
main.py     → Roteamento: handlers de comandos, callbacks e entrypoint
  ↓
util.py     → Lógica: persistência JSON, formatadores e compiladores de texto
  ↓
API.py      → Conectividade: requisições às APIs externas (Binance, AwesomeAPI)
```

### Estrutura de arquivos
```
.
├── main.py                    # Entrypoint e handlers do bot
├── API.py                     # Funções de busca de preço
├── util.py                    # Utilitários, persistência e compiladores
├── requirements.txt           # Dependências do projeto
├── .env                       # Token do bot (não commitar)
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

> Os arquivos `memoria_alertas.json`, `preferencias_usuarios.json`, `bot.lock` e `terminal_financeiro.log` são gerados automaticamente em tempo de execução e não fazem parte do repositório.

---

## APIs Utilizadas

| API | Uso | Autenticação |
|-----|-----|-------------|
| [CoinGecko](https://www.coingecko.com/en/api) | Preços de criptomoedas | Pública (Sujeito a Rate Limit) |
| [HG Brasil](https://hgbrasil.com/) | Preços de moedas fiat | Requer Chave API (`HG_API_KEY`) |
| Feeds RSS | Notícias financeiras | Pública |

---

## Hub Automático

O Hub Automático oferece duas assinaturas independentes por usuário:

- **Jornal Matinal** — Envia automaticamente no horário configurado (06h às 21h) um resumo com as 3 últimas manchetes da fonte escolhida e os preços das moedas favoritas.
- **Radar de Mercado** — Envia os preços das moedas favoritas a cada 90 minutos, enquanto ativado.

Use `/automatico` para ligar/desligar cada módulo e `/automoeda [SIGLA]` para vincular ativos ao seu painel.

---

## Segurança

- Nunca commite o arquivo `.env` — ele já está no `.gitignore`
- Os dados de alertas e preferências são armazenados localmente, nunca transmitidos a terceiros
- O arquivo `bot.lock` previne múltiplas instâncias simultâneas do bot

---

## Licença

Distribuído sob a [MIT License](LICENSE).

---

## Autor

**Alyson** · [github.com/Alyson256](https://github.com/Alyson256)
