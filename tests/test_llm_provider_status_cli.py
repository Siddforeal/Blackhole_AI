import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_llm_provider_status_defaults_to_disabled():
    result = runner.invoke(app, ["llm-provider-status"])

    assert result.exit_code == 0
    assert "LLM Provider Gate Status" in result.output
    assert "disabled" in result.output
    assert "False" in result.output
    assert "LLM provider execution is disabled by default." in result.output


def test_llm_provider_status_writes_json_without_provider_execution(tmp_path):
    output_file = tmp_path / "provider-status.json"

    result = runner.invoke(
        app,
        [
            "llm-provider-status",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    data = json.loads(output_file.read_text())

    assert data["config"]["provider_name"] == "disabled"
    assert data["config"]["allow_provider_execution"] is False
    assert data["config"]["require_prompt_audit_pass"] is True
    assert data["gate"]["allowed"] is False
    assert data["gate"]["provider_name"] == "disabled"
    assert "disabled by default" in data["gate"]["reason"]
    assert "does not read API keys" in data["notes"]


def test_llm_provider_status_blocks_unknown_provider_even_with_opt_in():
    result = runner.invoke(
        app,
        [
            "llm-provider-status",
            "--provider",
            "openai",
            "--allow-provider-execution",
            "--model",
            "gpt-example",
        ],
    )

    assert result.exit_code == 0
    assert "openai" in result.output
    assert "Unsupported LLM provider" in result.output
