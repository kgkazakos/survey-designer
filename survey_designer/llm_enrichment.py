"""Optional LLM enrichment via DSPy ChainOfThought.

LLM imports are module-level and conditional to enable unittest.mock patching
without requiring live API calls in tests.
"""

from __future__ import annotations

import os
from typing import Optional

from .models import SurveyQuestion

# Conditional, patchable imports
try:
    import dspy  # type: ignore
    _DSPY_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in environments without dspy
    dspy = None  # type: ignore
    _DSPY_AVAILABLE = False


SUPPORTED_BACKENDS = {
    "anthropic/claude-opus-4-7": "ANTHROPIC_API_KEY",
    "gemini/gemini-4-argon": "GEMINI_API_KEY",
    "openai/gpt-5.5": "OPENAI_API_KEY",
}

DEFAULT_BACKEND = "anthropic/claude-opus-4-7"


class QuestionEnrichment(dspy.Signature if _DSPY_AVAILABLE else object):  # type: ignore[misc]
    """Improve a survey question, suggest alternatives, and explain the rewrite.

    The goal is to produce a neutrally-phrased, bias-free, single-dimension question
    that aligns with the underlying construct. Output should preserve the original
    intent while removing bias, jargon, and assumption.
    """

    original_question: str = dspy.InputField(desc="The original survey question.") if _DSPY_AVAILABLE else None  # type: ignore
    construct: str = dspy.InputField(desc="The construct the question is meant to measure.") if _DSPY_AVAILABLE else None  # type: ignore
    detected_issues: str = dspy.InputField(desc="A summary of bias and scale issues detected.") if _DSPY_AVAILABLE else None  # type: ignore
    rewritten_question: str = dspy.OutputField(desc="A bias-free, single-dimension rewrite.") if _DSPY_AVAILABLE else None  # type: ignore
    alternative_phrasings: str = dspy.OutputField(desc="Two alternative phrasings of the rewritten question, separated by '||'.") if _DSPY_AVAILABLE else None  # type: ignore
    rationale: str = dspy.OutputField(desc="A short explanation of what was changed and why.") if _DSPY_AVAILABLE else None  # type: ignore


def _ensure_dspy_configured(backend: str) -> None:
    """Configure DSPy with the requested backend.

    Falls back silently if the API key is not present in env; the caller
    is expected to handle the resulting exception or check is_available().
    """
    if not _DSPY_AVAILABLE:
        raise RuntimeError("dspy is not installed. Install with: pip install dspy-ai litellm")

    env_var = SUPPORTED_BACKENDS.get(backend)
    if env_var is None:
        raise ValueError(
            f"Unsupported backend: {backend}. Supported: {list(SUPPORTED_BACKENDS.keys())}"
        )

    if not os.getenv(env_var):
        raise RuntimeError(
            f"Environment variable {env_var} is not set. LLM enrichment requires this key."
        )

    lm = dspy.LM(model=backend, max_tokens=1024)
    dspy.configure(lm=lm)


def is_available(backend: str = DEFAULT_BACKEND) -> bool:
    """Return True if dspy is installed and an API key is configured for the backend."""
    if not _DSPY_AVAILABLE:
        return False
    env_var = SUPPORTED_BACKENDS.get(backend)
    if env_var is None:
        return False
    return bool(os.getenv(env_var))


def enrich_question(
    question: SurveyQuestion,
    backend: str = DEFAULT_BACKEND,
) -> SurveyQuestion:
    """Enrich a single question with LLM rewrites and rationale.

    Mutates and returns the question. Sets llm_rewrite, llm_rationale,
    and llm_alternative_phrasings fields. On any error, leaves the
    question unchanged with llm_ fields as None.
    """
    if not _DSPY_AVAILABLE:
        return question

    try:
        _ensure_dspy_configured(backend)
        detected_issues = "; ".join(
            f"{flag.bias_type} ({flag.severity}): {flag.rationale}"
            for flag in question.bias_flags
        ) or "No issues detected."

        if question.scale_validation:
            scale_issues = "; ".join(question.scale_validation.issues + question.scale_validation.warnings)
            if scale_issues:
                detected_issues += f" | Scale: {scale_issues}"

        program = dspy.ChainOfThought(QuestionEnrichment)
        result = program(
            original_question=question.text,
            construct=question.construct,
            detected_issues=detected_issues,
        )

        question.llm_rewrite = result.rewritten_question.strip() if hasattr(result, "rewritten_question") else None
        question.llm_rationale = result.rationale.strip() if hasattr(result, "rationale") else None
        alternatives_raw = result.alternative_phrasings if hasattr(result, "alternative_phrasings") else ""
        if alternatives_raw:
            question.llm_alternative_phrasings = [a.strip() for a in alternatives_raw.split("||") if a.strip()]
    except Exception as exc:  # noqa: BLE001 - best-effort enrichment
        # Leave llm_ fields untouched (None) on any failure
        _ = exc

    return question


def enrich_questions(
    questions: list[SurveyQuestion],
    backend: str = DEFAULT_BACKEND,
) -> list[SurveyQuestion]:
    """Enrich a list of questions. Continues on per-question failures."""
    for q in questions:
        enrich_question(q, backend=backend)
    return questions


def summarize_survey(
    questions: list[SurveyQuestion],
    backend: str = DEFAULT_BACKEND,
) -> Optional[str]:
    """Produce a narrative summary of the survey's design quality."""
    if not _DSPY_AVAILABLE:
        return None
    try:
        _ensure_dspy_configured(backend)

        class SurveySummary(dspy.Signature):  # type: ignore
            """Summarise the methodological quality of a survey instrument."""
            question_count: int = dspy.InputField()
            constructs: str = dspy.InputField()
            bias_summary: str = dspy.InputField()
            summary: str = dspy.OutputField(desc="A short narrative summary for a research practitioner.")

        constructs = ", ".join(sorted({q.construct for q in questions if q.construct}))
        bias_count = sum(len(q.bias_flags) for q in questions)
        bias_summary = f"{bias_count} bias flags across {len(questions)} questions."

        program = dspy.ChainOfThought(SurveySummary)
        result = program(
            question_count=len(questions),
            constructs=constructs,
            bias_summary=bias_summary,
        )
        return result.summary.strip() if hasattr(result, "summary") else None
    except Exception:  # noqa: BLE001
        return None
