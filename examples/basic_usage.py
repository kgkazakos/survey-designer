"""Basic usage example for survey-designer."""

from survey_designer import ResearchBrief, build_survey

brief = ResearchBrief(
    topic="our new analytics dashboard",
    objectives=[
        "Measure satisfaction with the redesigned dashboard",
        "Identify the main barriers to daily use",
        "Estimate likelihood to recommend",
    ],
    audience="Active users in the last 30 days",
    constructs=["satisfaction", "usability", "barriers", "recommendation", "frequency"],
    desired_length=10,
)

# Rule-based only (no API key required)
survey = build_survey(brief, enrich_with_llm=False)

print(f"Generated {len(survey.questions)} questions.")
print(f"Overall quality score: {survey.overall_quality_score:.2f}")
print(f"Bias flags found: {survey.bias_count}")
print(f"Scale issues: {survey.scale_issue_count}")

# Inspect the first question
q = survey.questions[0]
print(f"\nQ1: {q.text}")
print(f"  Construct: {q.construct}")
print(f"  Quality: {q.quality_score:.2f}")
if q.scale:
    print(f"  Scale: {q.scale.scale_type} ({len(q.scale.labels)} labels)")

# To enable LLM enrichment, set ANTHROPIC_API_KEY (or GEMINI_API_KEY / OPENAI_API_KEY):
# survey = build_survey(brief, enrich_with_llm=True, llm_backend="anthropic/claude-opus-4-7")
