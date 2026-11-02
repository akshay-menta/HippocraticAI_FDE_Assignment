"""
Comprehensive test suite for the Bedtime Storyteller & LLM Judge System.
Built using standard library unittest for zero extra dependencies.
"""

import json
import unittest

from story_system.client import AnthropicStoryClient, call_claude
from story_system.judge import LLMJudge
from story_system.models import (
    JudgeEvaluation,
    RubricScore,
    StoryDraft,
    StoryPipelineResult,
    StoryRequest,
)
from story_system.orchestrator import BedtimeStoryPipeline
from story_system.prompts import (
    JUDGE_SYSTEM_PROMPT,
    STORYTELLER_SYSTEM_PROMPT,
    build_judge_prompt,
    build_revision_prompt,
    build_storyteller_prompt,
)
from story_system.storyteller import StorytellerAgent
from main import call_model


class TestBedtimeStorySystem(unittest.TestCase):
    """Test suite covering data models, client, judge, storyteller, and orchestration."""

    def test_story_request_properties(self):
        """Verify StoryRequest age group categorization and properties."""
        req_young = StoryRequest(prompt="A story about a puppy", target_age=5)
        self.assertIn("Early Childhood", req_young.age_group)

        req_mid = StoryRequest(prompt="A story about space", target_age=7)
        self.assertIn("Mid Childhood", req_mid.age_group)

        req_older = StoryRequest(prompt="A story about time travel", target_age=10)
        self.assertIn("Upper Childhood", req_older.age_group)

    def test_story_draft_word_count_and_reading_time(self):
        """Verify word count and read aloud time computation."""
        content = "Once upon a time there was a tiny blue bird. " * 50  # 500 words
        draft = StoryDraft(iteration=1, title="The Tiny Blue Bird", content=content)
        self.assertEqual(draft.word_count, 500)
        self.assertEqual(draft.estimated_read_time_minutes, round(500 / 125.0, 1))

    def test_client_mock_mode(self):
        """Verify AnthropicStoryClient mock mode returns high quality responses."""
        client = AnthropicStoryClient(mock_mode=True)
        response = client.call(
            prompt="Tell me a bedtime story about Alice and Bob",
            system_prompt=STORYTELLER_SYSTEM_PROMPT,
        )
        self.assertIn("Alice", response)
        self.assertIn("Bob", response)

    def test_judge_parsing_valid_json(self):
        """Verify LLMJudge successfully parses valid markdown JSON responses."""
        judge = LLMJudge(mock_mode=True)
        sample_json = """```json
        {
          "rubric_scores": {
            "age_appropriateness": {"score": 5, "rationale": "Clear and accessible."},
            "bedtime_wind_down": {"score": 5, "rationale": "Very sleepy."},
            "narrative_arc": {"score": 4, "rationale": "Solid arc."},
            "language_whimsy": {"score": 4, "rationale": "Charming."},
            "emotional_safety": {"score": 5, "rationale": "Deeply comforting."}
          },
          "overall_score": 23,
          "approved": true,
          "calm_factor_rating": "Perfect Bedtime Slumber",
          "strengths": ["Wonderful cadence"],
          "critique": ["None"],
          "actionable_revisions": []
        }
        ```"""
        eval_result = judge._parse_evaluation(sample_json)
        self.assertEqual(eval_result.overall_score, 23)
        self.assertTrue(eval_result.approved)
        self.assertEqual(eval_result.rubric_scores["age_appropriateness"].score, 5)
        self.assertEqual(eval_result.rubric_scores["bedtime_wind_down"].score, 5)

    def test_judge_approval_logic(self):
        """Verify approval criteria: total >= 21, no score < 4, bedtime_wind_down >= 4."""
        judge = LLMJudge(mock_mode=True)

        # Fails because bedtime wind-down is 3 (even though total is 21)
        fail_json = """```json
        {
          "rubric_scores": {
            "age_appropriateness": {"score": 5, "rationale": "Great"},
            "bedtime_wind_down": {"score": 3, "rationale": "Ending is too exciting"},
            "narrative_arc": {"score": 5, "rationale": "Great"},
            "language_whimsy": {"score": 4, "rationale": "Great"},
            "emotional_safety": {"score": 4, "rationale": "Safe"}
          },
          "overall_score": 21,
          "approved": true
        }
        ```"""
        eval_fail = judge._parse_evaluation(fail_json)
        self.assertFalse(eval_fail.approved)  # Overridden by business logic because wind-down < 4

        # Passes because all criteria are satisfied
        pass_json = """```json
        {
          "rubric_scores": {
            "age_appropriateness": {"score": 5, "rationale": "Great"},
            "bedtime_wind_down": {"score": 5, "rationale": "Sleepy"},
            "narrative_arc": {"score": 4, "rationale": "Good"},
            "language_whimsy": {"score": 4, "rationale": "Good"},
            "emotional_safety": {"score": 5, "rationale": "Safe"}
          },
          "overall_score": 23,
          "approved": true
        }
        ```"""
        eval_pass = judge._parse_evaluation(pass_json)
        self.assertTrue(eval_pass.approved)

    def test_judge_corrupted_json_fallback(self):
        """Verify graceful recovery if the LLM output is not valid JSON."""
        judge = LLMJudge(mock_mode=True)
        corrupted_output = "I cannot generate JSON right now, but this story was very cozy."
        eval_fallback = judge._parse_evaluation(corrupted_output)
        self.assertIsInstance(eval_fallback, JudgeEvaluation)
        self.assertGreater(eval_fallback.overall_score, 0)
        self.assertEqual(len(eval_fallback.rubric_scores), 5)

    def test_storyteller_title_extraction(self):
        """Verify title and content parsing from generated story."""
        storyteller = StorytellerAgent(mock_mode=True)
        raw_story = "# The Sleepy Hedgehog's Blanket\n\nOnce upon a time in a misty forest..."
        title, content = storyteller._extract_title_and_content(raw_story)
        self.assertEqual(title, "The Sleepy Hedgehog's Blanket")
        self.assertIn("Once upon a time", content)

    def test_pipeline_end_to_end(self):
        """Verify BedtimeStoryPipeline runs end-to-end with iteration progression."""
        pipeline = BedtimeStoryPipeline(mock_mode=True)
        request = StoryRequest(
            prompt="A story about Alice and Bob the cat",
            target_age=7,
            sleepy_factor=5,
        )

        events_logged = []
        def on_step(event, data):
            events_logged.append(event)

        result = pipeline.run(request, max_iterations=2, on_step=on_step)

        self.assertIsInstance(result, StoryPipelineResult)
        self.assertEqual(result.total_iterations, 2)
        self.assertEqual(result.initial_score, 19)
        self.assertEqual(result.final_score, 25)
        self.assertEqual(result.score_delta, 6)
        self.assertTrue(result.approved_by_judge)
        self.assertIn("Alice", result.final_story.content)
        self.assertIn("Bob", result.final_story.content)
        self.assertIn("drafting_start", events_logged)
        self.assertIn("judging_start", events_logged)
        self.assertIn("revision_start", events_logged)

    def test_call_model_backwards_compatibility(self):
        """Verify call_model function satisfies starter code interface."""
        resp = call_model("Tell me a quick bedtime story", mock_mode=True)
        self.assertIsInstance(resp, str)
        self.assertGreater(len(resp), 50)


if __name__ == "__main__":
    unittest.main()
