"""Rule-based bias detection for survey questions."""

from __future__ import annotations

import re

from .models import BiasFlag

# Leading question patterns
LEADING_PATTERNS = [
    (r"\bdon'?t you (?:think|agree|feel|believe)\b", "Asks for agreement directly"),
    (r"\bwouldn'?t you\b", "Hypothetical agreement framing"),
    (r"\bisn'?t it (?:true|obvious|clear)\b", "Presupposes a conclusion"),
    (r"\bsurely\b", "Implies the answer is obvious"),
    (r"\bobviously\b", "Implies the answer is obvious"),
    (r"\bof course\b", "Implies the answer is obvious"),
    (r"\bclearly\b", "Implies the answer is obvious"),
    (r"\bas (?:we )?(?:all )?know\b", "Presupposes shared belief"),
    (r"\bhow (?:much|often) do you (?:enjoy|love|like)\b", "Assumes positive sentiment"),
    (r"\bhow (?:much|often) do you (?:hate|dislike)\b", "Assumes negative sentiment"),
]

# Loaded / emotionally charged terms
LOADED_TERMS = {
    "amazing": "Positively loaded — biases toward agreement",
    "awful": "Negatively loaded — biases against",
    "terrible": "Negatively loaded — biases against",
    "fantastic": "Positively loaded — biases toward agreement",
    "wonderful": "Positively loaded — biases toward agreement",
    "horrible": "Negatively loaded — biases against",
    "disastrous": "Negatively loaded — biases against",
    "revolutionary": "Positively loaded — biases toward agreement",
    "ground-breaking": "Positively loaded — biases toward agreement",
    "groundbreaking": "Positively loaded — biases toward agreement",
    "innovative": "Positively loaded — biases toward agreement",
    "brilliant": "Positively loaded — biases toward agreement",
    "useless": "Negatively loaded — biases against",
    "pointless": "Negatively loaded — biases against",
    "perfect": "Positively loaded — biases toward agreement",
    "frustrating": "Negatively loaded — biases against",
    "delightful": "Positively loaded — biases toward agreement",
}

# Absolute language
ABSOLUTE_TERMS = {
    "always",
    "never",
    "every",
    "everyone",
    "everybody",
    "no one",
    "nobody",
    "all",
    "none",
    "completely",
    "totally",
    "absolutely",
    "entirely",
    "fully",
}

# Common UX/research jargon that survey respondents may not understand
JARGON_TERMS = {
    "onboarding": "Industry jargon",
    "user journey": "Industry jargon",
    "engagement metric": "Technical/internal term",
    "retention": "Business jargon",
    "ux": "Industry acronym",
    "ui": "Industry acronym",
    "kpi": "Business acronym",
    "ctr": "Industry acronym",
    "mau": "Internal acronym",
    "dau": "Internal acronym",
    "stickiness": "Industry jargon",
    "north star metric": "Internal jargon",
    "value proposition": "Business jargon",
    "minimum viable product": "Industry jargon",
    "mvp": "Industry acronym",
    "stakeholder": "Business jargon",
    "low-friction": "Industry jargon",
    "frictionless": "Industry jargon",
    "actionable": "Business jargon",
    "synergy": "Business jargon",
    "leverage": "Business jargon",
    "operationalise": "Business jargon",
    "operationalize": "Business jargon",
}

# Double-barreled signal words
DOUBLE_BARRELED_CONNECTORS = [
    r"\b(\w+)\s+and\s+(\w+)\b",  # generic and — will refine in code
    r"\b(?:fast and easy|easy and fast)\b",
    r"\b(?:simple and clear|clear and simple)\b",
    r"\b(?:useful and easy)\b",
]


def detect_leading(text: str) -> list[BiasFlag]:
    """Detect leading question patterns."""
    flags: list[BiasFlag] = []
    lower = text.lower()
    for pattern, rationale in LEADING_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            flags.append(
                BiasFlag(
                    bias_type="leading",
                    severity="high",
                    excerpt=match.group(0),
                    rationale=rationale,
                    rewrite_suggestion="Reframe neutrally — e.g. 'How would you describe...?'",
                )
            )
    return flags


def detect_loaded(text: str) -> list[BiasFlag]:
    """Detect emotionally loaded terms."""
    flags: list[BiasFlag] = []
    lower = text.lower()
    for term, rationale in LOADED_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", lower):
            flags.append(
                BiasFlag(
                    bias_type="loaded",
                    severity="medium",
                    excerpt=term,
                    rationale=rationale,
                    rewrite_suggestion=f"Replace '{term}' with a neutral descriptor.",
                )
            )
    return flags


def detect_absolutes(text: str) -> list[BiasFlag]:
    """Detect absolute language."""
    flags: list[BiasFlag] = []
    lower = text.lower()
    for term in ABSOLUTE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lower):
            flags.append(
                BiasFlag(
                    bias_type="absolute",
                    severity="low",
                    excerpt=term,
                    rationale="Absolute language forces extreme responses and limits nuance.",
                    rewrite_suggestion=f"Soften '{term}' with phrasing like 'often' or 'typically'.",
                )
            )
    return flags


def detect_jargon(text: str) -> list[BiasFlag]:
    """Detect industry jargon participants may not understand."""
    flags: list[BiasFlag] = []
    lower = text.lower()
    for term, rationale in JARGON_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", lower):
            flags.append(
                BiasFlag(
                    bias_type="jargon",
                    severity="medium",
                    excerpt=term,
                    rationale=rationale,
                    rewrite_suggestion=f"Define '{term}' in respondent-friendly language or replace it.",
                )
            )
    return flags


