"""Tests for question_generator and core orchestration."""

from survey_designer.core import audit_question, audit_questions, build_survey
from survey_designer.models import ResearchBrief, SurveyQuestion
from survey_designer.question_generator import generate_questions


def _basic_brief(length: int = 6) -> ResearchBrief:
    return ResearchBrief(
        topic="our new dashboard",
        objectives=["Measure satisfaction", "Find adoption barriers"],
        audience="Active users",
        constructs=["satisfaction", "barriers", "frequency"],
        desired_length=length,
    )


def test_generate_questions_returns_target_count():
    brief = _basic_brief(length=8)
    questions = generate_questions(brief)
    assert len(questions) == 8


def test_generate_questions_assigns_unique_ids():
    questions = generate_questions(_basic_brief(length=10))
    ids = [q.id for q in questions]
    assert len(ids) == len(set(ids))


def test_generate_questions_uses_topic():
    questions = generate_questions(_basic_brief())
    assert all("dashboard" in q.text for q in questions if "{topic}" not in q.text)


def test_generate_questions_default_constructs_when_none():
    brief = ResearchBrief(topic="thing", desired_length=4)
    questions = generate_questions(brief)
    assert len(questions) == 4
    assert all(q.construct for q in questions)


def test_audit_question_assigns_quality_score():
    q = SurveyQuestion(id="Q1", text="How would you describe your experience?", question_type="open_text")
    audit_question(q)
    assert 0.0 <= q.quality_score <= 1.0
    assert q.quality_score == 1.0  # clean question


def test_audit_question_penalises_biased():
    q = SurveyQuestion(
        id="Q1",
        text="Don't you think this amazing feature is fast and easy?",
        question_type="open_text",
    )
    audit_question(q)
    assert q.quality_score < 1.0
    assert len(q.bias_flags) > 0


def test_audit_questions_processes_all():
    questions = [
        SurveyQuestion(id="Q1", text="How is the experience?", question_type="open_text"),
        SurveyQuestion(id="Q2", text="Surely this is great?", question_type="open_text"),
    ]
    audit_questions(questions)
    assert questions[0].quality_score > questions[1].quality_score


def test_build_survey_returns_survey():
    brief = _basic_brief(length=6)
    survey = build_survey(brief, enrich_with_llm=False)
    assert survey.title.startswith("Survey")
    assert len(survey.questions) == 6
    assert 0.0 <= survey.overall_quality_score <= 1.0


def test_build_survey_quality_aggregates():
    brief = _basic_brief(length=6)
    survey = build_survey(brief, enrich_with_llm=False)
    expected_avg = sum(q.quality_score for q in survey.questions) / len(survey.questions)
    assert abs(survey.overall_quality_score - expected_avg) < 0.01


def test_build_survey_no_llm_leaves_llm_fields_none():
    brief = _basic_brief()
    survey = build_survey(brief, enrich_with_llm=False)
    assert survey.llm_backend is None
    assert survey.llm_summary is None
    for q in survey.questions:
        assert q.llm_rewrite is None
        assert q.llm_rationale is None


def test_survey_to_dict_serialisable():
    import json
    brief = _basic_brief()
    survey = build_survey(brief, enrich_with_llm=False)
    blob = json.dumps(survey.to_dict())
    assert "questions" in blob
    assert "overall_quality_score" in blob
