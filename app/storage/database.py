"""Configuração e inicialização do banco SQLite do projeto."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Final

from app.config import AppSettings, get_settings

CONVERSATIONS_TABLE: Final = "conversations"

CREATE_CONVERSATIONS_TABLE_SQL: Final = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    audio_file TEXT,
    user_transcription TEXT NOT NULL,
    corrected_sentence TEXT,
    natural_sentence TEXT,
    suggested_answers_json TEXT,
    mistakes_json TEXT,
    grammar_score INTEGER,
    naturalness_score INTEGER,
    vocabulary_score INTEGER,
    coach_feedback_ptbr TEXT,
    ai_response_en TEXT,
    follow_up_question_en TEXT
);
"""

CREATE_CONVERSATIONS_CREATED_AT_INDEX_SQL: Final = """
CREATE INDEX IF NOT EXISTS idx_conversations_created_at
ON conversations (created_at);
"""

# A lista permite evoluir o banco local sem apagar dados caso alguma pessoa já
# tenha criado a tabela em uma versão anterior da documentação.
REQUIRED_COLUMNS: Final[dict[str, str]] = {
    "suggested_answers_json": "TEXT",
    "follow_up_question_en": "TEXT",
}


class DatabaseError(RuntimeError):
    """Erro específico para falhas ao preparar ou acessar o SQLite."""


def _resolve_db_path(
    db_path: Path | None,
    settings: AppSettings | None,
) -> Path:
    """Resolve o caminho do banco a partir do parâmetro ou do `.env`."""

    if db_path is not None:
        return db_path

    active_settings = settings or get_settings()
    return active_settings.db_path


def _ensure_database_directory(db_path: Path) -> None:
    """Cria a pasta do banco antes de conectar.

    O SQLite cria o arquivo automaticamente, mas não cria diretórios pais. Por
    isso garantimos a pasta `data/` antes da primeira conexão.
    """

    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        msg = f"Não foi possível criar a pasta do banco de dados: {db_path.parent}."
        raise DatabaseError(msg) from exc


def create_connection(
    db_path: Path | None = None,
    *,
    settings: AppSettings | None = None,
) -> sqlite3.Connection:
    """Cria uma conexão SQLite configurada com `sqlite3.Row`.

    Usar `sqlite3.Row` permite acessar colunas pelo nome no repositório, deixando
    o código mais legível do que depender da posição de cada coluna no SELECT.
    """

    resolved_db_path = _resolve_db_path(db_path, settings)
    _ensure_database_directory(resolved_db_path)

    try:
        connection = sqlite3.connect(resolved_db_path)
    except sqlite3.Error as exc:
        msg = f"Não foi possível conectar ao banco SQLite em {resolved_db_path}."
        raise DatabaseError(msg) from exc

    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_connection(
    db_path: Path | None = None,
    *,
    settings: AppSettings | None = None,
) -> Iterator[sqlite3.Connection]:
    """Abre e fecha a conexão automaticamente.

    O context manager evita conexões esquecidas abertas durante os ciclos de
    conversa. Isso é simples e suficiente para um app local de terminal.
    """

    connection = create_connection(db_path, settings=settings)

    try:
        yield connection
    finally:
        connection.close()


def initialize_database(
    db_path: Path | None = None,
    *,
    settings: AppSettings | None = None,
) -> None:
    """Cria a tabela principal e índices necessários para o histórico."""

    try:
        with get_connection(db_path, settings=settings) as connection:
            connection.execute(CREATE_CONVERSATIONS_TABLE_SQL)
            _ensure_required_columns(connection)
            connection.execute(CREATE_CONVERSATIONS_CREATED_AT_INDEX_SQL)
            connection.commit()
    except sqlite3.Error as exc:
        msg = "Não foi possível inicializar o banco SQLite do projeto."
        raise DatabaseError(msg) from exc


def _ensure_required_columns(connection: sqlite3.Connection) -> None:
    """Adiciona colunas novas caso o banco já exista de uma versão anterior."""

    existing_columns = _get_existing_columns(connection)

    for column_name, column_type in REQUIRED_COLUMNS.items():
        if column_name in existing_columns:
            continue

        connection.execute(
            f"ALTER TABLE {CONVERSATIONS_TABLE} ADD COLUMN {column_name} {column_type};"
        )


def _get_existing_columns(connection: sqlite3.Connection) -> set[str]:
    """Lê as colunas atuais da tabela `conversations`."""

    rows = connection.execute(f"PRAGMA table_info({CONVERSATIONS_TABLE});").fetchall()
    return {str(row["name"]) for row in rows}
