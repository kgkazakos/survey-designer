"""Tests for dataclass serialisation and structure."""

from survey_designer.models import (
    BiasFlag,
    ResearchBrief,
    ResponseScale,
    ScaleValidation,
    Survey,
    SurveyQuestion,
)


def test_bias_flag_to_dict():
    flag = BiasFlag(bias_type="leading", severity="high", excerpt="x", rationale="y")
    d = flag.to_dict()
    assert d["bias_type"] == "leading"
    assert d["severity"] == "high"


def test_response_scale_defaults():
    scale = ResponseScale(scale_type="open")
    assert scale.points == 0
    assert scale.labels == []
    assert scale.is_balanced is True


def test_scale_validation_default_empty_lists():
    v = ScaleValidation(is_valid=True)
    assert v.issues == []
    assert v.warnings == []
    assert v.recommendations == []


def test_survey_question_construction():
    q = SurveyQuestion(id="Q1", text="hi", question_type="open_text")
    assert q.id == "Q1"
    assert q.bias_flags == []
    assert q.llm_rewrite is None  # default


def test_research_brief_defaults():
    b = ResearchBrief(topic="x")
    assert b.objectives == []
    assert b.desired_length == 12


def test_survey_to_dict_complete():
    brief = ResearchBrief(topic="x", objectives=["o1"])
    q = SurveyQuestion(id="Q1", text="t", question_type="open_text", construct="c")
    s = Survey(title="T", brief=brief, questions=[q])
    d = s.to_dict()
    assert d["title"] == "T"
    assert len(d["questions"]) == 1
    assert d["llm_backend"] is None
