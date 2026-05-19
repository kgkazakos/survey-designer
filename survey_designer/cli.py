"""Click CLI for survey-designer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core import audit_questions, build_survey
from .llm_enrichment import DEFAULT_BACKEND, SUPPORTED_BACKENDS, is_available
from .models import ResearchBrief, SurveyQuestion

console = Console()


def _load_brief(brief_path: Path) -> ResearchBrief:
    raw = json.loads(brief_path.read_text())
    return ResearchBrief(
        topic=raw.get("topic", "the product"),
        objectives=raw.get("objectives", []),
        audience=raw.get("audience", ""),
        constructs=raw.get("constructs", []),
        method_notes=raw.get("method_notes", ""),
        desired_length=raw.get("desired_length", 12),
    )


@click.group()
@click.version_option()
def cli() -> None:
    """survey-designer — AI-assisted survey generation, bias detection, and scale validation."""


@cli.command()
@click.option("--brief", "brief_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option(
    "--llm-backend",
    type=click.Choice(list(SUPPORTED_BACKENDS.keys()), case_sensitive=False),
    default=DEFAULT_BACKEND,
    show_default=True,
    help="LLM backend for enrichment. Defaults to Claude Opus.",
)
@click.option("--no-llm", is_flag=True, default=False, help="Disable LLM enrichment.")
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None)
@click.option("--json-output", is_flag=True, default=False, help="Emit JSON only to stdout.")
def generate(
    brief_path: Path,
    llm_backend: str,
    no_llm: bool,
    output_path: Path | None,
    json_output: bool,
) -> None:
    """Generate a survey from a research brief and audit it for bias and scale issues."""
    brief = _load_brief(brief_path)
    survey = build_survey(brief, enrich_with_llm=not no_llm, llm_backend=llm_backend)

    if output_path:
        output_path.write_text(json.dumps(survey.to_dict(), indent=2))
        if not json_output:
            console.print(f"[green]Saved survey to {output_path}[/green]")

    if json_output:
        click.echo(json.dumps(survey.to_dict(), indent=2))
        return

    _render_survey(survey)


@cli.command()
@click.option("--survey", "survey_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--json-output", is_flag=True, default=False)
def audit(survey_path: Path, json_output: bool) -> None:
    """Re-audit an existing survey JSON file for bias and scale issues."""
    raw = json.loads(survey_path.read_text())
    questions = [_question_from_dict(q) for q in raw.get("questions", [])]
    audit_questions(questions)

    if json_output:
        click.echo(json.dumps([q.to_dict() for q in questions], indent=2))
        return

    table = Table(title="Bias & Scale Audit", show_lines=True)
    table.add_column("Q", no_wrap=True)
    table.add_column("Question", overflow="fold")
    table.add_column("Score", justify="right")
    table.add_column("Bias flags", justify="right")
    table.add_column("Scale issues", justify="right")
    for q in questions:
        table.add_row(
            q.id,
            q.text,
            f"{q.quality_score:.2f}",
            str(len(q.bias_flags)),
            str(len(q.scale_validation.issues) if q.scale_validation else 0),
        )
    console.print(table)


@cli.command()
def backends() -> None:
    """List supported LLM backends and their availability."""
    table = Table(title="Supported LLM backends")
    table.add_column("Model")
    table.add_column("API key env var")
    table.add_column("Available?")
    for backend, env_var in SUPPORTED_BACKENDS.items():
        avail = "[green]yes[/green]" if is_available(backend) else "[yellow]not configured[/yellow]"
        table.add_row(backend, env_var, avail)
    console.print(table)


def _question_from_dict(d: dict) -> SurveyQuestion:
    """Reconstruct a SurveyQuestion from a dict (loose; ignores LLM fields)."""
    from .models import ResponseScale

    scale = None
    if d.get("scale"):
        scale = ResponseScale(**d["scale"])

    return SurveyQuestion(
        id=d.get("id", ""),
        text=d.get("text", ""),
        question_type=d.get("question_type", "open_text"),
        construct=d.get("construct", ""),
        rationale=d.get("rationale", ""),
        scale=scale,
    )


def _render_survey(survey) -> None:
    """Pretty-print a survey to the console."""
    header = Text()
    header.append(survey.title, style="bold")
    header.append(f"\nOverall quality score: {survey.overall_quality_score:.2f}", style="cyan")
    header.append(f"\nBias flags: {survey.bias_count}", style="yellow")
    header.append(f"\nScale issues: {survey.scale_issue_count}", style="yellow")
    if survey.llm_backend:
        header.append(f"\nLLM backend: {survey.llm_backend}", style="magenta")
    console.print(Panel(header, title="Survey overview"))

    if survey.llm_summary:
        console.print(Panel(survey.llm_summary, title="LLM summary"))

    for q in survey.questions:
        body = Text()
        body.append(f"{q.text}\n", style="bold")
        body.append(f"Construct: {q.construct} · Type: {q.question_type}\n", style="dim")
        body.append(f"Quality score: {q.quality_score:.2f}\n", style="cyan")
        if q.bias_flags:
            body.append("Bias flags:\n", style="yellow")
            for f in q.bias_flags:
                body.append(f"  · {f.bias_type} ({f.severity}): {f.rationale}\n")
        if q.scale_validation and (q.scale_validation.issues or q.scale_validation.warnings):
            body.append("Scale:\n", style="yellow")
            for issue in q.scale_validation.issues:
                body.append(f"  · {issue}\n")
            for warn in q.scale_validation.warnings:
                body.append(f"  · {warn}\n")
        if q.llm_rewrite:
            body.append(f"LLM rewrite: {q.llm_rewrite}\n", style="green")
        if q.llm_rationale:
            body.append(f"LLM rationale: {q.llm_rationale}\n", style="dim")
        console.print(Panel(body, title=f"[{q.id}]"))


if __name__ == "__main__":
    cli()
    sys.exit(0)
