# AI doing AI research: 2026 evidence ranked by closeness to the closed loop

target_category:
  - intermediate
  - asi
primary_model_use:
  - rnd_automation_today
  - regime_evidence
  - takeoff regime parameters (f_AGI, taste automation)

## The chain, and how far 2026 evidence gets along it

```text
1 AI suggests improvement            -> yes, weak (next-step choice beats selected human baseline 64%; open-ended papers rejected)
2 AI implements improvement          -> yes, routine (>80% of merged code at Anthropic is Claude-authored)
3 AI runs experiment                 -> yes (3.1 agent-workdays per human workday at OpenAI; 4+ concurrent agents common)
4 AI evaluates result                -> partly (>50% of successful 4-8h tasks need >=1 intervention)
5 improvement independently validated-> yes, at small scale (AlphaEvolve: ~1% Gemini training time; kernel/training speed-ups)
6 successor becomes more capable     -> NOT attributable (Mythos 5 is a level shift; no AI-attributable slope change)
7 successor improves next R&D cycle  -> NOT observed
```

Only a complete 1->7 loop is evidence for recursive self-improvement. As of
2026-10-06 steps 1-5 exist (5 only on bounded problems); 6-7 are not observed.
AI-assisted coding is **not** RSI.

## Evidence ranked by proximity to the closed loop

| Rank | Evidence | Steps | Source |
|---|---|---|---|
| 1 | Anthropic's ECI trajectory: Mythos 5 is above trend by the same margin as Mythos Preview, "inconsistent with" compounding acceleration; no sustained AI-attributable 2x speed-up | 6-7 (negative) | [Mythos 5 system card](https://www-cdn.anthropic.com/2f9323abbcc4abe219577539efe19a623c9ca2bd/Claude%20Fable%205%20&%20Claude%20Mythos%205%20System%20Card.pdf) |
| 2 | AlphaEvolve: AI-found kernel and scheduling improvements validated and deployed into Gemini training (~1% training time, 0.7% fleet compute) | 1-5 | [DeepMind, May 2025](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) |
| 3 | Small-LLM training speed-up task: ~3x (Opus 4, May 2025) -> 52-70x (Mythos Preview/5, 2026); a skilled human needs 4-8h to reach 4x | 2-5 (bounded) | [Anthropic RSI essay](https://www.anthropic.com/institute/recursive-self-improvement) |
| 4 | Autonomous weak-to-strong supervision project: agents recovered 97% of the gap vs 23% for two humans in a week; humans chose the problem and metric; did not transfer cleanly to production scale | 1-5 (bounded) | Anthropic RSI essay |
| 5 | OpenAI "research intern": multi-day well-defined tasks under human direction; planning remains a minimal share of agent tokens | 2-4 | [OpenAI, Sep 2026](https://openai.com/index/research-acceleration-view-inside-openai/) |
| 6 | GPT-6 Astra internal research debugging 78% (below "High"); GPT-5.6 Sol helped post-train a smaller model (reported) | 2-4 | [Astra system card](https://deploymentsafety.openai.com/gpt-6-astra) |
| 7 | Princeton "shadow evaluation": agents did the engineering for two unpublished NeurIPS 2026 questions; original authors rejected both papers | 1 (negative) | [MIT Technology Review](https://www.technologyreview.com/2026/08/18/1142188/ai-recursive-self-improvement/) |
| 8 | METR developer RCT: the late-2025 follow-up is unreliable because of selection effects; raw estimates -18% to -4% task time | uplift measurement | [METR](https://metr.org/blog/2026-02-24-uplift-update/) |

## How it enters the model

* `rnd_automation_today`: the decomposition gives A_R&D about 0.57 supervised and
  0.34 autonomous. The tight model interval (0.28-0.40) is an under-statement
  because component weights are fixed; a fair range is 0.2-0.5.
* Regime evidence: items 1, 3-5 and 7 belong to one correlation group
  (`lab_internal_rnd_measurement`) and are averaged, not multiplied.
* Takeoff parameters: residual research judgement is the Amdahl term (1 - f), and
  its automation rate is `taste_automation_per_oom`.
