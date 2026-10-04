from azure_agent_harness.config import Settings


def test_default_settings_are_development_safe():
    settings = Settings()
    assert settings.app_env
    assert settings.agent_version


def test_settings_read_environment_at_instantiation(monkeypatch):
    # Hosts call load_dotenv() after importing config; values must still apply.
    monkeypatch.setenv("AUTH_MODE", " Entra ")
    monkeypatch.setenv("APP_ENV", "production")
    settings = Settings()
    assert settings.auth_mode == "entra"
    assert settings.app_env == "production"
