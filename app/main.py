"""Integração principal do English Voice Coach AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.ai.coach import CoachError, generate_coach_feedback
from app.ai.transcriber import TranscriptionError, transcribe_audio_file
from app.audio.recorder import AudioRecordingError, record_until_enter
from app.config import AppSettings, ConfigError, get_settings
from app.storage.database import DatabaseError, initialize_database
from app.storage.repository import (
    build_context_from_recent_conversations,
    count_conversations_in_session,
    create_conversation_session,
    finish_conversation_session,
    save_conversation,
)
from app.ui.terminal_ui import (
    ask_next_action,
    show_app_header,
    show_coach_response,
    show_error,
    show_recording_finished,
    show_recording_instructions,
    show_recording_started,
    show_session_finished,
    show_session_started,
    show_success,
    show_transcription,
    show_warning,
)

SESSION_TITLE: Final = "Prática de conversação em inglês"
EXIT_SUCCESS: Final = 0
EXIT_ERROR: Final = 1


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Agrupa objetos usados durante a execução do app.

    Essa estrutura evita passar muitos parâmetros soltos entre funções e deixa
    claro quais dados representam a sessão atual do usuário.
    """

    settings: AppSettings
    session_id: int


def main() -> int:
    """Executa o fluxo completo do English Voice Coach AI.

    Cada chamada de `python run.py` cria uma nova sessão de conversa. Isso evita
    misturar o contexto de hoje com o contexto de outro dia, mas mantém tudo
    salvo no SQLite para histórico e evolução futura.
    """

    show_app_header()

    try:
        runtime_context = _prepare_runtime_context()
    except ConfigError as exc:
        show_error(
            str(exc),
            suggestion="Confira o arquivo .env e confirme se OPENAI_API_KEY foi preenchida.",
        )
        return EXIT_ERROR
    except DatabaseError as exc:
        show_error(
            str(exc),
            suggestion="Confira se a pasta data/ pode ser criada e se o arquivo do banco não está bloqueado.",
        )
        return EXIT_ERROR

    show_session_started(runtime_context.session_id)
    show_recording_instructions()

    try:
        _run_conversation_loop(runtime_context)
    except KeyboardInterrupt:
        show_warning("Sessão interrompida pelo usuário.")
    finally:
        _finish_runtime_context(runtime_context)

    return EXIT_SUCCESS


def _prepare_runtime_context() -> RuntimeContext:
    """Carrega configuração, prepara o banco e cria uma nova sessão."""

    settings = get_settings(require_openai_key=True)
    initialize_database(settings=settings)
    session_id = create_conversation_session(
        title=SESSION_TITLE,
        settings=settings,
    )

    return RuntimeContext(settings=settings, session_id=session_id)


def _run_conversation_loop(runtime_context: RuntimeContext) -> None:
    """Mantém o ciclo de prática até o usuário decidir sair."""

    while True:
        action = ask_next_action()

        if action == "exit":
            break

        _run_single_turn(runtime_context)


def _run_single_turn(runtime_context: RuntimeContext) -> None:
    """Executa uma rodada: gravação, transcrição, coach, UI e banco.

    Os erros de uma rodada são tratados aqui para que o aplicativo continue
    aberto. Isso é importante no uso real: uma gravação curta ou uma falha de
    rede não deve encerrar toda a sessão de estudo.
    """

    try:
        show_recording_started()
        audio_file = record_until_enter(
            runtime_context.settings.audio_temp_dir,
            runtime_context.settings.sample_rate,
        )
        show_recording_finished(str(audio_file))

        transcription = transcribe_audio_file(
            audio_file,
            settings=runtime_context.settings,
        )
        show_transcription(transcription)

        conversation_history = build_context_from_recent_conversations(
            session_id=runtime_context.session_id,
            limit=runtime_context.settings.conversation_context_limit,
            settings=runtime_context.settings,
        )
        coach_response = generate_coach_feedback(
            transcription,
            conversation_history=conversation_history,
            settings=runtime_context.settings,
        )

        show_coach_response(coach_response)
        save_conversation(
            user_transcription=transcription,
            coach_response=coach_response,
            session_id=runtime_context.session_id,
            audio_file=audio_file,
            settings=runtime_context.settings,
        )
        show_success("Rodada salva no histórico da sessão atual.")
    except AudioRecordingError as exc:
        show_error(
            str(exc),
            suggestion="Teste o microfone, fale por mais tempo ou tente gravar novamente.",
        )
    except TranscriptionError as exc:
        show_error(
            str(exc),
            suggestion="Confira sua conexão, sua cota da OpenAI e se o áudio não ficou vazio.",
        )
    except CoachError as exc:
        show_error(
            str(exc),
            suggestion="Tente uma frase menor ou confira o modelo configurado em COACH_MODEL.",
        )
    except DatabaseError as exc:
        show_error(
            str(exc),
            suggestion="A rodada foi processada, mas não pôde ser salva no SQLite.",
        )


def _finish_runtime_context(runtime_context: RuntimeContext) -> None:
    """Finaliza a sessão atual e mostra um resumo simples."""

    try:
        finish_conversation_session(
            runtime_context.session_id,
            settings=runtime_context.settings,
        )
        total_turns = count_conversations_in_session(
            runtime_context.session_id,
            settings=runtime_context.settings,
        )
    except DatabaseError as exc:
        show_warning(f"Não foi possível finalizar a sessão no banco: {exc}")
        return

    show_session_finished(runtime_context.session_id, total_turns)
