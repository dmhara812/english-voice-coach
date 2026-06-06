"""Testes das sessões de conversa salvas no SQLite."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.ai.coach import CoachResponse
from app.storage.database import initialize_database
from app.storage.repository import (
    build_context_from_recent_conversations,
    count_conversations_in_session,
    create_conversation_session,
    save_conversation,
)


def _make_response(topic: str) -> CoachResponse:
    """Cria uma resposta válida para salvar no banco de teste."""

    return CoachResponse.model_validate(
        {
            "original_sentence": f"I talked about {topic}.",
            "corrected_sentence": f"I talked about {topic}.",
            "natural_sentence": f"I was talking about {topic}.",
            "suggested_answers_en": [
                f"I want to learn more about {topic}.",
                f"I think {topic} is useful for my studies.",
            ],
            "mistakes": [],
            "score": {
                "grammar": 9,
                "naturalness": 8,
                "vocabulary": 8,
            },
            "coach_feedback_ptbr": "Resposta válida para teste de banco.",
            "ai_response_en": f"That is a good topic to practice: {topic}.",
            "follow_up_question_en": f"What do you like most about {topic}?",
        }
    )


class StorageSessionsTest(unittest.TestCase):
    """Garante que sessões diferentes não misturam contexto."""

    def test_context_is_limited_to_current_session(self) -> None:
        """Cada execução do app deve poder começar uma conversa limpa."""

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "conversations.db"
            initialize_database(db_path)

            first_session_id = create_conversation_session(
                title="Primeiro dia",
                db_path=db_path,
            )
            second_session_id = create_conversation_session(
                title="Segundo dia",
                db_path=db_path,
            )

            save_conversation(
                user_transcription="I talked about Python.",
                coach_response=_make_response("Python"),
                session_id=first_session_id,
                db_path=db_path,
            )
            save_conversation(
                user_transcription="I talked about English.",
                coach_response=_make_response("English"),
                session_id=second_session_id,
                db_path=db_path,
            )

            first_context = build_context_from_recent_conversations(
                session_id=first_session_id,
                db_path=db_path,
            )
            second_context = build_context_from_recent_conversations(
                session_id=second_session_id,
                db_path=db_path,
            )

            self.assertEqual(
                count_conversations_in_session(first_session_id, db_path=db_path), 1
            )
            self.assertEqual(
                count_conversations_in_session(second_session_id, db_path=db_path), 1
            )
            self.assertEqual(
                first_context[0].user_transcription, "I talked about Python."
            )
            self.assertEqual(
                second_context[0].user_transcription, "I talked about English."
            )


if __name__ == "__main__":
    unittest.main()
