# Bedtime Storyteller & LLM Judge Agent System
### Powered by Anthropic Claude Haiku 5.5 (`claude-haiku-5-5`) | Tailored for Children Ages 5–10

An agentic bedtime story generation system that transforms simple bedtime story requests into age-appropriate, soothing tales for children ages 5 to 10. The system features a specialized **Storyteller Agent**, an expert **LLM Judge** with an explicit 5-dimension rubric, and an **iterative reflection loop** that refines stories to ensure both imaginative engagement and peaceful bedtime sleep induction.

---

## 📑 Table of Contents
1. [Architecture & Block Diagram](#-architecture--block-diagram)
2. [Key Features & Agent Design](#-key-features--agent-design)
3. [The LLM Judge & Rubric](#-the-llm-judge--rubric)
4. [Prompt Engineering Strategy](#-prompt-engineering-strategy)
5. [Installation & Setup](#-installation--setup)
6. [How to Run](#-how-to-run)
7. [Running Tests](#-running-tests)
8. [What I Would Build Next (With 2 Additional Hours)](#-what-i-would-build-next-with-2-additional-hours)

---

### Component Flow

```
+---------------------------------------------------------------------------------------------------+
|                                 BEDTIME STORY AGENT ARCHITECTURE                                  |
+---------------------------------------------------------------------------------------------------+

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
```

---

## Key Features & Agent Design

1. **Claude Haiku 5.5 Integration**: Uses Anthropic's `claude-haiku-5-5` with smart alias fallback to `claude-3-5-haiku-20241022` to ensure rock-solid compatibility across any Anthropic API gateway.
2. **Child Developmental Psychology Awareness (Ages 5–10)**:
   - **Ages 5–6 (Early Childhood)**: Concrete sensory rhythms, repetition, familiar comforting routines, soft onomatopoeia.
   - **Ages 7–8 (Mid Childhood)**: Playful curiosity, lighthearted humor, gentle cooperation, relatable childhood wonder.
   - **Ages 9–10 (Upper Childhood)**: Richer descriptive metaphors, clever problem-solving, and emotional warmth.
3. **The 4-Stage Bedtime Slumber Arc**:
   Unlike conventional adventure stories that escalate toward an exhilarating climax, bedtime stories must guide a child toward sleep:
   - *Act 1: The Cozy Welcome* (safety, familiar anchors, endearing characters)
   - *Act 2: The Spark of Wonder* (mild, curious adventure with ZERO fear or anxiety)
   - *Act 3: The Heartwarming Resolution* (kindness, sharing, cooperative ingenuity)
   - *Act 4: The Slumber Descent* (narrative deceleration, slow reading cadence, sensory sleep cues: yawning, dimming starlight, deep breaths, cozy blankets, drifting into sweet dreams)
4. **LLM Judge Quality Feedback Loop**:
   - The Judge assesses the draft against an explicit 5-point rubric (Total 25 points).
   - If the story does not score $\ge 21/25$ with a Bedtime Wind-Down score of $\ge 4/5$, the Judge issues **actionable, prioritized revision instructions**.
   - The Storyteller receives the critique and rewrites the story to target those specific shortcomings while preserving approved elements.
5. **Rich Terminal Interface & Metrics**:
   - Beautiful terminal display using `rich` (with clean ANSI fallback).
   - Word count, oral reading time estimate (at 125 words per minute), and quality improvement delta (+X points from judge feedback).

---

## The LLM Judge & Rubric

The LLM Judge evaluates every draft across **5 distinct dimensions** (1–5 points each; Total: 25 points):

| Dimension | Weight | Target Criteria for 5/5 |
| :--- | :---: | :--- |
| **1. Age Appropriateness & Vocabulary** | 5 pts | Calibrated for 5–10 year olds; accessible, rich, free of dense academic jargon or babyish condescension. |
| **2. Bedtime Wind-Down & Slumber Arc** | 5 pts | Decelerates narrative tempo in the final 25%; weaves in rich sensory sleep cues (yawns, twilight, soft breathing, heavy eyelids). |
| **3. Narrative Arc & Engagement** | 5 pts | Classical 4-act bedtime structure (Welcome -> Spark of Wonder -> Heartwarming Resolution -> Slumber Descent). |
| **4. Language, Rhythm & Sensory Whimsy** | 5 pts | Lyrical, musical cadence that rolls off the tongue; rich with auditory and tactile warmth; delightful to read aloud. |
| **5. Emotional Safety & Warmth** | 5 pts | Zero scary elements or unresolved anxiety; models kindness, empathy, and safe emotional security. |

### Approval Threshold:
- Overall Score $\ge 21 / 25$
- No single category score $< 4$
- Bedtime Wind-Down score **must** be $\ge 4$

---

## Installation & Setup

### 1. Requirements
- Python 3.9+
- Anthropic Python SDK (`pip install anthropic`)
- Optional formatting dependencies: `rich`, `python-dotenv`

```bash
pip install anthropic rich python-dotenv
```

### 2. Configure Your Anthropic API Key
Set your API key in your environment:
```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```
Or create a `.env` file in the project root (a template `.env.example` is provided):
```bash
cp .env.example .env
# Edit .env and insert your ANTHROPIC_API_KEY
```
*(Note: `.env` is included in `.gitignore` to prevent any keys from being committed).*

---

## How to Run

### Interactive Mode (Standard CLI)
Matches the original starter code interface:
```bash
python3 main.py
```
You will be prompted:
```text
What kind of story do you want to hear? [Press Enter for default: 'A story about a girl named Alice and her best friend Bob, who happens to be a cat.']:
```

### CLI Flags & Customization
You can pass custom parameters directly:
```bash
# Custom prompt and age
python3 main.py -p "A little otter named Pip who wanted to count the stars" --age 6

# With child's name and theme
python3 main.py -p "A dragon who was afraid of the dark" --age 8 --child "Maya" --theme "courage & friendship"

# Offline Mock Demonstration Mode (runs without an API key)
python3 main.py --mock

# Display Architecture Block Diagram
python3 main.py --diagram

# Minimalist output (prints only story text)
python3 main.py -p "Alice and Bob" --simple
```

---

## Running Tests

A comprehensive suite of unit tests is included using Python's standard library `unittest` (zero external test runner dependencies):

```bash
python3 -m unittest discover tests
```

Tests cover:
- StoryRequest age-group classification and parameters
- StoryDraft oral reading time calculation (~125 WPM)
- Anthropic client mock mode & fallback handling
- LLM Judge JSON parsing, markdown stripping, and corrupted response fallback
- LLM Judge approval threshold logic (preventing false approvals if wind-down is low)
- Storyteller title & markdown extraction
- BedtimeStoryPipeline multi-agent iteration loop and score delta progression
- `call_model()` backwards compatibility

---

## What I Would Build Next (With 2 Additional Hours)

*Note: This response is also documented directly in `main.py` lines 12–32 as requested.*

With two additional hours, I would build:

1. **Dynamic Audio Narration & Slumber Soundscape (TTS)**:
   - Integrate ElevenLabs / Edge-TTS to synthesize soothing voice audio with dynamic pacing.
   - Implement tempo deceleration: speech rate gradually slows from ~140 WPM during the gentle adventure to ~95 WPM during the final wind-down, accompanied by an adaptive ambient audio bed (soft rain, gentle harp, nocturnal lullaby).
2. **Child Profile Personalization & Continuity Memory**:
   - A lightweight persistent vector/SQLite store maintaining child preferences (favorite stuffed animals, siblings' names, fears to avoid like spiders or darkness, and moral themes parents want reinforced).
   - Multi-night story arcs that subtly weave familiar safe anchors across sequential bedtime episodes.
3. **Multi-Modal Bedtime Storybook Illustrations**:
   - Generate soft-palette, watercolor bedtime illustrations using Flux/SDXL with consistent character seed conditioning to display in an interactive reader interface.
4. **Interactive Branching ("Choose-Your-Own-Dream")**:
   - Allow the child to make 1-2 gentle, low-stakes decisions early in the story ("Does Alice follow the silver star or check the lavender garden gate?") before the narrative converges into restful sleep.
5. **Automated Benchmarking & Quality Evals Suite**:
   - An automated regression harness running 50 diverse story requests across age groups (5-6, 7-8, 9-10) measuring Judge-Storyteller convergence rates, token efficiency, latency, and sentiment soothing curves.
