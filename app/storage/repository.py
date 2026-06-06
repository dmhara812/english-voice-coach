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

INSERT_SESSION_SQL: Final = """
INSERT INTO conversation_sessions (started_at, title)
VALUES (?, ?);
"""

FINISH_SESSION_SQL: Final = """
UPDATE conversation_sessions
SET ended_at = ?
WHERE id = ?;
"""

SELECT_SESSION_BY_ID_SQL: Final = """
SELECT id, started_at, ended_at, title
FROM conversation_sessions
WHERE id = ?;
"""

SELECT_RECENT_SESSIONS_SQL: Final = """
SELECT id, started_at, ended_at, title
FROM conversation_sessions
ORDER BY id DESC
LIMIT ?;
"""

INSERT_CONVERSATION_SQL: Final = """
INSERT INTO conversations (
    session_id,
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
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SELECT_RECENT_CONVERSATIONS_ALL_SQL: Final = """
SELECT
    id,
    session_id,
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

SELECT_RECENT_CONVERSATIONS_BY_SESSION_SQL: Final = """
SELECT
    id,
    session_id,
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
WHERE session_id = ?
ORDER BY id DESC
LIMIT ?;
"""

COUNT_CONVERSATIONS_BY_SESSION_SQL: Final = """
SELECT COUNT(*) AS total
FROM conversations
WHERE session_id = ?;
"""


@dataclass(frozen=True, slots=True)
class ConversationSessionRecord:
    """Representa uma sessão de estudo salva no banco."""

    id: int
    started_at: str
    ended_at: str | None
    title: str | None


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    """Representa uma rodada da conversa já persistida no banco."""

    id: int
    session_id: int | None
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
        """Converte o registro salvo para o formato de contexto do coach."""

        return ConversationTurn(
            user_transcription=self.user_transcription,
            ai_response_en=self.ai_response_en or "",
            follow_up_question_en=self.follow_up_question_en or "",
        )


