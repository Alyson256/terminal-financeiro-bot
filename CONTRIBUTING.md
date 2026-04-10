# Contribuindo para o Terminal Financeiro

Obrigado pelo interesse em contribuir! Este documento descreve como participar do projeto de forma organizada.

---

## Como Contribuir

### Reportar Bugs

Abra uma [Issue](https://github.com/AlysonRN/terminal-financeiro/issues) com as seguintes informações:

- **Título claro** — descreva o problema em uma linha
- **Passos para reproduzir** — comando enviado, comportamento esperado vs. atual
- **Ambiente** — sistema operacional e versão do Python
- **Log relevante** — trecho de `terminal_financeiro.log` se aplicável

### Sugerir Melhorias

Abra uma Issue com a tag `enhancement` descrevendo:
- O que gostaria de adicionar e por quê
- Como a funcionalidade se encaixaria na arquitetura atual (`main` → `util` → `API`)

### Enviar Pull Requests

1. Faça um **fork** do repositório
2. Crie uma branch descritiva:
   ```bash
   git checkout -b feat/nome-da-feature
   ```
3. Implemente suas mudanças respeitando a arquitetura modular do projeto
4. Faça commit seguindo o padrão abaixo
5. Abra um **Pull Request** com descrição clara do que foi alterado e por quê

---

## Padrão de Commits

Use prefixos semânticos:

| Prefixo | Uso |
|---------|-----|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `refactor:` | Refatoração sem mudança de comportamento |
| `docs:` | Documentação |
| `chore:` | Manutenção (dependências, configs) |

Exemplos:
```
feat: adicionar suporte a moeda PEPE via AwesomeAPI
fix: corrigir KeyError em alertas sem campo direcao
refactor: mover compilar_jornal para util.py
docs: atualizar README com novos comandos do Hub
```

---

## Padrões de Código

- Siga [PEP 8](https://peps.python.org/pep-0008/)
- Adicione **docstring** em funções novas
- Use **type hints** quando possível
- Mantenha linhas com no máximo 100 caracteres
- Respeite a separação de camadas: lógica de API fica em `API.py`, utilitários em `util.py`, roteamento em `main.py`

### Exemplo de função bem documentada
```python
def buscar_preco_binance(simbolo: str) -> float | None:
    """
    Busca o preço de um par na Binance.

    Args:
        simbolo: Par de negociação. Ex: 'BTCBRL'

    Returns:
        Preço como float ou None se indisponível.
    """
```

### Adicionar uma nova fonte de notícias

Basta inserir uma entrada no dicionário `FONTES_NOTICIAS` em `util.py`:
```python
"sua_fonte": {
    "nome": "Nome Exibido",
    "url": "https://seu-feed.com/rss"
}
```
Nenhuma outra alteração é necessária — o bot detecta e exibe automaticamente.

---

## Testando Antes de Enviar

```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar sintaxe
python -m py_compile main.py
python -m py_compile API.py
python -m py_compile util.py

# Executar localmente
python main.py
```

---

## Roadmap (Contribuições Bem-Vindas)

- [ ] Substituir JSON por SQLite para persistência escalável
- [ ] Live ticker via `edit_message_text` no Radar (evitar flood de mensagens)
- [ ] Suporte ao Discord (`main_discord.py` consumindo o mesmo `API.py` e `util.py`)
- [ ] Gráficos de variação de preço (matplotlib ou plotly)
- [ ] Testes automatizados com pytest
- [ ] Suporte a Docker para deploy simplificado

---

## Dúvidas

Abra uma [Discussion](https://github.com/AlysonRN/terminal-financeiro/discussions) ou uma [Issue](https://github.com/AlysonRN/terminal-financeiro/issues).
