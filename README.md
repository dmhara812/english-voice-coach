# English Voice Coach AI

Assistente em Python para praticar conversação em inglês com fala pelo microfone, transcrição com IA, correção estruturada e continuação da conversa em texto.

> Status: em desenvolvimento  
> Versão atual: captura de áudio local + transcrição + coach textual com JSON validado  
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
9. a conversa continua em ciclos.

---

## Decisão de MVP: sem TTS obrigatório

O MVP **não terá resposta em áudio da IA**.

O fluxo principal será:

```text
você fala pelo microfone
↓
o sistema transcreve
↓
o coach corrige sua fala
↓
mostra sugestões de melhoria
↓
responde em inglês por texto
↓
faz uma nova pergunta em inglês para você continuar falando
```

Essa decisão reduz custo, simplifica o desenvolvimento e mantém o foco principal do projeto: praticar fala em inglês com correção e continuidade de conversa.

O TTS pode ser implementado futuramente como recurso opcional, controlado por:

```env
ENABLE_TTS=false
```

---

## Decisão importante sobre a gravação

A gravação principal será manual:

```text
Enter para começar → falar com calma → Enter para parar
```

Essa decisão foi tomada porque o estudante pode precisar de pausas para pensar em inglês. Portanto, o sistema **não deve encerrar a gravação automaticamente só porque houve silêncio curto**.

O detector de silêncio continuará existindo apenas como apoio para identificar áudio vazio, microfone baixo ou gravações sem fala útil.

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

> Observação: `speaker.py` e TTS ficam fora do MVP inicial. Se forem adicionados no futuro, entrarão como recurso opcional.

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

> Não coloque sua chave da OpenAI no GitHub.

---

## Configuração recomendada para economizar

```env
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
COACH_MODEL=gpt-4.1-mini
ENABLE_TTS=false