def create_conversation_session(
    *,
    title: str | None = None,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> int:
    """Cria uma nova sessão de estudo.

    Na integração final, cada execução do `python run.py` deve chamar esta função
    uma vez. Assim a conversa de hoje fica separada da conversa de outro dia.
    """

    initialize_database(db_path, settings=settings)
    normalized_title = title.strip() if title and title.strip() else None
    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        with connection:
            cursor = connection.execute(
                INSERT_SESSION_SQL,
                (_utc_now_iso(), normalized_title),
            )
    except sqlite3.Error as exc:
        msg = "Não foi possível criar uma nova sessão de conversa."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    return int(cursor.lastrowid)


def finish_conversation_session(
    session_id: int,
    *,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> None:
    """Marca uma sessão como finalizada."""

    _validate_positive_id(session_id, "session_id")
    initialize_database(db_path, settings=settings)
    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        with connection:
            connection.execute(FINISH_SESSION_SQL, (_utc_now_iso(), session_id))
    except sqlite3.Error as exc:
        msg = f"Não foi possível finalizar a sessão {session_id}."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()


def get_conversation_session_by_id(
    session_id: int,
    *,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> ConversationSessionRecord | None:
    """Busca uma sessão específica pelo identificador."""

    _validate_positive_id(session_id, "session_id")
    initialize_database(db_path, settings=settings)
    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        row = connection.execute(SELECT_SESSION_BY_ID_SQL, (session_id,)).fetchone()
    except sqlite3.Error as exc:
        msg = f"Não foi possível buscar a sessão {session_id}."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    if row is None:
        return None

    return _row_to_session_record(row)


def list_recent_sessions(
    *,
    limit: int = 10,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> list[ConversationSessionRecord]:
    """Lista as sessões mais recentes, da mais nova para a mais antiga."""

    if limit <= 0:
        msg = "O limite de sessões recentes deve ser maior que zero."
        raise DatabaseError(msg)

    initialize_database(db_path, settings=settings)
    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        rows = connection.execute(SELECT_RECENT_SESSIONS_SQL, (limit,)).fetchall()
    except sqlite3.Error as exc:
        msg = "Não foi possível listar as sessões recentes."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    return [_row_to_session_record(row) for row in rows]


def save_conversation(
    *,
    user_transcription: str,
    coach_response: CoachResponse,
    session_id: int | None = None,
    audio_file: Path | str | None = None,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> int:
    """Salva uma rodada completa da conversa no SQLite."""

    normalized_transcription = user_transcription.strip()

    if not normalized_transcription:
        msg = "Não é possível salvar uma conversa sem transcrição do usuário."
        raise DatabaseError(msg)

    active_session_id = session_id or create_conversation_session(
        title="Sessão criada automaticamente",
        db_path=db_path,
        settings=settings,
    )

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
                    active_session_id,
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
    session_id: int | None = None,
    limit: int = 6,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> list[ConversationRecord]:
    """Lista conversas recentes em ordem cronológica.

    Quando `session_id` é informado, o contexto fica limitado à sessão atual. É
    isso que evita misturar a conversa de hoje com a conversa de outro dia.
    """

    if limit <= 0:
        msg = "O limite de conversas recentes deve ser maior que zero."
        raise DatabaseError(msg)

    if session_id is not None:
        _validate_positive_id(session_id, "session_id")

    initialize_database(db_path, settings=settings)
    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        if session_id is None:
            rows = connection.execute(
                SELECT_RECENT_CONVERSATIONS_ALL_SQL,
                (limit,),
            ).fetchall()
        else:
            rows = connection.execute(
                SELECT_RECENT_CONVERSATIONS_BY_SESSION_SQL,
                (session_id, limit),
            ).fetchall()
    except sqlite3.Error as exc:
        msg = "Não foi possível listar o histórico de conversas."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    records = [_row_to_conversation_record(row) for row in rows]
    return list(reversed(records))


def count_conversations_in_session(
    session_id: int,
    *,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> int:
    """Conta quantas rodadas foram salvas em uma sessão."""

    _validate_positive_id(session_id, "session_id")
    initialize_database(db_path, settings=settings)
    connection: sqlite3.Connection | None = None

    try:
        connection = create_connection(db_path, settings=settings)
        row = connection.execute(
            COUNT_CONVERSATIONS_BY_SESSION_SQL,
            (session_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        msg = f"Não foi possível contar as conversas da sessão {session_id}."
        raise DatabaseError(msg) from exc
    finally:
        if connection is not None:
            connection.close()

    return int(row["total"])


def build_context_from_recent_conversations(
    *,
    session_id: int | None = None,
    limit: int = 6,
    db_path: Path | None = None,
    settings: AppSettings | None = None,
) -> list[ConversationTurn]:
    """Monta o histórico curto que será enviado ao coach na integração."""

    records = list_recent_conversations(
        session_id=session_id,
        limit=limit,
        db_path=db_path,
        settings=settings,
    )

    return [
        record.to_context_turn()
        for record in records
        if record.ai_response_en and record.follow_up_question_en
    ]


def _row_to_session_record(row: sqlite3.Row) -> ConversationSessionRecord:
    """Converte uma linha do SQLite para uma sessão do projeto."""

    return ConversationSessionRecord(
        id=int(row["id"]),
        started_at=str(row["started_at"]),
        ended_at=_optional_str(row["ended_at"]),
        title=_optional_str(row["title"]),
    )


def _row_to_conversation_record(row: sqlite3.Row) -> ConversationRecord:
    """Converte uma linha do SQLite para uma conversa do projeto."""

    return ConversationRecord(
        id=int(row["id"]),
        session_id=_optional_int(row["session_id"]),
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


def _validate_positive_id(value: int, field_name: str) -> None:
    """Garante que identificadores internos sejam positivos."""

    if value <= 0:
        msg = f"{field_name} deve ser maior que zero."
        raise DatabaseError(msg)


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
