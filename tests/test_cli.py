"""Tests for CLI."""

import json
from pathlib import Path

from click.testing import CliRunner

from survey_designer.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "survey-designer" in result.output


def test_cli_backends_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["backends"])
    assert result.exit_code == 0
    assert "anthropic/claude-opus-4-7" in result.output


def test_cli_generate_json_output(tmp_path: Path):
    brief = {
        "topic": "our dashboard",
        "objectives": ["Measure satisfaction"],
        "audience": "Users",
        "constructs": ["satisfaction", "usability"],
        "desired_length": 4,
    }
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief))

    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--brief", str(brief_path), "--no-llm", "--json-output"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "questions" in data
    assert len(data["questions"]) == 4


def test_cli_generate_to_file(tmp_path: Path):
    brief = {
        "topic": "feature X",
        "objectives": ["Find barriers"],
        "constructs": ["barriers"],
        "desired_length": 3,
    }
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief))
    output_path = tmp_path / "survey.json"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["generate", "--brief", str(brief_path), "--no-llm", "--output", str(output_path)],
    )
    assert result.exit_code == 0
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert len(data["questions"]) == 3


def test_cli_audit_command(tmp_path: Path):
    survey_data = {
        "questions": [
            {
                "id": "Q1",
                "text": "Don't you think this amazing feature is great?",
                "question_type": "open_text",
                "construct": "satisfaction",
                "rationale": "test",
            }
        ]
    }
    survey_path = tmp_path / "survey.json"
    survey_path.write_text(json.dumps(survey_data))

    runner = CliRunner()
    result = runner.invoke(cli, ["audit", "--survey", str(survey_path), "--json-output"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert len(data[0]["bias_flags"]) > 0
