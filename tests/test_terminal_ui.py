"""Testes da montagem visual da resposta do professor."""

from __future__ import annotations

import unittest

from app.ai.coach import CoachResponse
from app.ui.terminal_ui import _build_teacher_message


def _make_response(
    *,
    ai_response_en: str = "That sounds like a useful project.",
    follow_up_question_en: str = "What did you learn from it?",
) -> CoachResponse:
    """Cria uma resposta válida do coach para testes de UI."""

    return CoachResponse.model_validate(
        {
            "original_sentence": "I created a project.",
            "corrected_sentence": "I created a project.",
            "natural_sentence": "I worked on a project recently.",
            "suggested_answers_en": [
                "I built a small app to practice Python.",
                "I learned how to organize my code better.",
            ],
            "mistakes": [],
            "score": {
                "grammar": 9,
                "naturalness": 8,
                "vocabulary": 8,
            },
            "coach_feedback_ptbr": "Boa resposta. Continue desenvolvendo a ideia.",
            "ai_response_en": ai_response_en,
            "follow_up_question_en": follow_up_question_en,
        }
    )


class TerminalUiTest(unittest.TestCase):
    """Valida a experiência de conversa exibida no terminal."""

    def test_teacher_message_combines_answer_and_question(self) -> None:
        """Resposta e pergunta devem aparecer no mesmo bloco visual."""

        response = _make_response()
        message = _build_teacher_message(response)

        self.assertIn("That sounds like a useful project.", message)
        self.assertIn("What did you learn from it?", message)
        self.assertNotIn("Question", message)

    def test_teacher_message_avoids_two_questions_when_answer_already_asks(
        self,
    ) -> None:
        """Se o modelo já colocou pergunta na resposta, a UI evita duplicar."""

        response = _make_response(
            ai_response_en="That sounds interesting. What kind of project was it?",
            follow_up_question_en="What did you learn from it?",
        )
        message = _build_teacher_message(response)

        self.assertIn("What kind of project was it?", message)
        self.assertNotIn("What did you learn from it?", message)


if __name__ == "__main__":
    unittest.main()
