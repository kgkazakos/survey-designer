"""survey-designer: AI-assisted survey question generation with bias detection and scale validation.

Part of the CPR Orbital Series — Tool 28 of 40.
"""

from .bias_detector import detect_all_bias
from .core import audit_question, audit_questions, build_survey
from .models import (
    BiasFlag,
    ResearchBrief,
    ResponseScale,
    ScaleValidation,
    Survey,
    SurveyQuestion,
)
from .question_generator import generate_questions
from .scale_validator import build_balanced_likert, validate_scale

__version__ = "0.1.0"

__all__ = [
    "BiasFlag",
    "ResearchBrief",
    "ResponseScale",
    "ScaleValidation",
    "Survey",
    "SurveyQuestion",
    "detect_all_bias",
    "validate_scale",
    "build_balanced_likert",
    "generate_questions",
    "audit_question",
    "audit_questions",
    "build_survey",
]
