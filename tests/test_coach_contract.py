"""Testes do contrato Pydantic usado pelo professor de inglês."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.ai.coach import CoachResponse


class CoachContractTest(unittest.TestCase):
    """Garante que o JSON esperado pelo coach continua validável."""

    def test_valid_coach_response_is_accepted(self) -> None:
        """Valida um exemplo completo de resposta do professor."""

        response = CoachResponse.model_validate(
            {
                "original_sentence": "I like create programs.",
                "corrected_sentence": "I like creating programs.",
                "natural_sentence": "I enjoy creating software and small apps.",
                "suggested_answers_en": [
                    "I usually build small projects to practice.",
                    "I like creating tools that solve simple problems.",
                ],
                "mistakes": [
                    {
                        "type": "grammar",
                        "explanation": "Use a gerund after 'like' in this sentence.",
                        "example": "I like creating programs.",
                    }
                ],
                "score": {
                    "grammar": 7,
                    "naturalness": 7,
                    "vocabulary": 6,
                },
                "coach_feedback_ptbr": "Boa ideia, mas use 'creating' depois de 'like'.",
                "ai_response_en": "That sounds like a useful way to practice programming.",
                "follow_up_question_en": "What kind of app would you like to build next?",
            }
        )

        self.assertEqual(response.score.grammar, 7)
        self.assertEqual(len(response.suggested_answers_en), 2)

    def test_invalid_score_is_rejected(self) -> None:
        """Garante que notas fora de 0 a 10 continuam proibidas."""

        with self.assertRaises(ValidationError):
            CoachResponse.model_validate(
                {
                    "original_sentence": "I like create programs.",
                    "corrected_sentence": "I like creating programs.",
                    "natural_sentence": "I enjoy creating software.",
                    "suggested_answers_en": [
                        "I like building apps.",
                        "I want to create useful tools.",
                    ],
                    "mistakes": [],
                    "score": {
                        "grammar": 11,
                        "naturalness": 8,
                        "vocabulary": 7,
                    },
                    "coach_feedback_ptbr": "Feedback de teste.",
                    "ai_response_en": "That is a good topic for practice.",
                    "follow_up_question_en": "What are you building now?",
                }
            )


if __name__ == "__main__":
    unittest.main()
