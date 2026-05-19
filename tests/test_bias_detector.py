"""Tests for bias_detector module."""

from survey_designer.bias_detector import (
    detect_absolutes,
    detect_acquiescence,
    detect_all_bias,
    detect_assumption,
    detect_double_barreled,
    detect_double_negative,
    detect_jargon,
    detect_leading,
    detect_loaded,
)


def test_leading_question_with_dont_you_think():
    flags = detect_leading("Don't you think this feature is helpful?")
    assert len(flags) == 1
    assert flags[0].bias_type == "leading"
    assert flags[0].severity == "high"


def test_leading_question_with_surely():
    flags = detect_leading("Surely this is the best option?")
    assert any(f.bias_type == "leading" for f in flags)


def test_leading_clean_question():
    flags = detect_leading("How would you describe your experience?")
    assert flags == []


def test_loaded_terms_amazing():
    flags = detect_loaded("How would you rate this amazing feature?")
    assert any(f.excerpt == "amazing" for f in flags)


def test_loaded_terms_terrible():
    flags = detect_loaded("Was the experience terrible?")
    assert any(f.excerpt == "terrible" for f in flags)


def test_loaded_clean():
    flags = detect_loaded("Was the experience helpful?")
    assert flags == []


def test_absolute_always():
    flags = detect_absolutes("Do you always use this feature?")
    assert any(f.excerpt == "always" for f in flags)


def test_absolute_never():
    flags = detect_absolutes("Have you ever used this? Never?")
    assert any(f.excerpt == "never" for f in flags)


def test_absolute_clean():
    flags = detect_absolutes("Do you sometimes use this feature?")
    assert flags == []


def test_jargon_onboarding():
    flags = detect_jargon("How was the onboarding experience?")
    assert any(f.excerpt == "onboarding" for f in flags)


def test_jargon_ux_acronym():
    flags = detect_jargon("How is the ux of this tool?")
    assert any(f.excerpt == "ux" for f in flags)


def test_double_barreled_fast_and_easy():
    flags = detect_double_barreled("Is this fast and easy to use?")
    assert any(f.bias_type == "double_barreled" for f in flags)


def test_double_barreled_clean():
    flags = detect_double_barreled("Is this easy to use?")
    assert flags == []


def test_double_negative():
    flags = detect_double_negative("Are you not unhappy with this feature?")
    assert any(f.bias_type == "double_negative" for f in flags)


def test_assumption_how_often():
    flags = detect_assumption("How often do you use this feature?")
    assert any(f.bias_type == "assumption" for f in flags)


def test_acquiescence_agreement():
    flags = detect_acquiescence("Do you agree that this is helpful?")
    assert any(f.bias_type == "acquiescence" for f in flags)


def test_detect_all_combines_results():
    text = "Don't you think this amazing feature is fast and easy?"
    flags = detect_all_bias(text)
    bias_types = {f.bias_type for f in flags}
    assert "leading" in bias_types
    assert "loaded" in bias_types
    assert "double_barreled" in bias_types


def test_detect_all_clean_question():
    text = "How would you describe your experience with the tool?"
    flags = detect_all_bias(text)
    assert flags == []
