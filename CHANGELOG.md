# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
e este projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.2.1] - 2026-04-09

### Adicionado
- **Manual Dinâmico (`/explicar`)**: Adição de uma enciclopédia de comandos interna vinculada ao `MANUAL_COMANDOS` (modularizado do util.py) fornecendo exemplos práticos em caso de dúvidas dos usuários e reduzindo a poluição visual.

### Corrigido
- Restaurada a funcionalidade do botão `Modo Automático` no menu interativo primário (`/start`), mapeando novamente o escutador.
- Tratamento de retrocompatibilidade (`Retrocompatibility Patch`) introduzido no Motor Assíncrono (`main.py`) injetando dinamicamente a direção para evitar quedas em alertas salvos em versões legadas do banco de dados (KeyError).

---

## [2.2.0] "Hub Automation" - 2026-04-09

### Adicionado
- **Hub Automático Pessoal**: Criação de Painel Interativo (`/automatico`) via botões alinhados com preferências de cada usuário.
- **Persistência Individualizada**: Lógica de Memória dedicada `preferencias_usuarios.json` separada dos Alertas base.
- **Sincronismo Tempo Real**: Implementação do `Radar (90m)` em background loop adaptado ao limite do Telegram.
- **Jornal Inteligente (`UTC-3`)**: Motor programado para fusos horários (`datetime`), disparando Agregador Notícias + Moedas Favoritas no horário definido na UI.
- Comando de ancoragem universal flexível para radar próprio: `/automoeda [SIGLA]`.

### Refatorado
- Expurgada lógica de formatação JSON e Compiladores de String do `main.py` diretamente para as veias de `util.py` (Arquitetura Total Clean).
- UI padronizada sem excesso de Emojis, usando bolhas Minimalistas baseadas em variação (🟢 e 🔴).

---

## [2.1.1] - 2026-04-09

### Adicionado
- Escudo Global de Exceções (`ExceptionHandler`) focado em resiliência de rede contra conexões abortadas.
- Implementação completa do Motor de Alertas Assíncrono (`background thread`) com lógica *One-Shot*.

### Melhorado
- Comando `/cotar` repaginado com roteamento inteligente, adicionando total suporte a consultas universais (suportando Cripto e moedas Fiat na mesma função).
- Comando de criação de alertas refatorado com validação antecipada de Sigla/Ticker junto às sub-APIs e normalização de floatings Brasileiros (vírgula).

---

## [2.1.0] "Core Refactoring" - 2026-04-01

### Adicionado
- Integração de ambiente virtual estrito (`.venv`) e controle de segurança de variáveis sensíveis (`.env` e `.gitignore`).
- Separação de responsabilidades com novo dicionário de rotas dinâmico (`ENDPOINTS`).

### Melhorado
- Arquitetura do projeto modularizada de fato, dividida em múltiplos arquivos (`main.py`, `API.py`, `util.py`) para ganho de escalabilidade.
- Migração do motor de busca de criptomoedas para o endpoint público da Binance.

### Removido
- Arquivo monolítico legado de +400 linhas.
- Dependência de chaves de autenticação da CoinMarketCap para cotações básicas.

---

## [2.0.0] - 2026-03-26

### Adicionado
- Refatoração da base de código para um padrão profissional.
- Sistema de logging centralizado com arquivo `terminal_financeiro.log`.
- Docstrings em todas as funções.
- Suporte melhorado a tratamento de erros.
- Motor de alertas otimizado com timeouts.
- Menu de notícias dinâmico.

### Melhorado
- Performance do motor de alertas (verificação a cada 60s).
- Organização interna de funções e constantes no arquivo principal.
- Mensagens de erro mais descritivas.
- Tratamento de conexões instáveis melhorado.
- Sistema de gerenciamento de memória mais robusto.

### Corrigido
- Duplicação da função `menu_noticias()`.
- Prints de debug removidos em favor de logging.
- Erros de timeout nas requisições HTTP.
- Problema de múltiplos disparos de alertas.
- Issues com encoding em arquivos JSON.

### Removido
- Duplicações de código.
- Comentários antigos de debug.
- Prints não padronizados.

### Deploy
- Adicionadas boas práticas para GitHub.
- README.md completo com documentação.
- Requirements.txt com versões específicas.
- .gitignore (versão inicial).
- LICENSE (MIT).

---

## [1.5.7] - 2026-03-10

### Adicionado
- Sistema inicial de alertas.
- Suporte a 4 moedas Fiat (USD, EUR, GBP, JPY).
- Suporte a 4 criptomoedas (BTC, ETH, LTC, DOGE).
- Menu de notícias RSS.
- Modo automático com resumo de cotações.
- Sistema de persistência com JSON.

### Melhorado
- Interface com botões interativos.
- Formatação visual das variações.

### Corrigido
- Problemas iniciais de conexão.

---

## [1.0.0] - 2026-02-15

### Adicionado
- Primeiro lançamento.
- Consulta básica de cotações.
- Menu principal simples.