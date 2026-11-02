"""
Data models for the Bedtime Story Generation & LLM Judge System.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StoryRequest:
    """User request and parameters for generating a bedtime story."""
    prompt: str
    target_age: int = 7
    child_name: Optional[str] = None
    theme: Optional[str] = None
    sleepy_factor: int = 5  # 1 (lively) to 5 (extra sleepy lullaby ending)

    @property
    def age_group(self) -> str:
        if self.target_age <= 6:
            return "Early Childhood (Ages 5-6): Focus on sensory rhythm, repetitive comfort, familiar routines"
        elif self.target_age <= 8:
            return "Mid Childhood (Ages 7-8): Gentle curiosity, playful humor, light problem solving"
        else:
            return "Upper Childhood (Ages 9-10): Richer vocabulary, clever ingenuity, deeper empathy"


@dataclass
class RubricScore:
    """Individual rubric criterion score and evaluation rationale."""
    name: str
    score: int  # 1 to 5
    max_score: int = 5
    rationale: str = ""

    @property
    def percentage(self) -> float:
        return (self.score / self.max_score) * 100


@dataclass
class JudgeEvaluation:
    """Comprehensive evaluation report from the LLM Judge."""
    overall_score: int
    max_score: int = 25
    rubric_scores: Dict[str, RubricScore] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    critique: List[str] = field(default_factory=list)
    actionable_revisions: List[str] = field(default_factory=list)
    approved: bool = False
    calm_factor_rating: str = "Sleepy & Cozy"
    summary: str = ""

    @property
    def percentage(self) -> float:
        return (self.overall_score / self.max_score) * 100


@dataclass
class StoryDraft:
    """A generated or revised story draft along with metadata and evaluation."""
    iteration: int
    title: str
    content: str
    word_count: int = 0
    estimated_read_time_minutes: float = 0.0
    evaluation: Optional[JudgeEvaluation] = None

    def __post_init__(self):
        if not self.word_count and self.content:
            self.word_count = len(self.content.split())
        if not self.estimated_read_time_minutes and self.word_count:
            # Bedtime oral reading speed is approximately 120-130 words per minute
            self.estimated_read_time_minutes = round(self.word_count / 125.0, 1)


@dataclass
class StoryPipelineResult:
    """Final result of the story generation and judge review loop."""
    request: StoryRequest
    final_story: StoryDraft
    history: List[StoryDraft] = field(default_factory=list)
    total_iterations: int = 1
    initial_score: int = 0
    final_score: int = 0
    score_delta: int = 0
    approved_by_judge: bool = False
