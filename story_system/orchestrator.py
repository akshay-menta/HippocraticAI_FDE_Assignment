"""
Orchestration pipeline connecting User, Storyteller Agent, and LLM Judge.
Implements the iterative feedback and self-correction loop.
"""

import logging
from typing import Callable, List, Optional

from story_system.client import AnthropicStoryClient, get_client
from story_system.judge import LLMJudge
from story_system.models import (
    JudgeEvaluation,
    StoryDraft,
    StoryPipelineResult,
    StoryRequest,
)
from story_system.storyteller import StorytellerAgent

logger = logging.getLogger(__name__)


class BedtimeStoryPipeline:
    """
    End-to-end multi-agent pipeline for generating, judging, and refining bedtime stories.
    """

    def __init__(
        self,
        client: Optional[AnthropicStoryClient] = None,
        mock_mode: bool = False,
    ):
        self.client = client or get_client(mock_mode=mock_mode)
        self.storyteller = StorytellerAgent(client=self.client)
        self.judge = LLMJudge(client=self.client)

    def run(
        self,
        request: StoryRequest,
        max_iterations: int = 2,
        on_step: Optional[Callable[[str, dict], None]] = None,
    ) -> StoryPipelineResult:
        """
        Execute the full pipeline:
        1. Draft initial story
        2. Judge evaluation against 5-point rubric
        3. If criteria not met and iterations remain, revise story addressing judge critique
        4. Re-evaluate and finalize
        """
        history: List[StoryDraft] = []

        def notify(event: str, data: dict):
            if on_step:
                try:
                    on_step(event, data)
                except Exception as e:
                    logger.debug(f"Callback notification error: {e}")

        # -------------------------------------------------------------
        # Iteration 1: Initial Draft
        # -------------------------------------------------------------
        notify("drafting_start", {"iteration": 1, "prompt": request.prompt})
        current_draft = self.storyteller.generate_draft(request)
        notify("drafting_complete", {"iteration": 1, "draft": current_draft})

        # Initial Judge Evaluation
        notify("judging_start", {"iteration": 1, "draft": current_draft})
        evaluation = self.judge.evaluate(
            story_content=current_draft.content,
            target_age=request.target_age,
            user_request=request.prompt,
            iteration=1,
        )
        current_draft.evaluation = evaluation
        history.append(current_draft)
        notify("judging_complete", {"iteration": 1, "evaluation": evaluation})

        initial_score = evaluation.overall_score
        iteration = 1

        # -------------------------------------------------------------
        # Iterative Revision Loop
        # -------------------------------------------------------------
        while not evaluation.approved and iteration < max_iterations:
            iteration += 1
            notify("revision_start", {
                "iteration": iteration,
                "previous_score": evaluation.overall_score,
                "revisions_needed": evaluation.actionable_revisions,
            })

            # Revise story based on Judge's feedback
            revised_draft = self.storyteller.revise_draft(
                previous_draft=current_draft,
                request=request,
                evaluation=evaluation,
                iteration=iteration,
            )
            notify("revision_complete", {"iteration": iteration, "draft": revised_draft})

            # Re-evaluate with Judge
            notify("judging_start", {"iteration": iteration, "draft": revised_draft})
            evaluation = self.judge.evaluate(
                story_content=revised_draft.content,
                target_age=request.target_age,
                user_request=request.prompt,
                iteration=iteration,
            )
            revised_draft.evaluation = evaluation
            history.append(revised_draft)
            current_draft = revised_draft
            notify("judging_complete", {"iteration": iteration, "evaluation": evaluation})

        final_score = current_draft.evaluation.overall_score if current_draft.evaluation else initial_score
        score_delta = final_score - initial_score

        return StoryPipelineResult(
            request=request,
            final_story=current_draft,
            history=history,
            total_iterations=iteration,
            initial_score=initial_score,
            final_score=final_score,
            score_delta=score_delta,
            approved_by_judge=current_draft.evaluation.approved if current_draft.evaluation else False,
        )
