"""Camada de acesso aos dados de conversas salvas no SQLite."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from app.ai.coach import CoachResponse, ConversationTurn
from app.config import AppSettings
from app.storage.database import DatabaseError, create_connection, initialize_database

INSERT_CONVERSATION_SQL: Final = """
INSERT INTO conversations (
    created_at,
    audio_file,
    user_transcription,
    corrected_sentence,
    natural_sentence,
    suggested_answers_json,
    mistakes_json,
    grammar_score,
    naturalness_score,
    vocabulary_score,
    coach_feedback_ptbr,
    ai_response_en,
    follow_up_question_en
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SELECT_RECENT_CONVERSATIONS_SQL: Final = """
SELECT
    id,
    created_at,
    audio_file,
    user_transcription,
    corrected_sentence,
    natural_sentence,
    suggested_answers_json,
    mistakes_json,
    grammar_score,
    naturalness_score,
    vocabulary_score,
    coach_feedback_ptbr,
    ai_response_en,
    follow_up_question_en
FROM conversations
ORDER BY id DESC
LIMIT ?;
"""

SELECT_CONVERSATION_BY_ID_SQL: Final = """
SELECT
    id,
    created_at,
    audio_file,
    user_transcription,
    corrected_sentence,
    natural_sentence,
    suggested_answers_json,
    mistakes_json,
    grammar_score,
    naturalness_score,
    vocabulary_score,
    coach_feedback_ptbr,
    ai_response_en,
    follow_up_question_en
FROM conversations
WHERE id = ?;
"""


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    """Representa uma conversa já persistida no banco."""

    id: int
    created_at: str
    audio_file: str | None
    user_transcription: str
    corrected_sentence: str | None
    natural_sentence: str | None
    suggested_answers: list[str]
    mistakes: list[dict[str, Any]]
    grammar_score: int | None
    naturalness_score: int | None
    vocabulary_score: int | None
    coach_feedback_ptbr: str | None
    ai_response_en: str | None
    follow_up_question_en: str | None

    def to_context_turn(self) -> ConversationTurn:
        """Converte o registro salvo para o formato de contexto do coach.

        O coach não precisa receber todos os dados do banco. Para manter custo
        baixo, enviamos apenas o que ajuda a continuar a conversa: fala do aluno,
        resposta do professor e pergunta feita anteriormente.
        """

        return ConversationTurn(
            user_transcription=self.user_transcription,
            ai_response_en=self.ai_response_en or "",
            follow_up_question_en=self.follow_up_question_en or "",
        )


def save_conversation(
    *,
    user_transcription: str,
    coach_response: CoachResponse,
    audio_file: Path | str | None = None,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> int:
    """Salva uma rodada completa da conversa no SQLite.

    A função recebe a transcrição e o objeto validado pelo Pydantic. Isso evita
    salvar uma resposta solta da IA sem garantia de formato.
    """

    normalized_transcription = user_transcription.strip()

    if not normalized_transcription:
        msg = "Não é possível salvar uma conversa sem transcrição do usuário."
        raise DatabaseError(msg)

    initialize_database(db_path, settings=settings)

    audio_file_text = str(audio_file) if audio_file is not None else None
    mistakes_json = _json_dumps(
        [mistake.model_dump(mode="json") for mistake in coach_response.mistakes]
    )
    suggested_answers_json = _json_dumps(coach_response.suggested_answers_en)

    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        with connection:
            cursor = connection.execute(
                INSERT_CONVERSATION_SQL,
                (
                    _utc_now_iso(),
                    audio_file_text,
                    normalized_transcription,
                    coach_response.corrected_sentence,
                    coach_response.natural_sentence,
                    suggested_answers_json,
                    mistakes_json,
                    coach_response.score.grammar,
                    coach_response.score.naturalness,
                    coach_response.score.vocabulary,
                    coach_response.coach_feedback_ptbr,
                    coach_response.ai_response_en,
                    coach_response.follow_up_question_en,
                ),
            )
    except sqlite3.Error as exc:
        msg = "Não foi possível salvar a conversa no SQLite."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    return int(cursor.lastrowid)


def list_recent_conversations(
    *,
    limit: int = 6,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> list[ConversationRecord]:
    """Lista as conversas recentes em ordem cronológica.

    O banco busca primeiro as últimas linhas por `id DESC`, mas a função devolve
    em ordem antiga → recente para facilitar o uso como contexto do coach.
    """

    if limit <= 0:
        msg = "O limite de conversas recentes deve ser maior que zero."
        raise DatabaseError(msg)

    initialize_database(db_path, settings=settings)

    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        rows = connection.execute(SELECT_RECENT_CONVERSATIONS_SQL, (limit,)).fetchall()
    except sqlite3.Error as exc:
        msg = "Não foi possível listar o histórico de conversas."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    records = [_row_to_record(row) for row in rows]
    return list(reversed(records))


def get_conversation_by_id(
    conversation_id: int,
    *,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> ConversationRecord | None:
    """Busca uma conversa específica pelo identificador interno."""

    if conversation_id <= 0:
        msg = "O id da conversa deve ser maior que zero."
        raise DatabaseError(msg)

    initialize_database(db_path, settings=settings)

    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        row = connection.execute(
            SELECT_CONVERSATION_BY_ID_SQL,
            (conversation_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        msg = f"Não foi possível buscar a conversa de id {conversation_id}."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    if row is None:
        return None

    return _row_to_record(row)


def build_context_from_recent_conversations(
    *,
    limit: int = 6,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> list[ConversationTurn]:
    """Monta o histórico curto que será enviado ao coach na integração."""

    records = list_recent_conversations(
        limit=limit,
        db_path=db_path,
        settings=settings,
    )

    return [
        record.to_context_turn()
        for record in records
        if record.ai_response_en and record.follow_up_question_en
    ]


def _row_to_record(row: sqlite3.Row) -> ConversationRecord:
    """Converte uma linha do SQLite para uma dataclass do projeto."""

    return ConversationRecord(
        id=int(row["id"]),
        created_at=str(row["created_at"]),
        audio_file=_optional_str(row["audio_file"]),
        user_transcription=str(row["user_transcription"]),
        corrected_sentence=_optional_str(row["corrected_sentence"]),
        natural_sentence=_optional_str(row["natural_sentence"]),
        suggested_answers=_json_loads_str_list(row["suggested_answers_json"]),
        mistakes=_json_loads_dict_list(row["mistakes_json"]),
        grammar_score=_optional_int(row["grammar_score"]),
        naturalness_score=_optional_int(row["naturalness_score"]),
        vocabulary_score=_optional_int(row["vocabulary_score"]),
        coach_feedback_ptbr=_optional_str(row["coach_feedback_ptbr"]),
        ai_response_en=_optional_str(row["ai_response_en"]),
        follow_up_question_en=_optional_str(row["follow_up_question_en"]),
    )


def _utc_now_iso() -> str:
    """Gera data/hora em UTC para histórico consistente."""

    return datetime.now(UTC).isoformat(timespec="seconds")


def _json_dumps(value: Any) -> str:
    """Serializa listas/dicionários preservando acentos em português."""

    return json.dumps(value, ensure_ascii=False)


def _json_loads_str_list(raw_value: str | None) -> list[str]:
    """Lê uma lista de strings salva como JSON."""

    loaded_value = _json_loads_list(raw_value)
    return [item for item in loaded_value if isinstance(item, str)]


def _json_loads_dict_list(raw_value: str | None) -> list[dict[str, Any]]:
    """Lê uma lista de dicionários salva como JSON."""

    loaded_value = _json_loads_list(raw_value)
    return [item for item in loaded_value if isinstance(item, dict)]


def _json_loads_list(raw_value: str | None) -> list[Any]:
    """Converte JSON textual em lista com fallback seguro."""

    if not raw_value:
        return []

    try:
        loaded_value = json.loads(raw_value)
    except json.JSONDecodeError:
        return []

    if not isinstance(loaded_value, list):
        return []

    return loaded_value


def _optional_str(value: object) -> str | None:
    """Converte valores opcionais do SQLite para string ou None."""

    if value is None:
        return None

    return str(value)


def _optional_int(value: object) -> int | None:
    """Converte valores opcionais do SQLite para inteiro ou None."""

    if value is None:
        return None

    return int(value)
