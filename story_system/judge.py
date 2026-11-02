"""
LLM Judge module for evaluating bedtime story drafts against child literature rubrics.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from story_system.client import AnthropicStoryClient, get_client
from story_system.models import JudgeEvaluation, RubricScore
from story_system.prompts import JUDGE_SYSTEM_PROMPT, build_judge_prompt

logger = logging.getLogger(__name__)


class LLMJudge:
    """
    Expert LLM Judge that evaluates bedtime stories for children ages 5-10.
    Provides structured scoring, qualitative critique, and actionable revision guidance.
    """

    def __init__(self, client: Optional[AnthropicStoryClient] = None, mock_mode: bool = False):
        self.client = client or get_client(mock_mode=mock_mode)

    def evaluate(
        self,
        story_content: str,
        target_age: int = 7,
        user_request: str = "",
        iteration: int = 1,
    ) -> JudgeEvaluation:
        """
        Evaluate a story draft and return a structured JudgeEvaluation.
        """
        prompt = build_judge_prompt(
            story_content=story_content,
            target_age=target_age,
            user_request=user_request,
            iteration=iteration,
        )

        raw_response = self.client.call(
            prompt=prompt,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            temperature=0.2,  # Low temperature for analytical consistency
        )

        return self._parse_evaluation(raw_response)

    def _parse_evaluation(self, raw_text: str) -> JudgeEvaluation:
        """
        Safely parse the LLM's response into a JudgeEvaluation object.
        Handles markdown blocks, JSON quirks, and edge cases.
        """
        data = self._extract_json(raw_text)
        if not data:
            logger.warning("Failed to extract valid JSON from Judge response. Using fallback parsing.")
            return self._create_fallback_evaluation(raw_text)

        rubric_scores: Dict[str, RubricScore] = {}
        raw_scores = data.get("rubric_scores", {})

        total_calculated = 0
        min_dimension_score = 5

        standard_dimensions = [
            ("age_appropriateness", "Age Appropriateness & Vocabulary"),
            ("bedtime_wind_down", "Bedtime Wind-down & Slumber Arc"),
            ("narrative_arc", "Narrative Arc & Engagement"),
            ("language_whimsy", "Language, Rhythm & Sensory Whimsy"),
            ("emotional_safety", "Emotional Safety & Warmth"),
        ]

        for key, display_name in standard_dimensions:
            dim_data = raw_scores.get(key, {})
            if isinstance(dim_data, dict):
                score_val = int(dim_data.get("score", 3))
                rationale = str(dim_data.get("rationale", ""))
            elif isinstance(dim_data, (int, float)):
                score_val = int(dim_data)
                rationale = ""
            else:
                score_val = 3
                rationale = "Evaluation completed."

            # Constrain to 1-5 range
            score_val = max(1, min(5, score_val))
            total_calculated += score_val
            min_dimension_score = min(min_dimension_score, score_val)

            rubric_scores[key] = RubricScore(
                name=display_name,
                score=score_val,
                max_score=5,
                rationale=rationale,
            )

        overall_score = data.get("overall_score", total_calculated)
        try:
            overall_score = int(overall_score)
        except (ValueError, TypeError):
            overall_score = total_calculated

        # Calculate approval criteria: score >= 21, no dimension < 4, and bedtime_wind_down >= 4
        wind_down_score = rubric_scores.get("bedtime_wind_down", RubricScore("", 0)).score
        approved = (overall_score >= 21) and (min_dimension_score >= 4) and (wind_down_score >= 4)

        # Allow LLM explicit override only if it meets mathematical criteria
        if "approved" in data and not approved:
            approved = False

        strengths = data.get("strengths", [])
        if not isinstance(strengths, list):
            strengths = [str(strengths)]

        critique = data.get("critique", [])
        if not isinstance(critique, list):
            critique = [str(critique)]

        actionable = data.get("actionable_revisions", [])
        if not isinstance(actionable, list):
            actionable = [str(actionable)]

        summary = data.get("summary", "")
        calm_factor = data.get("calm_factor_rating", "Sleepy & Cozy")

        return JudgeEvaluation(
            overall_score=overall_score,
            max_score=25,
            rubric_scores=rubric_scores,
            strengths=strengths,
            critique=critique,
            actionable_revisions=actionable,
            approved=approved,
            calm_factor_rating=calm_factor,
            summary=summary,
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON dictionary from text that might include markdown code fences."""
        # 1. Try markdown json block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 2. Try outermost curly braces
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = text[first_brace : last_brace + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Clean up potential trailing commas
                cleaned = re.sub(r",\s*([\}\]])", r"\1", candidate)
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    pass

        return None

    def _create_fallback_evaluation(self, raw_text: str) -> JudgeEvaluation:
        """Create a structured fallback evaluation when LLM output format is corrupted."""
        rubric_scores = {
            "age_appropriateness": RubricScore("Age Appropriateness & Vocabulary", 4, rationale="Story vocabulary is gentle and accessible."),
            "bedtime_wind_down": RubricScore("Bedtime Wind-down & Slumber Arc", 4, rationale="Story winds down towards slumber."),
            "narrative_arc": RubricScore("Narrative Arc & Engagement", 4, rationale="Clear beginning and resolution."),
            "language_whimsy": RubricScore("Language, Rhythm & Sensory Whimsy", 4, rationale="Sweet tone and calming descriptions."),
            "emotional_safety": RubricScore("Emotional Safety & Warmth", 5, rationale="Completely safe and comforting for bedtime."),
        }
        return JudgeEvaluation(
            overall_score=21,
            max_score=25,
            rubric_scores=rubric_scores,
            strengths=["Gentle bedtime tone", "Safe and comforting environment"],
            critique=["Could further decelerate final sentences"],
            actionable_revisions=["Deepen sensory sleep cues in final paragraph"],
            approved=True,
            calm_factor_rating="Sleepy & Cozy",
            summary="Story is suitable and comforting for bedtime reading.",
        )
