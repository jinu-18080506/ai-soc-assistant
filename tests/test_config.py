from soc.config import DEFAULT_BASE_URL, Settings, load_settings, parse_env_file


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_basic_file(tmp_path):
    file = write(tmp_path / ".env", "# comment\n\nAI_API_KEY=abc123\nAI_MODEL = flash-x\n")
    assert parse_env_file(file) == {"AI_API_KEY": "abc123", "AI_MODEL": "flash-x"}


def test_parse_strips_quotes_and_export(tmp_path):
    file = write(tmp_path / ".env", 'export AI_API_KEY="abc"\nAI_MODEL=\'m\'\n')
    assert parse_env_file(file) == {"AI_API_KEY": "abc", "AI_MODEL": "m"}


def test_parse_ignores_lines_without_equals(tmp_path):
    file = write(tmp_path / ".env", "just some text\nAI_API_KEY=k\n")
    assert parse_env_file(file) == {"AI_API_KEY": "k"}


def test_missing_file_gives_empty(tmp_path):
    assert parse_env_file(tmp_path / "nope.env") == {}


def test_defaults_when_nothing_set(tmp_path):
    settings = load_settings(tmp_path / "nope.env", environ={})
    assert settings.api_key == "" and settings.model == ""
    assert settings.base_url == DEFAULT_BASE_URL


def test_environment_overrides_file(tmp_path):
    file = write(tmp_path / ".env", "AI_API_KEY=from-file\nAI_MODEL=file-model\n")
    settings = load_settings(file, environ={"AI_API_KEY": "from-env"})
    assert settings.api_key == "from-env"
    assert settings.model == "file-model"


def test_empty_value_falls_back_to_default_url(tmp_path):
    file = write(tmp_path / ".env", "AI_BASE_URL=\n")
    assert load_settings(file, environ={}).base_url == DEFAULT_BASE_URL


def test_api_key_hidden_from_repr():
    assert "secret" not in repr(Settings(api_key="secret"))
