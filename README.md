# J.A.R.V.I.S-Lite — Data Orchestrator & Personal Assistant

[![EN](https://img.shields.io/badge/English-EN-blue)](README.md)
[![PT-BR](https://img.shields.io/badge/Portugu%C3%AAs-PT--BR-green)](README_pt.md)

**J.A.R.V.I.S-Lite** (formerly Financial Terminal) is a modular Super App built in Python running via Telegram. It acts as a data orchestrator and personal assistant designed for real-time monitoring and structurally prepared for the upcoming integration of the **Google Gemini API**, which will elevate the project with natural language processing and global conversational flows.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🧪 How to Test (Beta Testing)


The core of J.A.R.V.I.S-Lite (v3.0.0) is currently under development. When it's ready, I'll apply the commit with the new orchestration flows!

1. **Access the Bot:**[Click here to open in Telegram](https://t.me/cotsson_bot)
2. **Boot the System:** Send the `/start` command.
3. **Stress Test It:**
   - Try the interactive buttons for `/fiat` and `/cripto`.
   - Run custom queries like `/cotar BTC` or try nonexistent coins (e.g., `/cotar BLA`) to test the error handling.
   - Explore the interactive hub using `/automatico` and attach coins to your radar via `/automoeda`.
4. **Found a Bug?** Did you break the bot? Did it crash or stop responding? Please open an **Issue** in this repository with a screenshot or send me a direct message!

---

## Features V(3.0.0)

- **[NEW] Orchestration Architecture** — Structural preparation to integrate the Google Gemini API as the brain of the data flow and interactive personal assistant.
- **Cloud-Ready Financial Module** — I/O operations secured with `threading.Lock` and isolated request parsers with `timeouts`.
- **Network Intelligence (Anti-Geoblock)** — Real-time quotes via CoinGecko and HG Brasil mitigated by smart RAM caching via `cachetools`.
- **Free Search** — Any asset by its official symbol with automatic API fallbacks.
- **Alert System** — One-shot notifications with zero data loss (secured against *Race Conditions*).
- **Automated Hub** — Scheduled morning news briefs and market radar every 90 minutes.
- **News Center** — RSS feeds from major Brazilian financial news portals (G1, Livecoins, CriptoFácil, and CoinTelegraph).
- **Dynamic Manual** — `/explicar` command with detailed instructions per feature.

---

## Installation

### Prerequisites
- Python 3.10 or higher
- A Telegram bot created via [@BotFather](https://t.me/BotFather)

### 1. Clone the repository
```bash
git clone https://github.com/AlysonRN/terminal-financeiro.git
cd terminal-financeiro
```

### 2. Create a virtual environment and install dependencies
```bash
python -m venv .venv
.\.venv\Scripts\activate      # Windows
# or
source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```env
CHAVE_API=your_telegram_bot_token_here
```

### 4. Run
```bash
.\.venv\Scripts\python main.py
```

---

## Commands

| Command | Description | Example |
|---------|-----------|---------|
| `/start` | Interactive main menu | `/start` |
| `/cotar [COIN]` | Quote for any asset (crypto or fiat) | `/cotar ETH` |
| `/fiat` | Top national fiat currency quotes | `/fiat` |
| `/cripto` | Top cryptocurrency quotes | `/cripto` |
| `/automatico` | Automated Hub Dashboard (News + Radar) | `/automatico` |
| `/automoeda [SYMBOL]` | Binds a coin to your radar/news | `/automoeda BTC` |
| `/noticias` | Financial news sources menu | `/noticias` |
| `/alerta [COIN] [VALUE]` | Creates a price alert | `/alerta BTC 350000` |
| `/alertas` | Lists active alerts | `/alertas` |
| `/excluir [COIN]` | Removes an alert | `/excluir BTC` |
| `/explicar [CMD]` | Detailed explanation of a command | `/explicar automatico` |
| `/ajuda` | Lists all commands | `/ajuda` |
| `/sobre` | Version information | `/sobre` |

---

## Architecture

The project is divided into three layers with well-defined responsibilities:

```
main.py     → Routing: command handlers, callbacks, and entrypoint
  ↓
util.py     → Logic: JSON persistence, formatters, and text compilers
  ↓
API.py      → Connectivity: external API requests (Binance, AwesomeAPI)
```

### File Structure
```
.
├── main.py                    # Entrypoint and bot handlers
├── API.py                     # Price fetch functions
├── util.py                    # Utilities, persistence, and compilers
├── requirements.txt           # Project dependencies
├── .env                       # Bot token (do not commit)
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

> The files `memoria_alertas.json`, `preferencias_usuarios.json`, `bot.lock`, and `terminal_financeiro.log` are automatically generated at runtime and are not tracked by the repository.

---

## Used APIs

| API | Use Case | Authentication |
|-----|----------|----------------|
| [CoinGecko](https://www.coingecko.com/en/api) | Crypto prices | Public (Rate-limited) |
| [HG Brasil](https://hgbrasil.com/) | Fiat prices | Requires API Key (`HG_API_KEY`) |
| RSS Feeds | Financial news | Public |

---

## Automated Hub

The Automated Hub offers two independent subscriptions per user:

- **Morning News (Jornal)** — Sends a summary with the 3 latest headlines from the chosen source and favorite coin prices automatically at the configured time (06:00 to 21:00).
- **Market Radar (Radar)** — Sends favorite coin prices every 90 minutes while active.

Use `/automatico` to toggle each module and `/automoeda [SYMBOL]` to bind assets to your dashboard.

---

## Security

- Never commit the `.env` file — it is already in `.gitignore`.
- Alert and preference data are stored locally and never transmitted to third parties.
- The `bot.lock` file prevents multiple simultaneous instances of the bot.

---

## License

Distributed under the [MIT License](LICENSE).

---

## Author

**Alyson** · [github.com/Alyson256](https://github.com/Alyson256)
