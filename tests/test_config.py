from azure_agent_harness.config import Settings


def test_default_settings_are_development_safe():
    settings = Settings()
    assert settings.app_env
    assert settings.agent_version
