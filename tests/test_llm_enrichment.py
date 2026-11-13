"""Tests for LLM enrichment layer using unittest.mock — no live API calls."""

from unittest.mock import MagicMock, patch

from survey_designer import llm_enrichment
from survey_designer.models import BiasFlag, SurveyQuestion


def test_supported_backends_contains_three_models():
    assert "anthropic/claude-opus-4-7" in llm_enrichment.SUPPORTED_BACKENDS
    assert "gemini/gemini-4-argon" in llm_enrichment.SUPPORTED_BACKENDS
    assert "openai/gpt-5.5" in llm_enrichment.SUPPORTED_BACKENDS


def test_default_backend_is_claude_opus():
    assert llm_enrichment.DEFAULT_BACKEND == "anthropic/claude-opus-4-7"


def test_is_available_without_env_var(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Even if dspy is installed, missing key returns False
    if llm_enrichment._DSPY_AVAILABLE:
        assert llm_enrichment.is_available("anthropic/claude-opus-4-7") is False


def test_is_available_unknown_backend():
    assert llm_enrichment.is_available("nonsense/model") is False


def test_enrich_question_no_dspy_returns_unchanged(monkeypatch):
    monkeypatch.setattr(llm_enrichment, "_DSPY_AVAILABLE", False)
    q = SurveyQuestion(id="Q1", text="Test question", question_type="open_text")
    result = llm_enrichment.enrich_question(q)
    assert result.llm_rewrite is None
    assert result.llm_rationale is None


def test_enrich_question_with_mocked_dspy(monkeypatch):
    """Test enrichment with fully mocked dspy module."""
    if not llm_enrichment._DSPY_AVAILABLE:
        # Skip if dspy not installed in test env
        return

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_result = MagicMock()
    mock_result.rewritten_question = "How would you describe your experience?"
    mock_result.alternative_phrasings = "Phrasing A || Phrasing B"
    mock_result.rationale = "Removed leading phrasing."

    mock_program = MagicMock(return_value=mock_result)

    with patch.object(llm_enrichment, "dspy") as mock_dspy:
        mock_dspy.LM = MagicMock()
        mock_dspy.configure = MagicMock()
        mock_dspy.ChainOfThought = MagicMock(return_value=mock_program)

        q = SurveyQuestion(
            id="Q1",
            text="Don't you think this is great?",
            question_type="open_text",
            construct="satisfaction",
            bias_flags=[BiasFlag(bias_type="leading", severity="high", excerpt="don't you think", rationale="Leading")],
        )
        result = llm_enrichment.enrich_question(q, backend="anthropic/claude-opus-4-7")

        assert result.llm_rewrite == "How would you describe your experience?"
        assert result.llm_rationale == "Removed leading phrasing."
        assert result.llm_alternative_phrasings == ["Phrasing A", "Phrasing B"]


def test_enrich_question_handles_errors_gracefully(monkeypatch):
    """If LLM call fails, llm_ fields stay None and we don't raise."""
    if not llm_enrichment._DSPY_AVAILABLE:
        return

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch.object(llm_enrichment, "dspy") as mock_dspy:
        mock_dspy.LM = MagicMock(side_effect=RuntimeError("API down"))
        mock_dspy.configure = MagicMock()

        q = SurveyQuestion(id="Q1", text="Test", question_type="open_text")
        result = llm_enrichment.enrich_question(q)

        assert result.llm_rewrite is None


def test_enrich_questions_batch(monkeypatch):
    if not llm_enrichment._DSPY_AVAILABLE:
        return

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_result = MagicMock()
    mock_result.rewritten_question = "Rewritten"
    mock_result.alternative_phrasings = "Alt1"
    mock_result.rationale = "Rationale"
    mock_program = MagicMock(return_value=mock_result)

    with patch.object(llm_enrichment, "dspy") as mock_dspy:
        mock_dspy.LM = MagicMock()
        mock_dspy.configure = MagicMock()
        mock_dspy.ChainOfThought = MagicMock(return_value=mock_program)

        questions = [
            SurveyQuestion(id="Q1", text="A", question_type="open_text"),
            SurveyQuestion(id="Q2", text="B", question_type="open_text"),
        ]
        llm_enrichment.enrich_questions(questions)
        assert all(q.llm_rewrite == "Rewritten" for q in questions)
