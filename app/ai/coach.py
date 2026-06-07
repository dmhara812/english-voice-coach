"""Coach AI responsável por corrigir e conduzir a conversa em inglês."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Literal

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from app.config import AppSettings, ConfigError, get_settings
from app.prompts.english_coach_prompt import ENGLISH_COACH_SYSTEM_PROMPT

MistakeType = Literal[
    "grammar", "vocabulary", "pronunciation", "word_order", "naturalness"
]
JSON_RESPONSE_FORMAT: Final[dict[str, str]] = {"type": "json_object"}
MAX_COACH_TOKENS: Final = 900
DEFAULT_TEMPERATURE: Final = 0.4


class CoachError(RuntimeError):
    """Erro específico para falhas no professor de conversação."""


class Mistake(BaseModel):
    """Representa um erro ou ponto de melhoria encontrado na fala do usuário."""

    model_config = ConfigDict(extra="forbid")

    type: MistakeType
    explanation: str = Field(min_length=1)
    example: str = Field(min_length=1)


class Score(BaseModel):
    """Pontuação simples para acompanhar evolução ao longo do tempo."""

    model_config = ConfigDict(extra="forbid")

    grammar: int = Field(ge=0, le=10)
    naturalness: int = Field(ge=0, le=10)
    vocabulary: int = Field(ge=0, le=10)


class CoachResponse(BaseModel):
    """Resposta estruturada que será exibida no terminal e salva depois."""

    model_config = ConfigDict(extra="forbid")

    original_sentence: str = Field(min_length=1)
    corrected_sentence: str = Field(min_length=1)
    natural_sentence: str = Field(min_length=1)
    suggested_answers_en: list[str] = Field(
        min_length=2,
        max_length=3,
        validation_alias=AliasChoices("suggested_answers_en", "suggested_answers"),
        serialization_alias="suggested_answers_en",
    )
    mistakes: list[Mistake]
    score: Score
    coach_feedback_ptbr: str = Field(min_length=1)
    ai_response_en: str = Field(min_length=1)
    follow_up_question_en: str = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """Resumo de uma rodada anterior usado para manter contexto.

    Guardar apenas o necessário reduz custo de tokens e evita mandar histórico
    demais para a API em cada rodada.
    """

    user_transcription: str
    ai_response_en: str
    follow_up_question_en: str


def _normalize_user_transcription(user_transcription: str) -> str:
    """Normaliza a transcrição antes de enviar para o professor."""

    normalized = user_transcription.strip()

    if not normalized:
        msg = "A transcrição está vazia. Grave uma frase antes de pedir correção."
        raise CoachError(msg)

    return normalized


def _build_context_block(
    conversation_history: list[ConversationTurn],
    *,
    context_limit: int,
) -> str:
    """Monta um resumo curto das últimas rodadas da conversa."""

    if not conversation_history:
        return "No previous conversation context."

    recent_turns = conversation_history[-context_limit:]
    lines = ["Recent conversation context:"]

    for index, turn in enumerate(recent_turns, start=1):
        lines.append(f"Turn {index}:")
        lines.append(f"User said: {turn.user_transcription}")
        lines.append(f"Coach replied: {turn.ai_response_en}")
        lines.append(f"Coach asked: {turn.follow_up_question_en}")

    return "\n".join(lines)


def _build_user_prompt(
    user_transcription: str,
    conversation_history: list[ConversationTurn],
    settings: AppSettings,
) -> str:
    """Cria a mensagem do usuário com contexto, nível e transcrição atual."""

    context_block = _build_context_block(
        conversation_history,
        context_limit=settings.conversation_context_limit,
    )

    return f"""
Learner level: {settings.coach_level}
Interface language: {settings.app_language}

{context_block}

Current transcription from the learner:
{user_transcription}

