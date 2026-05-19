Most surveys go into the field with at least one broken question.

A leading "Don't you think...", a double-barreled "fast and easy", a Likert scale that's quietly forcing respondents to a side, a "How often do you use this?" with no escape for people who don't. Each one is a small data-quality leak. Together they compound. And under deadline pressure — when the brief lands Tuesday and the survey ships Friday — they're the kind of thing you spot in the readout, not in the draft.

I built **survey-designer** to be a quality net you run before fieldwork. You give it a research brief; it gives you a draft survey, scored question by question.

**What it does**

- Generates survey questions from a research brief (topic, objectives, constructs, target length)
- Audits every question for eight bias patterns: leading, loaded, double-barreled, jargon, absolutes, double negatives, hidden assumptions, acquiescence
- Validates response scales for balance, anchors, mid-point handling, and exhaustiveness
- Rewrites flagged questions with an LLM (Claude Opus 4.7, Gemini 3.1 Pro, or GPT 5.5 — pick your backend), with rationale and alternative phrasings
- Outputs a quality score per question and an overall score for the instrument
- Ships with a Streamlit UI and a CLI; JSON output for CI pipelines

**The objection I want to address up front**

This does not replace pilot testing. The rule-based detectors are rules — they will miss things and occasionally flag the wrong thing. The LLM rewrites are model-generated and need a researcher's eye. What this tool does is get your draft to pilot with fewer obvious leaks. The point is to spend your pilot exploring real comprehension issues, not catching things any methodologist would have flagged on a second read.

That's the value bar — it should be useful even to senior researchers, because under time pressure even senior researchers ship broken questions.

This is Tool 28 of the **CPR Orbital Series** — 40 open-source tools for AI-native product research, shipping at an almost daily cadence through December. The whole series is MIT-licensed and model-agnostic — works rule-based with no API key, or with any of three LLM backends when you want enrichment.

What's the most common bias pattern you catch in your team's survey drafts? Curious whether the eight I detect map to what you see.

#UXResearch #ComputationalProductResearch #OpenSource #SyntheticResearch #ProductResearch
