# English Voice Coach AI

Assistente em Python para praticar conversação em inglês com fala pelo microfone, transcrição com IA, correção estruturada, resposta textual e histórico local em SQLite.

> Status: em desenvolvimento  
> Versão atual: captura de áudio local + transcrição + coach textual com JSON validado + histórico SQLite  
> Decisão de MVP: sem TTS obrigatório  
> Observação: este README é inicial. Na etapa final, ele será reescrito em uma versão mais apresentável, em português e inglês, pensando em portfólio.

---

## Objetivo do projeto

O **English Voice Coach AI** será uma aplicação em Python para ajudar estudantes brasileiros a praticarem inglês oralmente.

A ideia principal é simular uma conversa com um professor de inglês:

1. o usuário fala em inglês pelo microfone;
2. o sistema grava a fala manualmente por Enter;
3. a fala é transcrita com a API da OpenAI;
4. o coach corrige a frase;
5. o coach mostra uma versão mais natural;
6. o coach sugere formas melhores de continuar a resposta;
7. o coach responde em inglês por texto;
8. o coach faz uma pergunta relacionada ao assunto;
9. a rodada é salva no SQLite;
10. a conversa continua em ciclos.

---

## Fluxo do MVP

```text
você fala pelo microfone
↓
o sistema grava sua fala
↓
o áudio é transcrito
↓
o coach corrige sua frase
↓
o coach mostra sugestões de melhoria
↓
o coach responde em inglês por texto
↓
o coach faz uma pergunta relacionada
↓
a rodada é salva no histórico SQLite
↓
você responde falando novamente
```

---

## Decisão de MVP: sem TTS obrigatório

O MVP **não terá resposta em áudio da IA**.

Essa decisão foi tomada por três motivos principais:

- reduz custo, porque elimina chamadas de text-to-speech;
- simplifica o desenvolvimento, evitando player de áudio, arquivo temporário de voz e problemas de reprodução no Windows;
- mantém o foco principal do projeto: praticar fala em inglês com correção e continuidade de conversa.

O TTS continua sendo uma ideia válida, mas fica fora do MVP inicial. Ele poderá ser implementado futuramente como recurso opcional.

Configuração atual:

```env
ENABLE_TTS=false
```

---

## Como o coach deve responder

A resposta textual deve seguir a ideia de uma aula curta de conversação:

```text
Correction:
...

A more natural way to say it:
...

You could also say:
1. ...
2. ...

My answer:
...

Question:
...
```

O objetivo não é apenas corrigir. O coach também deve estimular o usuário a continuar falando em inglês, sempre com uma pergunta relacionada ao assunto.

---

## Decisão importante sobre a gravação

A gravação principal será manual:

```text
Enter para começar → falar com calma → Enter para parar
```

Essa decisão foi tomada porque o estudante pode precisar de pausas para pensar em inglês. Portanto, o sistema **não deve encerrar a gravação automaticamente só porque houve silêncio curto**.

O detector de silêncio continuará existindo apenas como apoio para identificar áudio vazio, microfone baixo ou gravações sem fala útil.

---

## Histórico local com SQLite

O projeto salva cada rodada da conversa em um banco local SQLite:

```text
data/conversations.db
```

Cada registro guarda:

- caminho do áudio gravado;
- transcrição do usuário;
- frase corrigida;
- versão mais natural;
- sugestões de resposta;
- erros identificados;
- notas de gramática, naturalidade e vocabulário;
- feedback em português;
- resposta do coach em inglês;
- pergunta de continuação.

O banco local **não deve ser versionado no GitHub**.

---

## Funcionalidades planejadas no MVP

- Captura de áudio pelo microfone.
- Gravação manual por Enter.
- Validação de áudio vazio ou silencioso.
- Transcrição de fala usando a API da OpenAI.
- Correção gramatical e sugestões de fala natural.
- Sugestões de respostas possíveis em inglês.
- Continuação da conversa com perguntas relacionadas ao assunto.
- Resposta textual no terminal.
- Histórico de conversas em SQLite.
- Interface de terminal com Rich.

---

## Funcionalidades fora do MVP inicial

- Resposta em áudio usando TTS.
- Modo de conversa em tempo real.
- Interface gráfica.
- Dashboard de evolução.
- Métricas mais avançadas de progresso.

Essas ideias continuam válidas, mas serão tratadas como melhorias futuras.

---

## Funcionalidades implementadas até agora

- Estrutura inicial do projeto.
- Configuração de ambiente com `.env.example`.
- Configuração do Ruff para lint e formatação.
- Captura de áudio local em `.wav`.
- Reprodução local de arquivos `.wav` apenas para teste de áudio.
- Detector auxiliar de áudio silencioso.
- Configuração central em `app/config.py`.
- Transcrição de áudio em `app/ai/transcriber.py` usando OpenAI.
- Tratamento mais claro para erro de cota/créditos da OpenAI.
- Prompt do professor em `app/prompts/english_coach_prompt.py`.
- Coach textual em `app/ai/coach.py` com validação Pydantic.
- Decisão arquitetural formal: TTS fora do MVP obrigatório.
- Banco SQLite inicializado em `app/storage/database.py`.
- Repositório de conversas em `app/storage/repository.py`.
- Salvamento e leitura de histórico recente para contexto do coach.
- README inicial do projeto.

---

## Stack

- Python 3.11+
- OpenAI API
- python-dotenv
- sounddevice
- soundfile
- numpy
- pydantic
- rich
- SQLite
- Ruff

---

## Estrutura planejada

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
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
└── run.py
```

> Observação: `app/audio/player.py` pode continuar existindo como utilitário de teste local para arquivos `.wav`, mas não faz parte do fluxo principal do MVP. `app/ai/speaker.py` não será criado agora.

---

## Como rodar neste momento

Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
pip install -r requirements.txt
```

Crie o arquivo `.env`:

```powershell
Copy-Item .env.example .env
```

Depois, edite o `.env` e preencha sua chave real:

```env
OPENAI_API_KEY=sk-...
```

---

## Configuração recomendada para economizar

```env
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
COACH_MODEL=gpt-4.1-mini
ENABLE_TTS=false
```