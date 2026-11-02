"""
Storyteller Agent module for generating and iteratively revising bedtime stories.
"""

import re
from typing import Optional

from story_system.client import AnthropicStoryClient, get_client
from story_system.models import JudgeEvaluation, StoryDraft, StoryRequest
from story_system.prompts import (
    STORYTELLER_SYSTEM_PROMPT,
    build_revision_prompt,
    build_storyteller_prompt,
)


class StorytellerAgent:
    """
    Expert children's storyteller agent that produces initial bedtime stories
    and refines them in response to structured feedback from the LLM Judge.
    """

    def __init__(self, client: Optional[AnthropicStoryClient] = None, mock_mode: bool = False):
        self.client = client or get_client(mock_mode=mock_mode)

    def generate_draft(self, request: StoryRequest) -> StoryDraft:
        """Generate the first draft of the bedtime story based on user request."""
        prompt = build_storyteller_prompt(
            user_prompt=request.prompt,
            target_age=request.target_age,
            child_name=request.child_name,
            theme=request.theme,
            sleepy_factor=request.sleepy_factor,
        )

        raw_story = self.client.call(
            prompt=prompt,
            system_prompt=STORYTELLER_SYSTEM_PROMPT,
            temperature=0.75,  # Balanced creativity and coherence
        )

        title, content = self._extract_title_and_content(raw_story)

        return StoryDraft(
            iteration=1,
            title=title,
            content=content,
        )

    def revise_draft(
        self,
        previous_draft: StoryDraft,
        request: StoryRequest,
        evaluation: JudgeEvaluation,
        iteration: int = 2,
    ) -> StoryDraft:
        """Revise an existing draft based on detailed feedback from the LLM Judge."""
        # Convert evaluation to dict format for prompt builder
        judge_dict = {
            "overall_score": evaluation.overall_score,
            "rubric_scores": {
                k: {"score": v.score, "rationale": v.rationale}
                for k, v in evaluation.rubric_scores.items()
            },
            "strengths": evaluation.strengths,
            "critique": evaluation.critique,
            "actionable_revisions": evaluation.actionable_revisions,
        }

        prompt = build_revision_prompt(
            original_story=previous_draft.content,
            user_request=request.prompt,
            target_age=request.target_age,
            judge_feedback=judge_dict,
        )

        revised_raw = self.client.call(
            prompt=prompt,
            system_prompt=STORYTELLER_SYSTEM_PROMPT,
            temperature=0.65,  # Slightly lower temperature to focus on precision revision
        )

        title, content = self._extract_title_and_content(revised_raw, default_title=previous_draft.title)

        return StoryDraft(
            iteration=iteration,
            title=title,
            content=content,
        )

    def _extract_title_and_content(self, raw_text: str, default_title: str = "A Bedtime Story") -> tuple[str, str]:
        """Extract markdown # title if present, otherwise generate a sensible title."""
        lines = raw_text.strip().split("\n")
        title = default_title
        content_lines = []

        found_title = False
        for line in lines:
            if not found_title and line.startswith("# "):
                title = line.replace("# ", "").strip().strip('"').strip("*")
                found_title = True
            elif not found_title and line.startswith("Title:"):
                title = line.replace("Title:", "").strip().strip('"').strip("*")
                found_title = True
            else:
                content_lines.append(line)

        content = "\n".join(content_lines).strip()
        if not content:
            content = raw_text.strip()

        return title, content
