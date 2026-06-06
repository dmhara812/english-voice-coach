"""Interface de terminal do English Voice Coach usando Rich."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final, Literal

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from app.ai.coach import CoachResponse

UserAction = Literal["continue", "exit"]
APP_TITLE: Final = "English Voice Coach AI"

console = Console()


def show_app_header() -> None:
    """Mostra o cabeçalho principal da aplicação."""

    title = Text(APP_TITLE, style="bold cyan")
    subtitle = Text(
        "Practice speaking English with corrections, suggestions and follow-up questions.",
        style="white",
    )
    console.print(Panel.fit(Text.assemble(title, "\n", subtitle), box=box.ROUNDED))


def show_session_started(session_id: int) -> None:
    """Informa que uma nova sessão de estudo começou."""

    console.print(
        Panel(
            f"Sessão atual: [bold]{session_id}[/bold]\n"
            "O contexto desta conversa ficará separado das sessões antigas.",
            title="Nova sessão",
            border_style="green",
        )
    )


def show_recording_instructions() -> None:
    """Explica o fluxo manual de gravação antes da primeira rodada."""

    console.print(
        Panel(
            "1. Pressione [bold]Enter[/bold] para começar a gravar.\n"
            "2. Fale em inglês com calma. Você pode pausar para pensar.\n"
            "3. Pressione [bold]Enter[/bold] novamente para parar.\n"
            "4. Digite [bold]exit[/bold] quando quiser encerrar.",
            title="Como praticar",
            border_style="blue",
        )
    )


def ask_next_action() -> UserAction:
    """Pergunta se o usuário quer continuar ou sair."""

    answer = Prompt.ask(
        "\nPressione Enter para gravar outra resposta ou digite [bold]exit[/bold]",
        default="",
        show_default=False,
    )

    if answer.strip().lower() == "exit":
        return "exit"

    return "continue"


def wait_for_enter(message: str) -> None:
    """Pausa o terminal até o usuário pressionar Enter."""

    console.input(f"[bold cyan]{message}[/bold cyan]")


def show_recording_started() -> None:
    """Mostra feedback visual de início da gravação."""

    console.print("[bold red]Gravando...[/bold red] fale em inglês agora.")


def show_recording_finished(audio_file: str) -> None:
    """Mostra o caminho do áudio salvo."""

    console.print(
        f"[green]Gravação finalizada.[/green] Arquivo: [dim]{audio_file}[/dim]"
    )


def show_transcription(transcription: str) -> None:
    """Mostra a transcrição antes da correção do coach."""

    console.print(
        Panel(
            transcription,
            title="Sua fala transcrita",
            border_style="magenta",
        )
    )


def show_coach_response(response: CoachResponse) -> None:
    """Exibe a resposta validada do coach em blocos fáceis de ler."""

    console.print(Rule("Correção do professor"))
    _show_sentence_block(response)
    _show_suggestions(response.suggested_answers_en)
    _show_mistakes(response)
    _show_scores(response)
    _show_conversation_continuation(response)


def show_success(message: str) -> None:
    """Mostra uma mensagem curta de sucesso."""

    console.print(f"[green]✓[/green] {message}")


def show_warning(message: str) -> None:
    """Mostra um aviso sem interromper o programa."""

    console.print(f"[yellow]Atenção:[/yellow] {message}")


def show_error(message: str, *, suggestion: str | None = None) -> None:
    """Mostra erros de forma amigável para o usuário."""

    body = f"[red]{message}[/red]"

    if suggestion:
        body = f"{body}\n\nSugestão: {suggestion}"

    console.print(Panel(body, title="Erro", border_style="red"))


def show_session_finished(session_id: int, total_turns: int) -> None:
    """Mostra resumo simples ao encerrar a sessão."""

    console.print(
        Panel(
            f"Sessão {session_id} encerrada.\n"
            f"Rodadas salvas nesta sessão: [bold]{total_turns}[/bold].",
            title="Até a próxima prática",
            border_style="green",
        )
    )


def show_recent_sessions(sessions: Sequence[Any]) -> None:
    """Exibe sessões recentes sem acoplar a UI ao repositório.

    A função recebe objetos com atributos `id`, `started_at`, `ended_at` e
    `title`. Isso permite usar `ConversationSessionRecord` sem importar a camada
    de storage dentro da UI.
    """

    if not sessions:
        show_warning("Nenhuma sessão anterior foi encontrada.")
        return

    table = Table(title="Sessões recentes", box=box.SIMPLE_HEAVY)
    table.add_column("ID", justify="right")
    table.add_column("Início")
    table.add_column("Fim")
    table.add_column("Título")

    for session in sessions:
        table.add_row(
            str(getattr(session, "id", "")),
            str(getattr(session, "started_at", "")),
            str(getattr(session, "ended_at", "") or "em aberto"),
            str(getattr(session, "title", "") or "sem título"),
        )

    console.print(table)


def _show_sentence_block(response: CoachResponse) -> None:
    """Mostra frase original, correção e versão natural."""

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Item", style="cyan", no_wrap=True)
    table.add_column("Texto")

    table.add_row("Original", response.original_sentence)
    table.add_row("Correction", response.corrected_sentence)
    table.add_row("Natural", response.natural_sentence)

    console.print(table)


def _show_suggestions(suggestions: list[str]) -> None:
    """Mostra frases que o usuário pode usar para continuar falando."""

    suggestion_text = "\n".join(
        f"{index}. {suggestion}"
        for index, suggestion in enumerate(suggestions, start=1)
    )
    console.print(
        Panel(
            suggestion_text,
            title="You could also say",
            border_style="cyan",
        )
    )


def _show_mistakes(response: CoachResponse) -> None:
    """Mostra pontos de melhoria encontrados pelo coach."""

    if not response.mistakes:
        console.print(
            Panel(
                "Nenhum erro importante encontrado. Continue praticando!",
                title="Mistakes",
                border_style="green",
            )
        )
        return

    table = Table(title="Mistakes", box=box.ROUNDED)
    table.add_column("Tipo", style="yellow", no_wrap=True)
    table.add_column("Explicação")
    table.add_column("Exemplo")

    for mistake in response.mistakes:
        table.add_row(mistake.type, mistake.explanation, mistake.example)

    console.print(table)


def _show_scores(response: CoachResponse) -> None:
    """Mostra pontuações simples para acompanhamento."""

    score_table = Table(title="Score", box=box.SIMPLE_HEAVY)
    score_table.add_column("Grammar", justify="center")
    score_table.add_column("Naturalness", justify="center")
    score_table.add_column("Vocabulary", justify="center")

    score_table.add_row(
        str(response.score.grammar),
        str(response.score.naturalness),
        str(response.score.vocabulary),
    )

    console.print(score_table)


def _show_conversation_continuation(response: CoachResponse) -> None:
    """Mostra feedback e continuação em formato de conversa única."""

    console.print(
        Panel(
            response.coach_feedback_ptbr,
            title="Feedback rápido",
            border_style="yellow",
        )
    )
    console.print(
        Panel(
            _build_teacher_message(response),
            title="Teacher response",
            border_style="green",
        )
    )


def _build_teacher_message(response: CoachResponse) -> str:
    """Une resposta e pergunta final como uma fala única do professor.

    O JSON continua separado porque isso ajuda o banco e o contexto da próxima
    rodada. Na tela, porém, a experiência deve parecer uma conversa natural.

    Se o modelo desobedecer o prompt e já colocar uma pergunta em `ai_response_en`,
    mostramos apenas esse texto para evitar duas perguntas consecutivas. Isso
    protege a experiência do usuário sem quebrar a execução da sessão.
    """

    answer = response.ai_response_en.strip()
    question = response.follow_up_question_en.strip()

    if not question:
        return answer

    if _looks_like_question(answer):
        return answer

    return f"{answer}\n\n[bold]{question}[/bold]"


def _looks_like_question(text: str) -> bool:
    """Detecta se o texto já termina como pergunta.

    A verificação é simples de propósito. Ela não tenta fazer análise linguística;
    serve apenas para evitar o problema visual de duas perguntas no terminal.
    """

    return text.rstrip().endswith("?")
