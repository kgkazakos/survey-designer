"""Response scale validation."""

from __future__ import annotations

from .models import ResponseScale, ScaleValidation


def _is_balanced(labels: list[str]) -> bool:
    """Check if scale labels are balanced (equal positive/negative).

    Checks negative markers first so that 'disagree' is not also counted
    as 'agree'. Labels containing a negative marker are classified as
    negative even if a positive marker would otherwise also match.
    """
    if not labels:
        return True
    # Order matters: check negatives first since 'disagree' contains 'agree'
    negative_markers = ("disagree", "dissatisfied", "unlikely", "rarely", "difficult", "bad", "low", "negative")
    positive_markers = ("agree", "satisfied", "likely", "often", "easy", "good", "high", "positive")
    neutral_markers = ("neither", "neutral", "neither agree nor disagree")

    pos = 0
    neg = 0
    for label in labels:
        low = label.lower()
        if any(m in low for m in neutral_markers):
            continue
        if any(m in low for m in negative_markers):
            neg += 1
        elif any(m in low for m in positive_markers):
            pos += 1

    if pos == 0 and neg == 0:
        # Numeric or descriptive — assume balanced
        return True
    return abs(pos - neg) <= 1


def validate_scale(scale: ResponseScale) -> ScaleValidation:
    """Validate a single response scale and return a ScaleValidation object."""
    issues: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if scale.scale_type == "likert":
        # Likert scales should be 5 or 7 points typically
        if scale.points < 5:
            issues.append(f"Likert scale has only {scale.points} points — typical range is 5 or 7.")
        elif scale.points > 9:
            warnings.append(f"Likert scale has {scale.points} points — granularity may exceed respondent discrimination.")

        # Even-numbered scales force a forced-choice (no neutral)
        if scale.points % 2 == 0 and scale.includes_neutral:
            issues.append("Scale is even-numbered but flagged as including a neutral point — these are contradictory.")

        if scale.points % 2 == 0 and not scale.includes_neutral:
            recommendations.append("Forced-choice (even) scales push respondents toward a side — consider adding a neutral option unless intentional.")

        # Balance check
        if scale.labels and not _is_balanced(scale.labels):
            issues.append("Likert scale labels are not balanced — equal positive and negative anchors are recommended.")

        # Anchor presence
        if not scale.anchors:
            recommendations.append("Likert scales benefit from clear low and high anchors (e.g. 'Strongly disagree' to 'Strongly agree').")

    elif scale.scale_type == "rating":
        if scale.points == 0:
            issues.append("Rating scale must specify number of points.")
        elif scale.points < 3:
            issues.append(f"Rating scale has only {scale.points} points — too coarse for most use cases.")
        elif scale.points > 11:
            warnings.append(f"Rating scale has {scale.points} points — many respondents struggle past 7.")

        if not scale.anchors:
            recommendations.append("Numeric rating scales need anchor labels (e.g. 1 = 'Very poor', 10 = 'Excellent').")

    elif scale.scale_type == "ordinal":
        if not scale.labels:
            issues.append("Ordinal scale must include category labels.")
        elif len(scale.labels) < 3:
            warnings.append(f"Ordinal scale has only {len(scale.labels)} categories.")

    elif scale.scale_type == "nominal":
        if not scale.labels:
            issues.append("Nominal scale must include category labels.")
        elif len(scale.labels) < 2:
            issues.append("Nominal scale must have at least 2 options.")

        # Check for mutually exclusive issues (very basic heuristic: duplicate labels)
        if scale.labels and len(scale.labels) != len(set(scale.labels)):
            issues.append("Nominal scale has duplicate labels.")

        # Recommend 'Other' / 'Prefer not to say' for exhaustiveness
        if scale.labels and not any(label.lower() in {"other", "none of the above", "prefer not to say", "not applicable"} for label in scale.labels):
            recommendations.append("Consider adding 'Other' or 'Prefer not to say' to ensure exhaustiveness.")

    elif scale.scale_type == "open":
        # No scale validation for open-ended
        pass

    else:
        issues.append(f"Unknown scale type: '{scale.scale_type}'.")

    is_valid = len(issues) == 0
    return ScaleValidation(
        is_valid=is_valid,
        issues=issues,
        warnings=warnings,
        recommendations=recommendations,
    )


def build_balanced_likert(points: int = 5, construct: str = "agreement") -> ResponseScale:
    """Build a properly balanced Likert scale of the given length."""
    if construct == "agreement":
        if points == 5:
            labels = ["Strongly disagree", "Disagree", "Neither agree nor disagree", "Agree", "Strongly agree"]
        elif points == 7:
            labels = [
                "Strongly disagree",
                "Disagree",
                "Somewhat disagree",
                "Neither agree nor disagree",
                "Somewhat agree",
                "Agree",
                "Strongly agree",
            ]
        else:
            labels = []
        anchors = {"low": "Strongly disagree", "high": "Strongly agree"}
    elif construct == "frequency":
        if points == 5:
            labels = ["Never", "Rarely", "Sometimes", "Often", "Always"]
        elif points == 7:
            labels = ["Never", "Very rarely", "Rarely", "Sometimes", "Often", "Very often", "Always"]
        else:
            labels = []
        anchors = {"low": "Never", "high": "Always"}
    elif construct == "satisfaction":
        if points == 5:
            labels = ["Very dissatisfied", "Dissatisfied", "Neither", "Satisfied", "Very satisfied"]
        elif points == 7:
            labels = [
                "Very dissatisfied",
                "Dissatisfied",
                "Somewhat dissatisfied",
                "Neither",
                "Somewhat satisfied",
                "Satisfied",
                "Very satisfied",
            ]
        else:
            labels = []
        anchors = {"low": "Very dissatisfied", "high": "Very satisfied"}
    else:
        labels = []
        anchors = {}

    return ResponseScale(
        scale_type="likert",
        points=points,
        labels=labels,
        anchors=anchors,
        includes_neutral=points % 2 == 1,
        includes_na=False,
        is_balanced=True,
    )
