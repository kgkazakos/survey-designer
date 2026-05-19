"""Core orchestration: generate, audit, validate, and score a survey."""

from __future__ import annotations

from typing import Optional

from .bias_detector import detect_all_bias
from .models import ResearchBrief, Survey, SurveyQuestion
from .question_generator import generate_questions
from .scale_validator import validate_scale

# Severity weight for quality scoring
SEVERITY_WEIGHT = {"high": 0.25, "medium": 0.10, "low": 0.05}


def audit_question(question: SurveyQuestion) -> SurveyQuestion:
    """Run bias detection and scale validation on a question. Compute quality score."""
    question.bias_flags = detect_all_bias(question.text)
    if question.scale is not None:
        question.scale_validation = validate_scale(question.scale)

    # Quality score: start at 1.0, deduct for issues
    score = 1.0
    for flag in question.bias_flags:
        score -= SEVERITY_WEIGHT.get(flag.severity, 0.0)
    if question.scale_validation:
        score -= 0.15 * len(question.scale_validation.issues)
        score -= 0.05 * len(question.scale_validation.warnings)

    question.quality_score = max(0.0, min(1.0, round(score, 3)))
    return question


def audit_questions(questions: list[SurveyQuestion]) -> list[SurveyQuestion]:
    """Audit a list of questions in place."""
    for q in questions:
        audit_question(q)
    return questions


def build_survey(
    brief: ResearchBrief,
    enrich_with_llm: bool = True,
    llm_backend: Optional[str] = None,
) -> Survey:
    """End-to-end: generate questions from a brief, audit, score, optionally enrich.

    If enrich_with_llm is True (default), the LLM enrichment layer will be
    invoked if an API key is configured for the requested backend. If no key
    is present, enrichment is silently skipped — the rule-based output stands.
    """
    questions = generate_questions(brief)
    audit_questions(questions)

    title = f"Survey: {brief.topic}"
    survey = Survey(
        title=title,
        brief=brief,
        questions=questions,
        overall_quality_score=_compute_overall_quality(questions),
        bias_count=sum(len(q.bias_flags) for q in questions),
        scale_issue_count=sum(
            len(q.scale_validation.issues) if q.scale_validation else 0 for q in questions
        ),
    )

    if enrich_with_llm:
        from . import llm_enrichment

        backend = llm_backend or llm_enrichment.DEFAULT_BACKEND
        if llm_enrichment.is_available(backend):
            llm_enrichment.enrich_questions(questions, backend=backend)
            summary = llm_enrichment.summarize_survey(questions, backend=backend)
            survey.llm_backend = backend
            survey.llm_summary = summary

    return survey


def _compute_overall_quality(questions: list[SurveyQuestion]) -> float:
    if not questions:
        return 0.0
    return round(sum(q.quality_score for q in questions) / len(questions), 3)
