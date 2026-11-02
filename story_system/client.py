"""
Anthropic API client integration for Claude Haiku 5.5 (claude-haiku-5-5).
Handles API key retrieval, model fallbacks, error handling, and mock mode for testing.
"""

import json
import os
import re
import sys
from typing import Optional

# Attempt to load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Primary requested model as specified in the assignment prompt
PRIMARY_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
FALLBACK_MODELS = ["claude-3-5-haiku-20241022", "claude-3-5-haiku-latest"]


class AnthropicClientError(Exception):
    """Raised when an Anthropic API call fails."""
    pass


class AnthropicStoryClient:
    """
    Wrapper around the Anthropic Messages API.
    Designed for reliability, clear diagnostics, and graceful fallback.
    """

    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.mock_mode = mock_mode or os.getenv("MOCK_ANTHROPIC", "").lower() in ("1", "true", "yes")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = PRIMARY_MODEL
        self._client = None

        if not self.mock_mode:
            if not self.api_key:
                # We will check if the user passes it later, but warn now
                pass
            else:
                try:
                    import anthropic
                    self._client = anthropic.Anthropic(api_key=self.api_key)
                except Exception as e:
                    raise AnthropicClientError(f"Failed to initialize Anthropic client: {e}")

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 3000,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> str:
        """
        Execute a call to Claude Haiku 5.5.
        Falls back to claude-3-5-haiku-20241022 if the endpoint reports the model name as not found.
        """
        if self.mock_mode:
            return self._mock_call(prompt, system_prompt)

        if not self.api_key:
            raise AnthropicClientError(
                "ANTHROPIC_API_KEY environment variable is not set.\n"
                "Please set your Anthropic API key:\n"
                "  export ANTHROPIC_API_KEY='your-key-here'\n"
                "Or add ANTHROPIC_API_KEY=your-key-here to a .env file.\n"
                "To run a demonstration in mock mode, pass --mock."
            )

        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)

        import anthropic

        target_model = model or self.model
        models_to_try = [target_model] + [m for m in FALLBACK_MODELS if m != target_model]

        last_error = None
        for current_model in models_to_try:
            try:
                kwargs = {
                    "model": current_model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system_prompt:
                    kwargs["system"] = system_prompt

                response = self._client.messages.create(**kwargs)
                # Successful call
                text_content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text_content += block.text
                return text_content.strip()

            except anthropic.NotFoundError as e:
                # If claude-haiku-5-5 is an alias not yet recognized by this specific endpoint,
                # seamlessly try the verified 3.5 haiku fallback
                last_error = e
                continue
            except anthropic.BadRequestError as e:
                if "model" in str(e).lower():
                    last_error = e
                    continue
                raise AnthropicClientError(f"Anthropic API bad request: {e}")
            except Exception as e:
                raise AnthropicClientError(f"Anthropic API error with model {current_model}: {e}")

        raise AnthropicClientError(
            f"Failed to call Anthropic models ({models_to_try}). Last error: {last_error}"
        )

    def _mock_call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """High quality deterministic mock responses for testing and offline demos."""
        # Detect if this is a Judge evaluation request (asking for JSON evaluation)
        if system_prompt and "judge" in system_prompt.lower():
            # Check if this is evaluating an already revised story or initial draft
            is_revision = (
                "iteration 2" in prompt.lower()
                or "revised" in prompt.lower()
                or "whispering star" in prompt.lower()
                or "star-pebble" in prompt.lower()
            )
            if is_revision:
                return json.dumps({
                    "rubric_scores": {
                        "age_appropriateness": {
                            "score": 5,
                            "rationale": "Vocabulary and sentence rhythms are ideally calibrated for ages 5-10, blending engaging dialogue with cozy simplicity."
                        },
                        "bedtime_wind_down": {
                            "score": 5,
                            "rationale": "Flawless transition into slumber. The pacing slows down, sensory cues (soft purring, twilight stars, deep breaths) induce sleep."
                        },
                        "narrative_arc": {
                            "score": 5,
                            "rationale": "Clear four-act structure: cozy intro, curious spark, gentle heartwarming resolution, and soothing bedtime tuck-in."
                        },
                        "language_whimsy": {
                            "score": 5,
                            "rationale": "Delightful sensory language with soft onomatopoeia and warm rhythmic phrasing that sounds wonderful read aloud."
                        },
                        "emotional_safety": {
                            "score": 5,
                            "rationale": "Deeply comforting, modeling unconditional friendship, safety, kindness, and bedtime security."
                        }
                    },
                    "overall_score": 25,
                    "approved": True,
                    "calm_factor_rating": "Perfect Bedtime Slumber",
                    "strengths": [
                        "Exquisite bedtime wind-down rhythm that gradually slows reading pace",
                        "Endearing character dynamics that feel safe and reassuring",
                        "Vivid sensory details of warmth, sleepy purring, and twilight stars"
                    ],
                    "critique": [
                        "The story now meets and exceeds all publication quality standards."
                    ],
                    "actionable_revisions": [
                        "Ready for bedtime reading aloud."
                    ],
                    "summary": "An exceptional, heartwarming bedtime story with a gentle arc and an exquisitely soothing slumber conclusion."
                }, indent=2)
            else:
                # Initial draft evaluation - constructive critique requiring revision
                return json.dumps({
                    "rubric_scores": {
                        "age_appropriateness": {
                            "score": 4,
                            "rationale": "Well-tailored for 7-year-olds, though a few sentences could have more soothing read-aloud cadence."
                        },
                        "bedtime_wind_down": {
                            "score": 3,
                            "rationale": "The ending resolves well, but the transition into deep bedtime sleep could be slower, warmer, and more sensory."
                        },
                        "narrative_arc": {
                            "score": 4,
                            "rationale": "Good flow, but the middle adventure could feel slightly more focused on gentle curiosity rather than sudden movement."
                        },
                        "language_whimsy": {
                            "score": 4,
                            "rationale": "Charming dialogue, but could benefit from more rhythmic sensory words (soft thumps, quiet purrs, fading twilight)."
                        },
                        "emotional_safety": {
                            "score": 4,
                            "rationale": "Very safe and sweet, with zero scary elements."
                        }
                    },
                    "overall_score": 19,
                    "approved": False,
                    "calm_factor_rating": "Gentle but needs Sleepy Wind-down",
                    "strengths": [
                        "Lovely warmth between the characters",
                        "Completely free of any frightening or overstimulating tropes"
                    ],
                    "critique": [
                        "The bedtime transition happens too abruptly; needs more sensory deceleration",
                        "Needs stronger tactile and auditory slumber cues (yawning, breathing, soft blankets)"
                    ],
                    "actionable_revisions": [
                        "Expand the final two paragraphs to decelerate the tempo from playful to drowsy",
                        "Add sensory cues of tucking in, soft purrs, heavy eyelids, and peaceful breathing",
                        "Emphasize the feeling of being safe, warm, and ready for sweet dreams"
                    ],
                    "summary": "A delightful foundation that needs a more pronounced, soothing bedtime wind-down arc to help the child drift to sleep."
                }, indent=2)

        # Revision request
        if "critique" in prompt.lower() or "revision" in prompt.lower():
            return (
                "# The Whispering Star and Bob's Cozy Dream\n\n"
                "Once upon a quiet twilight, in a yellow house with a garden of lavender, "
                "lived a seven-year-old girl named Alice and her best friend, Bob. Bob was not an ordinary friend—he was a round, "
                "fluffy orange cat with whiskers that twitched whenever an idea tickled his head.\n\n"
                "Tonight, the sky was turning the color of deep blueberry pie. Through the bedroom window, "
                "a tiny silver star blinked awake. 'Look, Bob,' Alice whispered, leaning against the windowsill. "
                "'The first star of the evening.' Bob answered with a soft *mrrow-purr*, rubbing his warm cheek against her wrist.\n\n"
                "Suddenly, a tiny silver sparkle tumbled gently through the open breeze and landed right on Alice's windowsill! "
                "It was a fallen Star-Pebble, glowing with a soft, warm lemon light. 'Oh!' whispered Alice. 'Are you lost, little light?' "
                "Bob crept forward, his soft white paws making not a single sound. He touched the pebble with the tip of his wet pink nose. "
                "The pebble gave a gentle chime, like a silver bell wrapped in wool.\n\n"
                "Together, Alice and Bob knew just what to do. With gentle hands, Alice placed the Star-Pebble into Bob's cozy woven basket. "
                "'Let's sing it a lullaby so it can float back home,' Alice suggested. She hummed a sweet, slow tune that her grandmother "
                "once sang. Bob joined in with the deepest, steadiest purr a cat could muster: *rum-rum-rum-rum*.\n\n"
                "As the lullaby filled the quiet room, the Star-Pebble grew light as a dandelion seed. It rose into the cool evening air, "
                "glided softly out the window, and nestled back into the dark velvet sky with a grateful golden wink. The sky was now calm and still.\n\n"
                "Alice felt a big, sleepy yawn stretch across her face. Bob stretched his front paws, stretched his back paws, and let out "
                "a sleepy kitty yawn of his own. Alice climbed under her warm quilt, smooth and cool like a cloud. Bob curled into a furry circle "
                "right beside her pillow, his rhythmic purr humming like a gentle train in the distance.\n\n"
                "Outside, the stars watched over the house. Inside, Alice's eyelids grew pleasantly heavy. One slow breath in... and one slow breath out. "
                "'Goodnight, Bob,' Alice murmured. Bob gave a tiny tail flick, sighed a contented sigh, and together they drifted away into sweet, safe dreams."
            )

        # Initial Story draft
        return (
            "# Alice and Bob's Bedtime Adventure\n\n"
            "Once upon a time, in a cozy bedroom with starry wallpaper, lived a girl named Alice and her best friend, Bob. "
            "Bob was a cat with emerald eyes and ginger fur who loved to chase dust motes.\n\n"
            "One evening before bedtime, Bob nudged Alice's slippers. He had spotted a tiny golden moth fluttering near the lamp. "
            "'Quiet, Bob,' Alice giggled. 'It's almost time to sleep.' But Bob patted the rug with a playful paw. "
            "Alice followed Bob under the reading tent made of blankets.\n\n"
            "Inside the tent, the shadows looked like a fairy forest. The golden moth landed softly on an open storybook. "
            "'It's showing us the picture of the Moon Castle,' Alice said. Bob purred and rested his head on Alice's knee. "
            "The moth fluttered out the open window into the cool night air.\n\n"
            "Alice yawned and climbed into bed. Bob jumped up and curled at her feet. "
            "'Goodnight Bob,' said Alice. 'Goodnight Alice,' purred Bob, and they went to sleep."
        )


# Global singleton instance for convenient access
_default_client: Optional[AnthropicStoryClient] = None


def get_client(mock_mode: bool = False) -> AnthropicStoryClient:
    """Retrieve or create the global AnthropicStoryClient instance."""
    global _default_client
    if _default_client is None or _default_client.mock_mode != mock_mode:
        _default_client = AnthropicStoryClient(mock_mode=mock_mode)
    return _default_client


def call_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 3000,
    temperature: float = 0.7,
    mock_mode: bool = False,
) -> str:
    """Helper function to call Claude Haiku 5.5."""
    client = get_client(mock_mode=mock_mode)
    return client.call(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
