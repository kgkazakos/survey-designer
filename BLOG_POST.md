# Survey Designer: A pre-fieldwork quality net for survey instruments

*Tool 28 of the CPR Orbital Series — May 2026*

---

## The problem nobody talks about in survey research

If you've been in product research for a few years, you have a story like this one.

A Tuesday brief lands on your desk. The PM wants quantitative validation of an in-flight feature by end of week. You have a draft of the survey by Wednesday afternoon, you ship Thursday morning, and you're reading early results Friday. The story is fine. You move on.

Then, six weeks later, you're writing the readout and you notice it. Question 4 was double-barreled — "Is the dashboard fast and easy to use?" — and now you have no idea whether the 70% agreement number you're about to put on a slide is about speed, ease, or some weighted average of the two. You can't unship the survey. You footnote it and live with the noise.

This happens. It happens to senior researchers. It happens to teams with style guides and review rituals. The reason it happens is that survey instrument design under deadline pressure exceeds the bandwidth of a single careful read-through. There is too much to check — leading phrasings, loaded terms, jargon, scale balance, mid-point handling, anchor presence, exhaustiveness, hidden assumptions — and the cost of missing one is invisible until the data comes back broken.

`survey-designer` is the quality net I wanted on that Tuesday afternoon.

---

## What it does

You give it a brief:

```json
{
  "topic": "our new analytics dashboard",
  "objectives": [
    "Measure satisfaction",
    "Identify barriers to adoption",
    "Estimate likelihood to recommend"
  ],
  "audience": "Active users in the last 30 days",
  "constructs": ["satisfaction", "usability", "barriers", "recommendation"],
  "desired_length": 10
}
```

It gives you back ten questions, each with:

- A response scale appropriate to the construct (balanced Likert, 0–10 rating, ranking, nominal, open-ended)
- A bias audit across eight patterns
- A scale-design validation
- A 0.00–1.00 quality score
- When an LLM backend is configured: a rewrite, a rationale for the rewrite, and two alternative phrasings

You inspect the questions, accept the rewrites you agree with, override the ones you don't, and you go to pilot with a stronger draft.

---

## What it detects

The bias detectors are intentionally rule-based. I want them to be transparent, deterministic, and inspectable — you should be able to look at a flag and immediately understand why it fired. LLMs are great at the *rewrite* step but not the right tool for the *detection* step where consistency and explainability matter.

The eight bias patterns:

**1. Leading.** "Don't you think...", "Wouldn't you agree...", "Surely...", "Clearly...". Patterns that signal the expected answer. High severity.

**2. Loaded.** Emotionally charged adjectives: "amazing", "terrible", "revolutionary", "useless". These shift the entire response distribution. Medium severity.

**3. Double-barreled.** A single question asking about two distinct dimensions joined by "and" or "or" — "fast and easy", "secure and convenient". Respondents who feel differently about each dimension are forced into an aggregated answer. High severity.

**4. Jargon.** UX-industry and internal-business terms that respondents don't share the vocabulary for: "onboarding", "retention", "stickiness", "UX", "KPI". Medium severity.

**5. Absolutes.** "Always", "never", "everyone", "completely". These force extreme responses and limit nuance. Low severity (sometimes intentional).

**6. Double negatives.** "Not unhappy with...", "never fail to..." — increase respondent error rates by demanding cognitive double-take. Medium severity.

**7. Hidden assumptions.** "How often do you use feature X?" — assumes the respondent uses it, gives no escape option. "When you open the app..." — assumes they do. These are not bias-bias, but they are data-quality bombs because non-users either drop off or fabricate. Medium severity.

**8. Acquiescence.** "I am satisfied with X" + agreement scale. Yes-bias is well-documented in survey methodology, and the fix is reverse-coded items or bipolar phrasings. Low severity (with recommendation to balance the scale).

The scale validator checks:

- Likert length (5 or 7 is standard; <5 is too coarse; >9 exceeds discrimination)
- Even-numbered scales claiming to include a neutral point (contradictory)
- Forced-choice scales without explicit "this is intentional" justification
- Balance between positive and negative anchors
- Anchor presence on rating scales
- Mutually exclusive and exhaustive options on nominal scales
- Duplicate labels

Each question gets a score: start at 1.00, deduct 0.25 for each high-severity bias flag, 0.10 for medium, 0.05 for low, 0.15 per scale issue, 0.05 per scale warning. The overall instrument score is the mean.

---

## The LLM layer

LLM enrichment is on by default. Three backends are supported and you can switch between them:

| Model | Env var |
|---|---|
| `anthropic/claude-opus-4-7` *(default)* | `ANTHROPIC_API_KEY` |
| `gemini/gemini-3.1-pro` | `GEMINI_API_KEY` |
| `openai/gpt-5.5` | `OPENAI_API_KEY` |