Correct the current transcription and continue the conversation.
Remember: the assistant response will be shown as text in the terminal, not spoken with TTS.
Return only valid JSON.
""".strip()


def _extract_openai_error_code(exc: APIStatusError) -> str:
    """Extrai o código interno da OpenAI quando a resposta trouxer esse campo."""

    body = getattr(exc, "body", None)

    if not isinstance(body, dict):
        return ""

    error = body.get("error")

    if not isinstance(error, dict):
        return ""

    return str(error.get("code") or "")


def _extract_message_content(completion: Any) -> str:
    """Extrai o conteúdo textual da resposta do Chat Completions."""

    choices = getattr(completion, "choices", None)

    if not choices:
        msg = "A OpenAI não retornou nenhuma resposta para o coach."
        raise CoachError(msg)

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "")

    if isinstance(content, list):
        content = "".join(str(part) for part in content)

    content = str(content).strip()

    if not content:
        msg = "A resposta do coach voltou vazia. Tente novamente."
        raise CoachError(msg)

    return _remove_optional_json_fence(content)


def _remove_optional_json_fence(content: str) -> str:
    """Remove cercas Markdown caso o modelo desobedeça o prompt."""

    if not content.startswith("```"):
        return content

    lines = content.splitlines()

    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).removeprefix("json").strip()

    return content


def _validate_coach_response(raw_content: str) -> CoachResponse:
    """Valida o JSON do professor com Pydantic."""

    try:
        return CoachResponse.model_validate_json(raw_content)
    except ValidationError as exc:
        msg = (
            "A IA respondeu em JSON, mas não seguiu exatamente o formato esperado "
            "pelo projeto. Tente novamente. Se o erro persistir, revise o prompt "
            "do coach e o modelo configurado em COACH_MODEL."
        )
        raise CoachError(msg) from exc


def generate_coach_feedback(
    user_transcription: str,
    *,
    conversation_history: list[ConversationTurn] | None = None,
    settings: AppSettings | None = None,
) -> CoachResponse:
    """Gera correção, sugestões e continuação da conversa.

    Esta função recebe a transcrição já produzida pela Etapa 4. Ela não grava
    áudio e não usa TTS, porque o MVP atual responde em texto para reduzir custo
    e complexidade.
    """

    active_settings = settings or get_settings(require_openai_key=True)
    normalized_transcription = _normalize_user_transcription(user_transcription)
    active_history = conversation_history or []

    client = OpenAI(api_key=active_settings.openai_api_key)

    try:
        completion = client.chat.completions.create(
            model=active_settings.coach_model,
            messages=[
                {"role": "system", "content": ENGLISH_COACH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_user_prompt(
                        normalized_transcription,
                        active_history,
                        active_settings,
                    ),
                },
            ],
            response_format=JSON_RESPONSE_FORMAT,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=MAX_COACH_TOKENS,
        )
    except ConfigError:
        raise
    except AuthenticationError as exc:
        msg = "A OpenAI recusou a chave de API. Verifique o valor de OPENAI_API_KEY no arquivo .env."
        raise CoachError(msg) from exc
    except BadRequestError as exc:
        msg = "A OpenAI recusou a solicitação do coach. Verifique o modelo configurado em COACH_MODEL."
        raise CoachError(msg) from exc
    except RateLimitError as exc:
        error_code = _extract_openai_error_code(exc)
        if error_code == "insufficient_quota":
            msg = (
                "A OpenAI recusou o coach por falta de cota ou créditos na API. "
                "Verifique Billing, créditos disponíveis e se a chave pertence ao projeto correto."
            )
        else:
            msg = (
                "A OpenAI limitou temporariamente as requisições do coach. "
                "Tente novamente depois ou reduza a frequência de testes."
            )
        raise CoachError(msg) from exc
    except APIConnectionError as exc:
        msg = "Não foi possível conectar à OpenAI. Verifique sua internet e tente novamente."
        raise CoachError(msg) from exc
    except APIStatusError as exc:
        msg = f"A OpenAI retornou um erro de serviço no coach: HTTP {exc.status_code}."
        raise CoachError(msg) from exc
    except OpenAIError as exc:
        msg = "Ocorreu um erro inesperado na API da OpenAI durante o feedback do coach."
        raise CoachError(msg) from exc

    raw_content = _extract_message_content(completion)
    return _validate_coach_response(raw_content)
