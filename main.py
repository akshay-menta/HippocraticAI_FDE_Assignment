import argparse
import os
import sys
from typing import Optional

# Try to load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

With two additional hours, I would build:
1. Dynamic Audio Narration & Slumber Soundscape (TTS):
   - Integrate ElevenLabs / Edge-TTS to synthesize soothing voice audio with dynamic pacing.
   - Implement tempo deceleration: speech rate gradually slows from ~140 WPM during the gentle adventure to ~95 WPM during the final wind-down, accompanied by an adaptive ambient audio bed (soft rain, gentle harp, nocturnal lullaby).
2. Child Profile Personalization & Continuity Memory:
   - A lightweight persistent vector/SQLite store maintaining child preferences (favorite stuffed animals, siblings' names, fears to avoid like spiders or darkness, and moral themes parents want reinforced).
   - Multi-night story arcs that subtly weave familiar safe anchors across sequential bedtime episodes.
3. Multi-Modal Bedtime Storybook Illustrations:
   - Generate soft-palette, watercolor bedtime illustrations using Flux/SDXL with consistent character seed conditioning to display in an interactive reader interface.
4. Interactive Branching ("Choose-Your-Own-Dream"):
   - Allow the child to make 1-2 gentle, low-stakes decisions early in the story ("Does Alice follow the silver star or check the lavender garden gate?") before the narrative converges into restful sleep.
5. Automated Benchmarking & Quality Evals Suite:
   - An automated regression harness running 50 diverse story requests across age groups (5-6, 7-8, 9-10) measuring Judge-Storyteller convergence rates, token efficiency, latency, and sentiment soothing curves.
"""

from story_system.client import (
    PRIMARY_MODEL,
    AnthropicClientError,
    AnthropicStoryClient,
    call_claude,
    get_client,
)
from story_system.models import StoryRequest
from story_system.orchestrator import BedtimeStoryPipeline
from story_system.ui import (
    print_banner,
    print_final_story,
    print_judge_scorecard,
    print_request_summary,
    print_system_diagram,
)

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def call_model(
    prompt: str,
    max_tokens: int = 3000,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    mock_mode: bool = False,
) -> str:
    """
    Direct model call function replacing the original OpenAI GPT-3.5 Turbo implementation
    with Anthropic's Claude Haiku 5.5 (claude-haiku-5-5).
    
    Reads ANTHROPIC_API_KEY from environment variables.
    """
    client = get_client(mock_mode=mock_mode)
    return client.call(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def build_parser() -> argparse.ArgumentParser:
    """Configure CLI arguments for the story generator."""
    parser = argparse.ArgumentParser(
        description="Bedtime Story Generator with LLM Judge (Powered by Claude Haiku 5.5)"
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        default=None,
        help="Story request prompt. If omitted, will prompt interactively."
    )
    parser.add_argument(
        "--age", "-a",
        type=int,
        default=7,
        help="Target child age between 5 and 10 (default: 7)"
    )
    parser.add_argument(
        "--child", "-c",
        type=str,
        default=None,
        help="Child's name for personalization"
    )
    parser.add_argument(
        "--theme", "-t",
        type=str,
        default=None,
        help="Theme or moral lesson (e.g., 'sharing', 'curiosity', 'bedtime calm')"
    )
    parser.add_argument(
        "--sleepy", "-s",
        type=int,
        default=5,
        choices=[1, 2, 3, 4, 5],
        help="Sleepy wind-down factor (1=lively, 5=extra sleepy lullaby ending, default: 5)"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=2,
        help="Maximum review and refinement iterations with the LLM Judge (default: 2)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline mock demonstration mode (useful for testing without API keys)"
    )
    parser.add_argument(
        "--diagram",
        action="store_true",
        help="Print the system architecture block diagram and exit"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Output only the final story text without scorecard or banners"
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.diagram:
        print_system_diagram()
        return

    # Check for API key if not in mock mode
    api_key = os.getenv("ANTHROPIC_API_KEY")
    mock_mode = args.mock

    if not mock_mode and not api_key:
        # Prompt user or inform them
        print("\n[Notice] ANTHROPIC_API_KEY environment variable is not set.")
        print("To run with live Claude Haiku 5.5, please set:")
        print("    export ANTHROPIC_API_KEY='your_api_key_here'")
        print("Running in demonstration MOCK mode for now...\n")
        mock_mode = True

    # Get story request prompt
    user_input = args.prompt
    if not user_input:
        if not args.simple:
            print_banner()
        try:
            user_input = input(f"What kind of story do you want to hear? [Press Enter for default: '{example_requests}']: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

        if not user_input:
            user_input = example_requests

    # Validate age within 5-10
    target_age = max(5, min(10, args.age))

    request = StoryRequest(
        prompt=user_input,
        target_age=target_age,
        child_name=args.child,
        theme=args.theme,
        sleepy_factor=args.sleepy,
    )

    if not args.simple:
        print_request_summary(request)

    # Initialize the multi-agent pipeline
    pipeline = BedtimeStoryPipeline(mock_mode=mock_mode)

    try:
        # Callback to print step progress in real time
        def on_step_callback(event: str, data: dict):
            if args.simple:
                return
            if event == "drafting_start":
                print(f"Storyteller is composing initial draft for age {target_age}...")
            elif event == "judging_start":
                print(f"LLM Judge is evaluating draft against 5-point child literature rubric...")
            elif event == "judging_complete":
                evaluation = data.get("evaluation")
                if evaluation:
                    print_judge_scorecard(evaluation, iteration=data.get("iteration", 1))
            elif event == "revision_start":
                print(f"Revision Loop: Storyteller is refining story to address Judge directives...")

        result = pipeline.run(
            request=request,
            max_iterations=args.iterations,
            on_step=on_step_callback,
        )

        # Display final story
        if args.simple:
            print(result.final_story.content)
        else:
            print_final_story(result)

    except AnthropicClientError as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[Unexpected Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()