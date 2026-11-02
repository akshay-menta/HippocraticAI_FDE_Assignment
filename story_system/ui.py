"""
User interface and visualization module for the Bedtime Story System.
Provides formatted terminal display using 'rich' with clean fallback formatting.
"""

from typing import List, Optional
from story_system.models import JudgeEvaluation, StoryDraft, StoryPipelineResult, StoryRequest

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def print_banner():
    """Print the bedtime story system welcome banner."""
    if RICH_AVAILABLE:
        banner_text = Text()
        banner_text.append("BEDTIME STORYTELLER & LLM JUDGE \n", style="bold cyan")
        banner_text.append("Powered by Anthropic Claude Haiku 5.5 | Tailored for Ages 5–10", style="dim italic")
        console.print(Panel(banner_text, border_style="cyan", box=box.ROUNDED))
    else:
        print("\n" + "=" * 65)
        print("BEDTIME STORYTELLER & LLM JUDGE")
        print("Powered by Anthropic Claude Haiku 5.5 | Tailored for Ages 5–10")
        print("=" * 65 + "\n")


def print_request_summary(request: StoryRequest):
    """Print a summary of the story generation parameters."""
    if RICH_AVAILABLE:
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Key", style="bold yellow")
        table.add_column("Value", style="white")

        table.add_row("Story Request:", f'"{request.prompt}"')
        table.add_row("Target Audience:", f"Age {request.target_age} ({request.age_group})")
        if request.child_name:
            table.add_row("Child Name:", request.child_name)
        if request.theme:
            table.add_row("Theme / Lesson:", request.theme)
        table.add_row("Sleepy Wind-down:", f"{' ' * request.sleepy_factor} ({request.sleepy_factor}/5)")

        console.print(Panel(table, title="[bold]Bedtime Configuration[/bold]", border_style="blue", box=box.ROUNDED))
    else:
        print(f"Request: \"{request.prompt}\"")
        print(f"Target Age: {request.target_age} ({request.age_group})")
        if request.child_name:
            print(f"Child Name: {request.child_name}")
        if request.theme:
            print(f"Theme: {request.theme}")
        print(f"Sleepy Wind-down: {request.sleepy_factor}/5\n")


def print_judge_scorecard(evaluation: JudgeEvaluation, iteration: int = 1):
    """Print a structured scorecard showing the LLM Judge's multi-rubric evaluation."""
    if RICH_AVAILABLE:
        status_color = "green" if evaluation.approved else "yellow"
        approval_badge = "[bold green]✓ APPROVED[/bold green]" if evaluation.approved else "[bold yellow]⚠ REVISION REQUESTED[/bold yellow]"
        
        table = Table(box=box.ROUNDED, expand=True)
        table.add_column("Rubric Dimension", style="bold cyan", width=30)
        table.add_column("Score", justify="center", width=12)
        table.add_column("Judge Rationale & Observations", style="white")

        for key, rubric in evaluation.rubric_scores.items():
            stars = "★" * rubric.score + "☆" * (rubric.max_score - rubric.score)
            score_style = "green" if rubric.score >= 4 else ("yellow" if rubric.score == 3 else "red")
            table.add_row(
                rubric.name,
                f"[{score_style}]{stars} {rubric.score}/5[/{score_style}]",
                rubric.rationale or "—"
            )

        console.print(table)

        # Strengths & Actionable Critique
        summary_panel_text = Text()
        summary_panel_text.append(f"Overall Score: {evaluation.overall_score}/25 ({approval_badge}) | Atmosphere: {evaluation.calm_factor_rating}\n\n", style="bold")
        
        if evaluation.strengths:
            summary_panel_text.append("Strengths:\n", style="bold green")
            for s in evaluation.strengths:
                summary_panel_text.append(f"  • {s}\n", style="white")
            summary_panel_text.append("\n")

        if evaluation.actionable_revisions:
            summary_panel_text.append("🛠️ Judge's Actionable Directives for Revision:\n", style="bold yellow")
            for a in evaluation.actionable_revisions:
                summary_panel_text.append(f"  • {a}\n", style="white")

        console.print(Panel(
            summary_panel_text,
            title=f"[bold]LLM Judge Evaluation (Iteration {iteration})[/bold]",
            border_style=status_color,
            box=box.ROUNDED,
        ))
    else:
        print(f"\n--- LLM Judge Evaluation (Iteration {iteration}) ---")
        print(f"Overall Score: {evaluation.overall_score}/25 | Approved: {evaluation.approved}")
        print(f"Calm Factor: {evaluation.calm_factor_rating}")
        print("\nScores by Rubric Dimension:")
        for key, rubric in evaluation.rubric_scores.items():
            print(f"  - {rubric.name}: {rubric.score}/5 — {rubric.rationale}")
        
        if evaluation.strengths:
            print("\nStrengths:")
            for s in evaluation.strengths:
                print(f"  + {s}")
        if evaluation.actionable_revisions:
            print("\nActionable Revisions:")
            for a in evaluation.actionable_revisions:
                print(f"  * {a}")
        print("--------------------------------------------------\n")


