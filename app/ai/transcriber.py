"""Transcrição de áudio usando a API da OpenAI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from app.audio.silence_detector import SilenceDetectionError, analyze_audio_file
from app.config import AppSettings, ConfigError, get_settings

SUPPORTED_AUDIO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".ogg", ".wav", ".webm"}
)
MIN_AUDIO_FILE_SIZE_BYTES: Final = 1024
MIN_AUDIO_DURATION_SECONDS: Final = 0.3
DEFAULT_TRANSCRIPTION_PROMPT: Final = (
    "The speaker is a Portuguese-speaking English learner practicing conversation. "
    "They may speak slowly, pause to think, and use beginner or intermediate English. "
    "Transcribe the user's spoken English as clearly as possible."
)


class TranscriptionError(RuntimeError):
    """Erro específico para falhas durante a transcrição de áudio."""


def validate_audio_file(audio_file_path: Path, settings: AppSettings) -> None:
    """Valida se o arquivo de áudio pode ser enviado para transcrição.

    A validação local evita gastar chamada de API com arquivo inexistente, vazio,
    silencioso ou em formato não aceito. Ela também produz mensagens mais úteis
    para o usuário do que um erro genérico vindo da API.
    """

    if not audio_file_path.exists():
        msg = f"Arquivo de áudio não encontrado: {audio_file_path}"
        raise TranscriptionError(msg)

    if not audio_file_path.is_file():
        msg = f"O caminho informado não é um arquivo de áudio: {audio_file_path}"
        raise TranscriptionError(msg)

    if audio_file_path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
        supported_formats = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
        msg = (
            f"Formato de áudio não suportado: {audio_file_path.suffix}. "
            f"Use um destes formatos: {supported_formats}."
        )
        raise TranscriptionError(msg)

    if audio_file_path.stat().st_size < MIN_AUDIO_FILE_SIZE_BYTES:
        msg = "O arquivo de áudio parece vazio ou curto demais para transcrição."
        raise TranscriptionError(msg)

    try:
        analysis = analyze_audio_file(
            audio_file_path,
            silence_threshold=settings.silence_threshold,
        )
    except SilenceDetectionError as exc:
        msg = "Não foi possível validar o volume do áudio antes da transcrição."
        raise TranscriptionError(msg) from exc

    if analysis.duration_seconds < MIN_AUDIO_DURATION_SECONDS:
        msg = "A gravação ficou curta demais. Grave uma frase um pouco maior."
        raise TranscriptionError(msg)

    if analysis.is_probably_silent:
        msg = (
            "O áudio parece silencioso ou com volume muito baixo. "
            "Verifique o microfone e tente falar um pouco mais perto dele."
        )
        raise TranscriptionError(msg)


def _extract_openai_error_code(exc: APIStatusError) -> str:
    """Extrai o código interno da OpenAI quando a resposta trouxer esse campo."""

    body = getattr(exc, "body", None)

    if not isinstance(body, dict):
        return ""

    error = body.get("error")

    if not isinstance(error, dict):
        return ""

    return str(error.get("code") or "")


def _extract_transcription_text(response: Any) -> str:
    """Extrai o texto da resposta da OpenAI de forma defensiva."""

    if isinstance(response, str):
        transcription_text = response
    else:
        transcription_text = str(getattr(response, "text", ""))

    transcription_text = transcription_text.strip()

    if not transcription_text:
        msg = "A transcrição voltou vazia. Tente gravar novamente com mais volume."
        raise TranscriptionError(msg)

    return transcription_text


def transcribe_audio_file(
    audio_file_path: Path,
    *,
    settings: AppSettings | None = None,
) -> str:
    """Transcreve um arquivo de áudio local usando a OpenAI.

    O arquivo já deve ter sido gravado pelo módulo `app.audio.recorder`. Esta
    função não captura microfone; ela apenas recebe o arquivo final, valida e
    envia para o endpoint de transcrição.
    """

    active_settings = settings or get_settings(require_openai_key=True)
    validate_audio_file(audio_file_path, active_settings)

    client = OpenAI(api_key=active_settings.openai_api_key)

    try:
        with audio_file_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=active_settings.transcription_model,
                file=audio_file,
                language=active_settings.transcription_language,
                prompt=DEFAULT_TRANSCRIPTION_PROMPT,
            )
    except ConfigError:
        raise
    except AuthenticationError as exc:
        msg = "A OpenAI recusou a chave de API. Verifique o valor de OPENAI_API_KEY no arquivo .env."
        raise TranscriptionError(msg) from exc
    except BadRequestError as exc:
        msg = "A OpenAI recusou o arquivo de áudio. Verifique se a gravação não está vazia ou corrompida."
        raise TranscriptionError(msg) from exc
    except RateLimitError as exc:
        error_code = _extract_openai_error_code(exc)
        if error_code == "insufficient_quota":
            msg = (
                "A OpenAI recusou a transcrição por falta de cota ou créditos na API. "
                "Verifique Billing, créditos disponíveis e se a chave pertence ao projeto correto."
            )
        else:
            msg = (
                "A OpenAI limitou temporariamente as requisições de transcrição. "
                "Tente novamente depois ou reduza a frequência de testes."
            )
        raise TranscriptionError(msg) from exc
    except APIConnectionError as exc:
        msg = "Não foi possível conectar à OpenAI. Verifique sua internet e tente novamente."
        raise TranscriptionError(msg) from exc
    except APIStatusError as exc:
        msg = f"A OpenAI retornou um erro de serviço durante a transcrição: HTTP {exc.status_code}."
        raise TranscriptionError(msg) from exc
    except OpenAIError as exc:
        msg = "Ocorreu um erro inesperado na API da OpenAI durante a transcrição."
        raise TranscriptionError(msg) from exc
    except OSError as exc:
        msg = f"Não foi possível abrir o arquivo de áudio: {audio_file_path}"
        raise TranscriptionError(msg) from exc

    return _extract_transcription_text(response)
