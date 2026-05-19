"""Core dataclasses for survey-designer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

# Question types
QUESTION_TYPES = (
    "single_choice",
    "multi_choice",
    "likert",
    "rating",
    "ranking",
    "open_text",
    "numeric",
    "yes_no",
)


@dataclass
class ResponseScale:
    """A response scale for a survey question."""

    scale_type: str  # likert | rating | ordinal | nominal | open
    points: int = 0  # number of scale points (0 for open)
    labels: list[str] = field(default_factory=list)
    anchors: dict[str, str] = field(default_factory=dict)  # e.g. {"low": "Strongly disagree"}
    includes_neutral: bool = False
    includes_na: bool = False
    is_balanced: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BiasFlag:
    """A bias issue detected in a question."""

    bias_type: str  # leading | double_barreled | loaded | jargon | absolute | double_negative | assumption | acquiescence
    severity: str  # low | medium | high
    excerpt: str
    rationale: str
    rewrite_suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScaleValidation:
    """Validation results for a response scale."""

    is_valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SurveyQuestion:
    """A single survey question with metadata."""

    id: str
    text: str
    question_type: str
    construct: str = ""  # what this question measures
    rationale: str = ""  # why this question is asked
    scale: Optional[ResponseScale] = None
    bias_flags: list[BiasFlag] = field(default_factory=list)
    scale_validation: Optional[ScaleValidation] = None
    quality_score: float = 0.0  # 0.0 to 1.0
    # LLM enrichment fields (null when rule-based only)
    llm_rewrite: Optional[str] = None
    llm_rationale: Optional[str] = None
    llm_alternative_phrasings: Optional[list[str]] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class ResearchBrief:
    """A research brief used to generate a survey."""

    topic: str
    objectives: list[str] = field(default_factory=list)
    audience: str = ""
    constructs: list[str] = field(default_factory=list)
    method_notes: str = ""
    desired_length: int = 12  # target number of questions

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Survey:
    """A complete survey with quality metadata."""

    title: str
    brief: ResearchBrief
    questions: list[SurveyQuestion] = field(default_factory=list)
    overall_quality_score: float = 0.0
    bias_count: int = 0
    scale_issue_count: int = 0
    # LLM enrichment metadata
    llm_backend: Optional[str] = None
    llm_summary: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "brief": self.brief.to_dict(),
            "questions": [q.to_dict() for q in self.questions],
            "overall_quality_score": self.overall_quality_score,
            "bias_count": self.bias_count,
            "scale_issue_count": self.scale_issue_count,
            "llm_backend": self.llm_backend,
            "llm_summary": self.llm_summary,
        }