def print_final_story(result: StoryPipelineResult):
    """Print the final approved bedtime story in a presentation format."""
    story = result.final_story

    if RICH_AVAILABLE:
        story_text = Text()
        story_text.append(story.content)
        
        metadata_footer = (
            f"\n\n[dim]📖 {story.word_count} words | "
            f"⏱️ ~{story.estimated_read_time_minutes} min read aloud | "
            f"Target Age: {result.request.target_age} | "
            f"Quality Score: {result.final_score}/25"
        )
        if result.score_delta > 0:
            metadata_footer += f" (+{result.score_delta} from judge revision)[/dim]"
        else:
            metadata_footer += "[/dim]"

        story_text.append(metadata_footer)

        console.print(Panel(
            story_text,
            title=f"[bold gold1]✨ {story.title} ✨[/bold gold1]",
            subtitle="[dim]🌙 Ready for bedtime tuck-in[/dim]",
            border_style="purple",
            box=box.DOUBLE,
            padding=(1, 2)
        ))
    else:
        print("\n" + "=" * 65)
        print(f"✨ {story.title} ✨")
        print("=" * 65 + "\n")
        print(story.content)
        print("\n" + "-" * 65)
        print(f"Words: {story.word_count} | Reading Time: ~{story.estimated_read_time_minutes} mins | Quality: {result.final_score}/25 (Delta: +{result.score_delta})")
        print("=" * 65 + "\n")


def print_system_diagram():
    """Print the system architecture block diagram in ASCII art."""
    diagram = """
+----------------------------------------------------------------------------------------------------+
|                                  BEDTIME STORY AGENT ARCHITECTURE                                  |
+----------------------------------------------------------------------------------------------------+

                   +--------------------------+
                   |       USER / PARENT      |
                   | (Story Request, Age 5-10)|
                   +-------------+------------+
                                 |
                                 v
        +----------------------------------------------------+
        |         STORY PIPELINE ORCHESTRATOR                |
        |  - Coordinates Request, Storyteller, and Judge     |
        |  - Manages feedback loop & iteration budget        |
        +-------+------------------------------------+-------+
                |                                    ^
                | [User Prompt & Age Specs]          | [Structured Critique & Rubric Scores]
                v                                    |
   +---------------------------+            +----------------------------+
   |     STORYTELLER AGENT     |            |       LLM JUDGE AGENT      |
   | (Anthropic Claude Haiku)  |            |   (Anthropic Claude Haiku) |
   |                           |            |                            |
   | - System Prompt:          |            | - System Prompt:           |
   |   * 4-Act Slumber Arc     |            |   * 5-Dimension Rubric     |
   |   * Sensory deceleration  |            |   * Child literature expert|
   |   * Age-graded vocabulary |            |   * Pacing & safety tester |
   |                           |            |                            |
   | - Actions:                |            | - Output:                  |
   |   1. Generate draft       |            |   1. 5 Rubric Scores (1-5) |
   |   2. Revise with critique |            |   2. Qualitative Strengths |
   +-------------+-------------+            |   3. Actionable Directives |
                 |                          |   4. Approval Status (>=21)|
                 | [Story Draft]            +--------------+-------------+
                 v                                         ^
          +---------------+                                |
          |  Story Draft  +--------------------------------+
          +-------+-------+
                  |
                  | If Approved or Max Iterations Reached
                  v
   +---------------------------------------------------------------------+
   |                      FINAL POLISHED STORY                           |
   |  - Age-appropriate wonder (Ages 5-10)                               |
   |  - Calming, sleepy sensory lullaby wind-down                        |
   |  - Scorecard & reading time metrics (~5-8 mins)                     |
   +---------------------------------------------------------------------+
"""
    if RICH_AVAILABLE:
        console.print(Panel(Text(diagram, style="bold cyan"), title="System Flow & Block Diagram", box=box.ROUNDED))
    else:
        print(diagram)
