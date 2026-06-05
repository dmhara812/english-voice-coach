# English Voice Coach AI

Assistente de voz para praticar conversação em inglês com correção, feedback e continuidade de diálogo.

> Status: em desenvolvimento  
> Versão atual: estrutura inicial + captura de áudio local  
> Observação: este README é inicial. Na etapa final do projeto, ele será reescrito em uma versão mais apresentável, com português e inglês, pensando em portfólio.

---

## Objetivo do projeto

O **English Voice Coach AI** será uma aplicação em Python para ajudar estudantes brasileiros a praticarem inglês oralmente.

A ideia principal é simular uma conversa com um professor de inglês:

1. o usuário fala em inglês pelo microfone;
2. o sistema grava a fala;
3. a fala é transcrita com IA;
4. o coach corrige a frase;
5. o coach sugere uma forma mais natural de falar;
6. o coach responde em inglês;
7. o coach faz uma pergunta relacionada ao assunto;
8. o sistema transforma a resposta em áudio;
9. a conversa continua em ciclos.

---

## Decisão importante sobre a gravação

A gravação será controlada manualmente pelo usuário:

```text
Pressione Enter para começar a gravar.
Fale em inglês com calma.
Pressione Enter novamente quando terminar.
```

Essa decisão foi tomada porque o projeto é voltado para aprendizado. Durante uma conversa em inglês, o estudante pode precisar pausar para pensar, então o sistema não deve encerrar a gravação automaticamente a cada silêncio curto.

O detector de silêncio será usado apenas como apoio para identificar áudio vazio, muito baixo ou gravações sem fala útil.

---

## Funcionalidades planejadas

- Captura de áudio pelo microfone.
- Gravação manual com início e fim por Enter.
- Análise auxiliar de silêncio ou áudio vazio.
- Transcrição da fala com a API da OpenAI.
- Correção gramatical e sugestão de frase mais natural.
- Feedback curto em português brasileiro.
- Resposta conversacional em inglês.
- Perguntas de continuidade relacionadas ao assunto.
- Text-to-speech para o coach responder por voz.
- Histórico de conversas em SQLite.
- Interface no terminal com Rich.

---

## Stack principal

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

## Estrutura inicial do projeto

```text
english-voice-coach/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── recorder.py
│   │   ├── player.py
│   │   └── silence_detector.py
│   ├── ai/
│   │   ├── transcriber.py
│   │   ├── coach.py
│   │   └── speaker.py
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

---

## Configuração inicial

Criar o ambiente virtual:

```powershell
python -m venv .venv
```

Ativar o ambiente virtual no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar dependências:

```powershell
pip install -r requirements.txt
```

Criar o arquivo local de variáveis de ambiente:

```powershell
copy .env.example .env
```

Editar o `.env` e preencher a chave da OpenAI:

```env
OPENAI_API_KEY=sua_chave_real_aqui
```

Nunca envie o arquivo `.env` para o GitHub.

---

## Como validar a etapa atual

Executar o arquivo inicial:

```powershell
python run.py
```

Validar lint e formatação:

```powershell
ruff check .
ruff format . --check
```

Testar gravação manual pelo terminal:

```powershell
python -c "from pathlib import Path; from app.audio.recorder import record_until_enter; print(record_until_enter(Path('data/audio'), 16000))"
```

Testar análise de silêncio substituindo o caminho pelo arquivo gravado:

```powershell
python -c "from pathlib import Path; from app.audio.silence_detector import analyze_audio_file; print(analyze_audio_file(Path('data/audio/seu-arquivo.wav')))"
```

Testar reprodução substituindo o caminho pelo arquivo gravado:

```powershell
python -c "from pathlib import Path; from app.audio.player import play_audio_file; play_audio_file(Path('data/audio/seu-arquivo.wav'))"
```

---

## Roadmap das etapas

- [x] Etapa 1 — Planejamento
- [x] Etapa 2 — Configuração do ambiente
- [x] Etapa 3 — Captura de áudio
- [ ] Etapa 4 — Transcrição
- [ ] Etapa 5 — Coach AI
- [ ] Etapa 6 — Text-to-speech e reprodução
- [ ] Etapa 7 — Storage com SQLite
- [ ] Etapa 8 — UI no terminal
- [ ] Etapa 9 — Integração principal
- [ ] Etapa 10 — Testes e Ruff
- [ ] Etapa 11 — README final bilíngue para portfólio

---

## Observação para portfólio

Este projeto será organizado para demonstrar:

- arquitetura modular em Python;
- integração com APIs de IA;
- manipulação de áudio local;
- tratamento explícito de erros;
- validação de dados com Pydantic;
- persistência com SQLite;
- documentação incremental;
- boas práticas com Ruff e Conventional Commits.