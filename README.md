# survey-designer

**AI-assisted survey question generation with bias detection and response-scale validation.**

Part of the [CPR Orbital Series](https://github.com/kgkazakos) — Tool 28 of 40. Built on `dspy-ai` and `litellm` with a rule-based core that runs fully offline. LLM enrichment is enabled by default across three model backends.

---

## What this is

`survey-designer` turns a research brief into a set of survey questions, audits each one for bias patterns and scale-design issues, and (optionally) rewrites them with an LLM. It is not a replacement for piloting your survey with real participants — it is a quality net you run before fieldwork.

You give it a brief like:

```json
{
  "topic": "our new dashboard feature",
  "objectives": [
    "Measure satisfaction",
    "Identify adoption barriers",
    "Estimate likelihood to recommend"
  ],
  "audience": "Active users in the last 30 days",
  "constructs": ["satisfaction", "usability", "barriers", "recommendation"],
  "desired_length": 10
}
```

You get back a set of questions, each with:

- A response scale appropriate to its construct
- A bias audit (leading, loaded, double-barreled, jargon, absolutes, double negatives, assumptions, acquiescence)
- A scale-design validation (balance, anchors, exhaustiveness, mid-point handling)
- A quality score (0.0–1.0)
- An LLM rewrite + rationale + alternative phrasings when an API key is configured

---

## Install

```bash
pip install survey-designer
```

Or from source:

```bash
git clone https://github.com/kgkazakos/survey-designer.git
cd survey-designer
pip install -e .
```

---

## LLM backends

LLM enrichment is **on by default**. Three backends are supported:

| Model | Env var |
|---|---|
| `anthropic/claude-opus-4-7` *(default)* | `ANTHROPIC_API_KEY` |
| `gemini/gemini-4-argon` | `GEMINI_API_KEY` |
| `openai/gpt-5.5` | `OPENAI_API_KEY` |

If no key is configured, the tool falls back to its rule-based output and the `llm_*` fields in the JSON are `null`. Nothing breaks.

```bash
survey-designer backends   # see which backends are available
```

---

## Usage

### CLI

```bash
# Generate, audit, and enrich a survey from a brief
survey-designer generate --brief brief.json --output survey.json

# Pick a specific backend
survey-designer generate --brief brief.json --llm-backend gemini/gemini-4-argon

# Disable LLM entirely (rule-based only)
survey-designer generate --brief brief.json --no-llm

# Re-audit an existing survey file
survey-designer audit --survey survey.json

# Machine-readable output for CI
survey-designer generate --brief brief.json --json-output > survey.json
```

### Streamlit UI

```bash
streamlit run -m survey_designer.app
```

The UI lets you draft a brief, pick a model backend, generate the survey, inspect every flag and recommendation per question, and export the result as JSON.

### Python API

```python
from survey_designer import ResearchBrief, build_survey

brief = ResearchBrief(
    topic="our new dashboard",
    objectives=["Measure satisfaction", "Find adoption barriers"],
    constructs=["satisfaction", "barriers", "recommendation"],
    desired_length=10,
)

survey = build_survey(brief, enrich_with_llm=True, llm_backend="anthropic/claude-opus-4-7")
print(survey.overall_quality_score, survey.bias_count)
```

---

## What it detects

**Bias patterns** (per question):

- **Leading** — "Don't you think...", "Surely...", "Wouldn't you agree..."
- **Loaded** — emotionally charged terms ("amazing", "terrible", "revolutionary")
- **Double-barreled** — "fast and easy", "secure and convenient"
- **Jargon** — internal acronyms and UX-industry terms that respondents don't share
- **Absolutes** — "always", "never", "everyone"
- **Double negatives** — "not unhappy", "never fail to"
- **Assumptions** — "How often do you use..." with no escape option
- **Acquiescence** — yes-bias patterns

**Scale-design issues**:

- Likert scales too short, too long, or unbalanced
- Even-numbered scales claiming to include neutral
- Forced-choice scales without an explicit "this is intentional" path
- Nominal scales with duplicate or non-exhaustive labels
- Missing anchors on rating scales

---

## What this is and what it is not

**This is**: a pre-fieldwork quality net. It catches the leading phrasings, jargon, and broken scales that practitioners under deadline pressure miss. It produces consistent quality scores you can track across a research programme.

**This is not**: a replacement for pilot testing with real participants. The detectors are rule-based and the LLM rewrites are model-generated — both have known failure modes. Always pilot before launch. The tool helps you arrive at pilot with a stronger draft, not skip it.

---

## Part of the CPR Ecosystem

`survey-designer` is one tool in a 40-tool open-source series for AI-native product research:

- **[transcript-cleaner](https://github.com/kgkazakos/transcript-cleaner)** — fix diarization and turn-taking in raw transcripts
- **[qual-sniffer](https://github.com/kgkazakos/qual-sniffer)** — detect methodological weaknesses in discussion guides
- **[survey-cleaner](https://github.com/kgkazakos/survey-cleaner)** — remove speeders, straight-liners, and gibberish open-ends
- **[guide-scorer](https://github.com/kgkazakos/guide-scorer)** — score discussion guides across eight quality dimensions
- **[bias-audit](https://github.com/kgkazakos/bias-audit)** — interviewer bias detection across transcript corpora
- **[max-diff-analyzer](https://github.com/kgkazakos/max-diff-analyzer)** — LLM-assisted MaxDiff preference analysis
- **[synthetic-panel](https://github.com/kgkazakos/synthetic-panel)** — persistent versioned synthetic research panel

Survey-designer sits on the instrument-design side of the workflow: you draft a brief → use `survey-designer` to draft the instrument → pilot with real participants → run `survey-cleaner` on the returned data → analyse downstream.

---

## License

MIT.

## Citation

If `survey-designer` informs your work, a citation is appreciated:

```
Kazakos, K. (2026). survey-designer: AI-assisted survey question generation with bias detection.
Part of the CPR Orbital Series. https://github.com/kgkazakos/survey-designer
```
