# System Architecture & Component Flow Diagram

This document details the multi-agent architecture, prompt flow, and feedback loops of the Bedtime Storyteller & LLM Judge System.

---

## Block Diagram

```
+-----------------------------------------------------------------------------------------------------------------+
|                                         BEDTIME STORY AGENT ARCHITECTURE                                        |
+-----------------------------------------------------------------------------------------------------------------+

                                              +-----------------------+
                                              |     USER / PARENT     |
                                              | - Bedtime Prompt      |
                                              | - Target Age (5-10)   |
                                              | - Theme / Child Name  |
                                              +-----------+-----------+
                                                          |
                                                          v
                       +------------------------------------------------------------------+
                       |                   BEDTIME PIPELINE ORCHESTRATOR                  |
                       | - Coordinates agent communication & iteration budgets            |
                       | - Enforces business logic (e.g. approval thresholds)             |
                       | - Aggregates quality deltas (Initial vs Final score)             |
                       +----------------+--------------------------------+----------------+
                                        |                                ^
                                        |                                |
        [Initial Request / Parameters]  |                                | [Actionable Critique & Scores]
                                        v                                |
     +----------------------------------------------------+              |
     |                 STORYTELLER AGENT                  |              |
     |         (Anthropic Claude Haiku 5.5)               |              |
     |                                                    |              |
     | System Prompt Injections:                          |              |
     | 1. Developmental Psychology for Ages 5-10          |              |
     |    - Ages 5-6: Repetition, concrete, sensory rhythm|              |
     |    - Ages 7-8: Gentle curiosity, subtle humor      |              |
     |    - Ages 9-10: Evocative nuance, gentle ingenuity |              |
     | 2. The 4-Stage Bedtime Slumber Arc:                |              |
     |    * Act 1: The Cozy Welcome (safety & intro)      |              |
     |    * Act 2: Spark of Wonder (low-stakes curiosity) |              |
     |    * Act 3: Heartwarming Resolution (empathy)      |              |
     |    * Act 4: Slumber Descent (tempo deceleration,   |              |
     |             sleepy sensory cues: yawning, purring, |              |
     |             deep breaths, dimming starlight)       |              |
     +-------------------------+--------------------------+              |
                               |                                         |
                               | Generates                               |
                               v                                         |
                       +---------------+                                 |
                       |  Story Draft  +---------------------------------+
                       +-------+-------+                                 |
                               |                                         |
                               | Evaluates                               |
                               v                                         |
     +----------------------------------------------------+              |
     |                   LLM JUDGE AGENT                  |              |
     |            (Anthropic Claude Haiku 5.5)            |              |
     |                                                    |              |
     | System Prompt Injections:                          |              |
     | - Expert Persona: Children's Editor & Sleep Coach  |              |
     | - 5-Dimension Rubric (Scored 1 to 5):              |              |
     |   1. Age Appropriateness & Vocabulary              |              |
     |   2. Bedtime Wind-Down & Slumber Deceleration      |              |
     |   3. Narrative Arc & Engagement                    |              |
     |   4. Language, Rhythm & Sensory Whimsy             |              |
     |   5. Emotional Safety & Warmth (zero fear/anxiety) |              |
     |                                                    |              |
     | Output JSON Schema:                                |              |
     | - rubric_scores: { [dim]: { score, rationale } }   |              |
     | - overall_score: 5 to 25                           |              |
     | - approved: bool (Score >= 21 & Wind-Down >= 4)    |              |
     | - strengths: [ ... ]                               |              |
     | - critique: [ ... ]                                |              |
     | - actionable_revisions: [ prioritized steps ]      +--------------+
     +-------------------------+--------------------------+
                               |
                               | If Approved (Score >= 21) OR Max Iterations Reached
                               v
     +------------------------------------------------------------------------------------+
     |                                FINAL STORY PRESENTATION                            |
     | - Formatted bedtime title & story text                                             |
     | - Reading metrics: ~125 WPM oral reading pace, word count, estimated minutes       |
     | - LLM Judge Scorecard with dimension progress stars                                |
     | - Quality improvement delta (+X points from judge feedback loop)                   |
     +------------------------------------------------------------------------------------+
```

---

## 3. Component Deep Dive

### A. The Bedtime Storyteller Agent
- **Engine**: Anthropic Claude Haiku 5.5 (`claude-haiku-5-5`), with automatic fallback to `claude-3-5-haiku-20241022` if required by the API endpoint.
- **Narrative Theory**: Unlike open-ended story generators that maintain high dramatic tension up to a climax, bedtime stories require **narrative deceleration**. The final 25% of the story systematically reduces sentence length, lowers narrative stakes, and introduces auditory/tactile sleep cues (soft rhythmic breathing, fading twilight, purring cats, warm blankets).

### B. The LLM Judge Agent
- **Role Separation**: Operates with a distinct system persona from the Storyteller—acting as a pediatric sleep specialist and children's literature editor.
- **Rubric Structure**:
  1. *Age Appropriateness*: Calibrated across three age bands (5-6, 7-8, 9-10).
  2. *Bedtime Wind-Down*: Assesses whether reading the story will genuinely help a child relax and fall asleep.
  3. *Narrative Arc*: Confirms 4-act structure without jarring abruptness.
  4. *Language & Sensory Whimsy*: Evaluates read-aloud musicality, alliteration, and tactile imagery.
  5. *Emotional Safety*: Zero nightmare triggers, no unresolved panic, modeling empathy and security.
- **Actionable Directives**: Rather than generic praise, the judge issues targeted revision directives (e.g. *"Extend the final paragraph by two sentences to slow down the reading tempo with sensory bedtime cues"*).

### C. The Orchestration & Reflection Loop
- **Convergence Guard**: Limits iterations (default: 2) to optimize latency and token spend while guaranteeing quality improvements.
- **Delta Tracking**: Calculates the quantitative score increase between draft 1 and draft 2, demonstrating the tangible impact of the LLM Judge.
- **Graceful Degradation**: If an LLM response ever has formatting issues, a fallback parser recovers cleanly without disrupting the user experience.
