"""Tests for scale_validator module."""

from survey_designer.models import ResponseScale
from survey_designer.scale_validator import build_balanced_likert, validate_scale


def test_validate_likert_5_point_balanced():
    scale = build_balanced_likert(5, "agreement")
    result = validate_scale(scale)
    assert result.is_valid


def test_validate_likert_7_point_balanced():
    scale = build_balanced_likert(7, "agreement")
    result = validate_scale(scale)
    assert result.is_valid


def test_validate_likert_too_few_points():
    scale = ResponseScale(scale_type="likert", points=3, labels=[])
    result = validate_scale(scale)
    assert not result.is_valid
    assert any("only 3 points" in i for i in result.issues)


def test_validate_likert_even_with_neutral_contradiction():
    scale = ResponseScale(
        scale_type="likert",
        points=6,
        labels=["Strongly disagree", "Disagree", "Somewhat disagree", "Somewhat agree", "Agree", "Strongly agree"],
        includes_neutral=True,
    )
    result = validate_scale(scale)
    assert not result.is_valid
    assert any("contradictory" in i for i in result.issues)


def test_validate_likert_even_without_neutral_warns():
    scale = ResponseScale(
        scale_type="likert",
        points=6,
        labels=["Strongly disagree", "Disagree", "Somewhat disagree", "Somewhat agree", "Agree", "Strongly agree"],
        includes_neutral=False,
    )
    result = validate_scale(scale)
    # Should be valid but with a recommendation about forced-choice
    assert any("forced-choice" in r.lower() or "even" in r.lower() for r in result.recommendations)


def test_validate_rating_scale_valid():
    scale = ResponseScale(
        scale_type="rating",
        points=11,
        labels=[str(i) for i in range(11)],
        anchors={"low": "0", "high": "10"},
    )
    result = validate_scale(scale)
    assert result.is_valid


def test_validate_rating_scale_too_coarse():
    scale = ResponseScale(scale_type="rating", points=2, labels=["1", "2"])
    result = validate_scale(scale)
    assert not result.is_valid


def test_validate_nominal_duplicate_labels():
    scale = ResponseScale(
        scale_type="nominal",
        points=0,
        labels=["A", "B", "A"],
    )
    result = validate_scale(scale)
    assert not result.is_valid
    assert any("duplicate" in i.lower() for i in result.issues)


def test_validate_nominal_missing_labels():
    scale = ResponseScale(scale_type="nominal", points=0, labels=[])
    result = validate_scale(scale)
    assert not result.is_valid


def test_validate_nominal_recommends_other():
    scale = ResponseScale(scale_type="nominal", points=0, labels=["A", "B", "C"])
    result = validate_scale(scale)
    assert any("other" in r.lower() or "exhaustive" in r.lower() for r in result.recommendations)


def test_build_balanced_likert_agreement_5():
    scale = build_balanced_likert(5, "agreement")
    assert len(scale.labels) == 5
    assert scale.includes_neutral
    assert "agree" in scale.anchors["high"].lower()


def test_build_balanced_likert_frequency_5():
    scale = build_balanced_likert(5, "frequency")
    assert len(scale.labels) == 5
    assert scale.anchors["low"] == "Never"
    assert scale.anchors["high"] == "Always"


def test_build_balanced_likert_satisfaction_7():
    scale = build_balanced_likert(7, "satisfaction")
    assert len(scale.labels) == 7
    assert "dissatisfied" in scale.anchors["low"].lower()


def test_validate_open_scale_is_valid():
    scale = ResponseScale(scale_type="open", points=0, labels=[])
    result = validate_scale(scale)
    assert result.is_valid


def test_validate_unknown_scale_type():
    scale = ResponseScale(scale_type="bizarre", points=0, labels=[])
    result = validate_scale(scale)
    assert not result.is_valid
