from bugintel.ui.intro import (
    IntroConfig,
    UFO_ASCII,
    render_intro_panel,
    should_show_intro,
)


def test_ufo_ascii_exists():
    assert "⣿⣿⣿" in UFO_ASCII
    assert "⠿⠿" in UFO_ASCII
    assert len(UFO_ASCII.splitlines()) >= 10


def test_render_intro_panel_includes_status_text():
    panel = render_intro_panel("0.8.0-dev")
    rendered = str(panel.renderable)

    assert "Welcome to BugIntel AI Workbench" in rendered
    assert "Scope Guard online" in rendered
    assert "Evidence engine ready" in rendered
    assert "Research planner ready" in rendered
    assert "LLM bridge safe-mode" in rendered
    assert "⣿⣿⣿" in rendered


def test_should_show_intro_respects_no_intro_env(monkeypatch):
    monkeypatch.setenv("BUGINTEL_NO_INTRO", "1")

    assert should_show_intro(force=False) is False
    assert should_show_intro(force=True) is True


def test_intro_config_defaults_are_safe():
    config = IntroConfig()

    assert config.force is False
    assert config.clear_screen is True
