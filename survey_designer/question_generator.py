"""Rule-based question generator from a research brief."""

from __future__ import annotations

from .models import ResearchBrief, ResponseScale, SurveyQuestion
from .scale_validator import build_balanced_likert

# Construct → starter question templates (neutral phrasing, anchor terms avoided)
CONSTRUCT_TEMPLATES = {
    "satisfaction": [
        ("How would you describe your overall experience with {topic}?", "likert", "satisfaction"),
        ("Looking at {topic} overall, how does it compare to your expectations?", "likert", "satisfaction"),
    ],
    "usability": [
        ("How would you describe the ease of completing common tasks in {topic}?", "likert", "agreement"),
        ("When you tried to {action}, how would you describe that experience?", "open_text", None),
    ],
    "frequency": [
        ("How often do you typically interact with {topic}?", "likert", "frequency"),
        ("In a typical week, how many times do you use {topic}?", "numeric", None),
    ],
    "preference": [
        ("Which of the following best describes your preferred way of working with {topic}?", "single_choice", None),
        ("Rank the following aspects of {topic} from most to least important to you.", "ranking", None),
    ],
    "motivation": [
        ("What is the main reason you use {topic}?", "open_text", None),
        ("Which of the following best describes why you started using {topic}?", "single_choice", None),
    ],
    "barriers": [
        ("What, if anything, has made {topic} harder to use than you expected?", "open_text", None),
        ("Which of the following have you found challenging when using {topic}? Select all that apply.", "multi_choice", None),
    ],
    "trust": [
        ("How would you describe your confidence in {topic}?", "likert", "agreement"),
        ("Thinking about {topic}, how comfortable are you sharing information with it?", "likert", "agreement"),
    ],
    "recommendation": [
        ("How likely are you to recommend {topic} to a colleague?", "rating", None),
        ("What would need to change for you to recommend {topic}?", "open_text", None),
    ],
    "value": [
        ("How would you describe the value {topic} provides for the time you spend with it?", "likert", "agreement"),
        ("What outcomes have you achieved using {topic}?", "open_text", None),
    ],
}

# Default fallback constructs if the brief has none specified
DEFAULT_CONSTRUCTS = ["satisfaction", "usability", "frequency", "motivation", "barriers", "recommendation"]


def _make_id(index: int) -> str:
    return f"Q{index + 1:03d}"


def _build_scale(scale_type: str, scale_construct: str | None) -> ResponseScale | None:
    if scale_type == "likert" and scale_construct:
        return build_balanced_likert(points=5, construct=scale_construct)
    if scale_type == "rating":
        return ResponseScale(
            scale_type="rating",
            points=11,
            labels=[str(i) for i in range(0, 11)],
            anchors={"low": "0 — Not at all likely", "high": "10 — Extremely likely"},
            includes_neutral=False,
            includes_na=False,
            is_balanced=True,
        )
    if scale_type == "numeric":
        return ResponseScale(
            scale_type="open",
            points=0,
            labels=[],
            anchors={"unit": "times per week"},
            includes_neutral=False,
            includes_na=False,
            is_balanced=True,
        )
    if scale_type == "open_text":
        return ResponseScale(scale_type="open", points=0, labels=[], anchors={}, includes_neutral=False, includes_na=False, is_balanced=True)
    if scale_type in {"single_choice", "multi_choice"}:
        return ResponseScale(
            scale_type="nominal",
            points=0,
            labels=["Option A", "Option B", "Option C", "Other"],
            anchors={},
            includes_neutral=False,
            includes_na=False,
            is_balanced=True,
        )
    if scale_type == "ranking":
        return ResponseScale(
            scale_type="ordinal",
            points=0,
            labels=["Aspect 1", "Aspect 2", "Aspect 3", "Aspect 4"],
            anchors={},
            includes_neutral=False,
            includes_na=False,
            is_balanced=True,
        )
    if scale_type == "yes_no":
        return ResponseScale(
            scale_type="nominal",
            points=2,
            labels=["Yes", "No"],
            anchors={},
            includes_neutral=False,
            includes_na=False,
            is_balanced=True,
        )
    return None


def generate_questions(brief: ResearchBrief) -> list[SurveyQuestion]:
    """Generate a survey from a brief using rule-based templates.

    Each question is created from a construct template, slotting in the topic.
    The resulting questions are deliberately neutral and bias-low by construction.
    """
    constructs = brief.constructs or DEFAULT_CONSTRUCTS
    questions: list[SurveyQuestion] = []

    target_count = max(1, brief.desired_length)

    # Round-robin through constructs until we hit target_count
    i = 0
    construct_index = 0
    while len(questions) < target_count:
        construct = constructs[construct_index % len(constructs)]
        if construct not in CONSTRUCT_TEMPLATES:
            # If a custom construct, use a generic template
            templates = [(f"In your own words, how would you describe {{topic}} as it relates to {construct}?", "open_text", None)]
        else:
            templates = CONSTRUCT_TEMPLATES[construct]

        template_index = (i // len(constructs)) % len(templates)
        text_tpl, scale_type, scale_construct = templates[template_index]
        text = text_tpl.format(topic=brief.topic, action="complete a task")
        scale = _build_scale(scale_type, scale_construct)
        q = SurveyQuestion(
            id=_make_id(i),
            text=text,
            question_type=scale_type,
            construct=construct,
            rationale=f"Captures '{construct}' aligned with the brief's objectives.",
            scale=scale,
        )
        questions.append(q)
        construct_index += 1
        i += 1

    return questions