def detect_double_barreled(text: str) -> list[BiasFlag]:
    """Detect double-barreled questions.

    A question is double-barreled if it asks two things at once.
    Heuristic: presence of 'and' or 'or' joining two distinct adjectives,
    nouns, or actions where the respondent could feel differently about each.
    """
    flags: list[BiasFlag] = []
    lower = text.lower()

    # Look for adjective/noun pairs around 'and'/'or' that suggest distinct dimensions
    risk_pairs = [
        ("fast", "easy"),
        ("easy", "fast"),
        ("useful", "intuitive"),
        ("intuitive", "useful"),
        ("simple", "powerful"),
        ("powerful", "simple"),
        ("reliable", "fast"),
        ("fast", "reliable"),
        ("secure", "convenient"),
        ("convenient", "secure"),
        ("affordable", "high-quality"),
        ("high-quality", "affordable"),
        ("flexible", "structured"),
        ("structured", "flexible"),
        ("clear", "comprehensive"),
        ("comprehensive", "clear"),
    ]
    for a, b in risk_pairs:
        pattern = rf"\b{re.escape(a)}\s+(?:and|or)\s+{re.escape(b)}\b"
        match = re.search(pattern, lower)
        if match:
            flags.append(
                BiasFlag(
                    bias_type="double_barreled",
                    severity="high",
                    excerpt=match.group(0),
                    rationale=f"'{a}' and '{b}' are distinct dimensions — respondents may feel differently about each.",
                    rewrite_suggestion=f"Split into two questions, one about '{a}' and one about '{b}'.",
                )
            )

    # Generic catch — question has multiple verbs joined by 'and'
    verb_pattern = r"\b(rate|evaluate|describe|assess)\s+(?:the\s+)?\w+\s+and\s+\w+"
    if re.search(verb_pattern, lower):
        # Only flag if no specific pair caught it
        if not any(f.bias_type == "double_barreled" for f in flags):
            flags.append(
                BiasFlag(
                    bias_type="double_barreled",
                    severity="medium",
                    excerpt="multiple dimensions joined",
                    rationale="The question may be asking about more than one dimension at once.",
                    rewrite_suggestion="Consider splitting into separate questions.",
                )
            )

    return flags


def detect_double_negative(text: str) -> list[BiasFlag]:
    """Detect double negatives."""
    flags: list[BiasFlag] = []
    lower = text.lower()
    # Patterns like "not unhappy", "never fail to", etc.
    patterns = [
        r"\bnot\s+un\w+",
        r"\bnever\s+(?:not|fail to)\b",
        r"\bno\s+(?:un\w+|in\w+)\b",
        r"\bdon'?t\s+(?:un\w+|dis\w+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            flags.append(
                BiasFlag(
                    bias_type="double_negative",
                    severity="medium",
                    excerpt=match.group(0),
                    rationale="Double negatives confuse respondents and increase error rates.",
                    rewrite_suggestion="Rephrase using a single positive or negative form.",
                )
            )
    return flags


def detect_assumption(text: str) -> list[BiasFlag]:
    """Detect questions that assume a prior condition without an escape option.

    Examples: 'How often do you use feature X?' assumes the respondent uses it.
    """
    flags: list[BiasFlag] = []
    lower = text.lower()
    patterns = [
        (r"\bhow (?:often|frequently|much) do you (?:use|engage|interact)\b",
         "Assumes the respondent uses/engages — include an 'I don't use this' option."),
        (r"\bwhen you (?:use|open|access)\b",
         "Assumes the action occurs — verify with a screening question first."),
        (r"\bsince you (?:started|began|joined)\b",
         "Assumes a starting event — confirm it applies to the respondent."),
    ]
    for pattern, rationale in patterns:
        match = re.search(pattern, lower)
        if match:
            flags.append(
                BiasFlag(
                    bias_type="assumption",
                    severity="medium",
                    excerpt=match.group(0),
                    rationale=rationale,
                    rewrite_suggestion="Add an escape option (e.g. 'Not applicable') or screen first.",
                )
            )
    return flags


def detect_acquiescence(text: str) -> list[BiasFlag]:
    """Detect acquiescence bias — questions phrased so 'agree' is the easy answer."""
    flags: list[BiasFlag] = []
    lower = text.lower()
    # Heuristic: starts with "I" + agreement framing, no negative alternative
    patterns = [
        r"^\s*i\s+(?:am satisfied|am happy|enjoy|love|like|find)\b",
        r"\bdo you agree (?:that|with)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            flags.append(
                BiasFlag(
                    bias_type="acquiescence",
                    severity="low",
                    excerpt=match.group(0),
                    rationale="Statements like 'I am satisfied with X' invite yes-bias. Mix in reverse-coded items.",
                    rewrite_suggestion="Reframe as a bipolar scale or balance with a reverse-coded item.",
                )
            )
    return flags


def detect_all_bias(text: str) -> list[BiasFlag]:
    """Run all bias detectors on a question and return combined flags."""
    flags: list[BiasFlag] = []
    flags.extend(detect_leading(text))
    flags.extend(detect_loaded(text))
    flags.extend(detect_absolutes(text))
    flags.extend(detect_jargon(text))
    flags.extend(detect_double_barreled(text))
    flags.extend(detect_double_negative(text))
    flags.extend(detect_assumption(text))
    flags.extend(detect_acquiescence(text))
    return flags
