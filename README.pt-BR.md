# English Voice Coach AI

Assistente de conversação em inglês com entrada por voz, correção com IA e histórico em SQLite.

[Read in English](README.en.md) · [Voltar ao seletor de idioma](README.md)

---

## Sobre o projeto

**English Voice Coach AI** é um projeto em Python para praticar conversação em inglês usando o microfone do computador.

A ideia principal é simples: você fala em inglês, o sistema transcreve sua fala, um coach de IA corrige a frase, sugere formas mais naturais de falar e continua a conversa com uma nova pergunta em inglês.

O MVP foi desenhado para ser útil, barato de rodar e bom para portfólio. Por isso, a IA responde em texto no terminal em vez de falar por áudio. A prática continua sendo oral, porque o usuário responde falando no microfone.

---

## Fluxo do MVP

```text
Usuário fala pelo microfone
↓
Gravação manual controlada por Enter
↓
Transcrição do áudio com OpenAI
↓
Coach AI corrige a fala
↓
Coach mostra sugestões e resposta em texto
↓
Coach faz uma pergunta relacionada ao assunto
↓
Rodada é salva no SQLite
↓
Usuário responde falando novamente
```

---

## Principais decisões de produto

### 1. Gravação manual por Enter

O sistema não encerra a gravação automaticamente após poucos segundos de silêncio. Isso foi decidido porque estudantes de inglês precisam de tempo para pensar antes de terminar a resposta.

O fluxo recomendado é:

```text
Pressione Enter para começar a gravar.
Fale com calma.
Pressione Enter novamente para encerrar.
```

### 2. Sem TTS obrigatório no MVP

O projeto não usa voz da IA como requisito principal. A resposta do professor aparece em texto no terminal.

Essa decisão reduz custo, remove complexidade de reprodução de áudio e mantém o foco no objetivo principal: praticar fala em inglês com correção e continuidade de conversa.

### 3. Conversas separadas por sessão

Cada execução do app cria uma nova sessão de conversa.

```text
Hoje: python run.py → sessão 1
Amanhã: python run.py → sessão 2
```

O histórico antigo continua salvo no banco, mas o contexto enviado ao coach usa apenas a sessão atual. Assim, uma conversa nova não fica misturada com assuntos de dias anteriores.

### 4. Uma pergunta final por rodada

A interface mostra a resposta do professor e a pergunta de continuação no mesmo bloco. O coach deve evitar criar uma pergunta dentro da resposta principal e outra pergunta separada.

O formato esperado é:

```text
Teacher response:
Programming sounds like a great way to spend your time.

What kind of software do you like to create?
```

---

## Funcionalidades

- Captura de áudio pelo microfone.
- Gravação manual com início e fim controlados pelo usuário.
- Transcrição do áudio usando a API da OpenAI.
- Correção gramatical e melhoria de naturalidade.
- Sugestões de frases alternativas.
- Resposta conversacional em inglês.
- Pergunta final para estimular o usuário a continuar falando.
- Validação da resposta da IA com Pydantic.
- Interface de terminal com Rich.
- Histórico persistente em SQLite.
- Separação de conversas por sessão.
- Padronização de lint e formatação com Ruff.
- Testes automatizados com `unittest`.

---

## Stack utilizada

- Python 3.11+
- OpenAI API
- python-dotenv
- sounddevice
- soundfile
- numpy
- Pydantic
- Rich
- SQLite
- Ruff
- unittest

---

## Arquitetura

```text
english-voice-coach/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── audio/
│   │   ├── recorder.py
│   │   ├── player.py
│   │   └── silence_detector.py
│   ├── ai/
│   │   ├── transcriber.py
│   │   └── coach.py
│   ├── storage/
│   │   ├── database.py
│   │   └── repository.py
│   ├── ui/
│   │   └── terminal_ui.py
│   └── prompts/
│       └── english_coach_prompt.py
├── data/
│   └── audio/
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
├── README.pt-BR.md
├── README.en.md
└── run.py
```

---

## Como instalar

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/english-voice-coach.git
cd english-voice-coach
```

### 2. Criar e ativar o ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Depois edite o `.env` e informe sua chave da OpenAI:

```env
OPENAI_API_KEY=sua_chave_aqui
APP_LANGUAGE=pt-BR
COACH_LEVEL=intermediate
SAMPLE_RATE=16000
SILENCE_THRESHOLD=0.01
SILENCE_DURATION_MS=1500
DB_PATH=data/conversations.db
AUDIO_TEMP_DIR=data/audio
RECORDING_MODE=manual
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
COACH_MODEL=gpt-4.1-mini
ENABLE_TTS=false
```

> Nunca envie o arquivo `.env` para o GitHub. Use apenas `.env.example` no repositório.

---

## Como rodar

```bash
python run.py
```

Fluxo esperado:

```text
1. O app cria uma nova sessão.
2. Você pressiona Enter para começar a gravar.
3. Você fala em inglês.
4. Você pressiona Enter novamente para parar.
5. O áudio é transcrito.
6. O coach corrige e responde em texto.
7. A rodada é salva no banco.
8. Você responde a próxima pergunta falando novamente.
```

Para sair:

```text
exit
```

---

## Como validar o banco SQLite

Inicializar banco:

```powershell
python -c "from app.storage.database import initialize_database; initialize_database(); print('Banco inicializado com sucesso.')"
```

Verificar tabelas no PowerShell:

```powershell
python -c "import sqlite3; con = sqlite3.connect('data/conversations.db'); print(con.execute('SELECT name FROM sqlite_master WHERE type = ?', ('table',)).fetchall()); con.close()"
```

Resultado esperado:

```text
[('conversation_sessions',), ('conversations',)]
```

---

## Testes

Rodar todos os testes:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Ruff

Verificar lint:

```bash
ruff check .
```

Corrigir automaticamente o que for possível:

```bash
ruff check . --fix
```

Formatar código:

```bash
ruff format .
```

Verificar formatação sem alterar arquivos:

```bash
ruff format . --check
```

---

## Roadmap

- Adicionar modo opcional de TTS.
- Criar resumo automático por sessão.
- Adicionar estatísticas de evolução do usuário.
- Permitir níveis diferentes de exigência do coach.
- Exportar histórico para Markdown ou CSV.
- Criar interface web no futuro.

---

## Valor para portfólio

Este projeto demonstra conhecimentos em:

- integração com APIs de IA;
- processamento de áudio;
- arquitetura modular em Python;
- validação de dados com Pydantic;
- persistência com SQLite;
- interface de terminal com Rich;
- boas práticas com Ruff;
- documentação técnica incremental;
- decisões de produto baseadas em custo, usabilidade e manutenção.

---

## Licença

Este projeto pode ser usado como base de estudo e portfólio. Defina uma licença formal antes de publicar em produção.