The LLM step uses DSPy's `ChainOfThought` over a structured signature: it receives the original question, the construct it's meant to measure, and a serialized list of detected issues. It returns a rewrite, two alternative phrasings, and a short rationale explaining what was changed and why.

The architecture is deliberately decoupled. The rule-based core runs offline. If no API key is configured, the `llm_*` fields in the output JSON are `null` and the tool returns its rule-based output unchanged. There's no failure mode where a missing key breaks the pipeline — the LLM is enrichment, not a dependency.

This matters for three reasons. First, it makes the tool usable in environments with no external network. Second, it makes the rule-based output testable in isolation. Third, it gives researchers a fallback when an LLM is unavailable or its rewrite isn't useful — the rule-based flags and recommendations stand on their own.

---

## What this is and what it is not

This is the section I write in every CPR Orbital tool's README, and it matters most for tools like this one.

**This is**: a pre-fieldwork quality net. It catches the kind of issues that practitioners under deadline pressure miss. It produces consistent quality scores you can track across a research programme — a useful signal for research-ops teams trying to maintain instrument quality at scale.

**This is not**: a replacement for piloting your survey with real participants. The rule-based detectors have known failure modes — they will miss context-dependent issues (a phrase that's jargon in B2B and plain English in B2C, for example), and they will occasionally flag questions that are intentionally phrased the way they are. The LLM rewrites are model-generated and need a methodologist's eye. Cognitive interviews remain irreplaceable for catching comprehension failures.

The framing I want to defend: this tool helps you arrive at pilot with a stronger draft, not skip pilot. The value is in shifting your pilot's attention from obvious flaws to real comprehension issues.

---

## Architecture notes

For practitioners interested in the engineering side:

- Python 3.10–3.12, MIT licensed
- `click` CLI with `rich` terminal output
- `streamlit` for the UI
- `dspy-ai` + `litellm` for LLM enrichment
- Module-level conditional imports for LLM dependencies (patchable by `unittest.mock` for testing without live API calls)
- 63-test pytest suite, ruff linted, GitHub Actions CI on three Python versions
- `pyproject.toml` with `setuptools.build_meta` backend
- All LLM dependencies are core, not optional extras — this is a deliberate choice in the post–Tool 16 architecture of the CPR Orbital Series

The data model is three nested dataclasses: `Survey` contains `ResearchBrief` + a list of `SurveyQuestion`s, each of which contains a `ResponseScale`, a list of `BiasFlag`s, and a `ScaleValidation`. Everything serializes cleanly to JSON for CI integration.

---

## How it sits in the CPR Ecosystem

The CPR Orbital Series is a forty-tool, MIT-licensed open-source effort to build the practitioner-facing infrastructure for AI-native product research. Tools are designed to feed into one another:

**Pre-fieldwork**: `qual-sniffer` (discussion-guide weakness detection), `guide-scorer` (eight-dimension quality scoring), **`survey-designer` (this tool)**, `screener-generator` (recruitment screeners), `ethics-checker`, `sample-sizer`

**During fieldwork**: `interview-sim`, `recall-probe`, `say-do-lite`

**Post-fieldwork data cleaning**: `transcript-cleaner`, `survey-cleaner`

**Analysis**: `bias-audit`, `saturation-meter`, `effect-sizer`, `max-diff-analyzer`, `quant-qual-bridge`, `segment-finder`

**Synthesis & reporting**: `stat-narrator`, `insight-differ`, `stakeholder-brief-writer`, `journey-map-generator`, `jtbd-extractor`

`survey-designer` sits at the start of that workflow. A brief comes in → you draft the instrument with `survey-designer` → you pilot with real participants → returned data goes through `survey-cleaner` → analysis tools take it from there.

---

## What's next

Tool 29 is `quant-qual-bridge` — linking quantitative segments to qualitative insight threads across a mixed-methods corpus. After that, `segment-finder` (automated behavioural segmentation) and `usability-metrics-kit` (SUS, UMUX, SUPR-Q calculation and benchmarking). The series finishes in December with `cpr-toolkit`, a meta-package that bundles all forty tools into a single install.

Almost daily cadence through December. Every tool MIT-licensed. Every tool model-agnostic. Every tool with a "what this is and isn't" section, because the framing matters as much as the code.

If you build with it, send me a note about what works and what doesn't. The feedback loop is what keeps the series honest.

---

**Repo**: github.com/kgkazakos/survey-designer
**Install**: `pip install survey-designer`
**License**: MIT
**Part of**: [CPR Orbital Series](https://github.com/kgkazakos)
