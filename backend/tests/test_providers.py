import socket

import pytest

from app import providers
from app.config import Settings
from app.providers.base import ProviderError, with_retry


class StatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def test_retry_recovers_from_rate_limit(monkeypatch):
    monkeypatch.setattr("app.providers.base.time.sleep", lambda s: None)
    calls = iter([StatusError(429), StatusError(503), "ok"])

    def call():
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    assert with_retry("test", call) == "ok"


def test_permanent_error_is_not_retried():
    attempts = []

    def call():
        attempts.append(1)
        raise StatusError(401)

    with pytest.raises(ProviderError, match="test: HTTP 401"):
        with_retry("test", call)
    assert len(attempts) == 1


@pytest.mark.parametrize("error", [
    type("GeminiError", (Exception,), {"code": 400, "message": "API key not valid."})("400 INVALID_ARGUMENT. {...}"),
    type("OpenAIError", (Exception,), {"status_code": 401, "body": {"message": "API key not valid."}})("Error {...}"),
])
def test_provider_error_shows_the_message_not_the_dump(error):
    def call():
        raise error

    with pytest.raises(ProviderError) as caught:
        with_retry("x", call)
    assert str(caught.value) in ("x: 400 API key not valid.", "x: 401 API key not valid.")


def test_provider_defaults_follow_llm_provider():
    gemini = Settings(_env_file=None, database_url="postgresql://x/y", gemini_api_key="k",
                      chat_model="", embed_model="")
    openai = Settings(_env_file=None, database_url="postgresql://x/y", llm_provider="openai", openai_api_key="k",
                      chat_model="", embed_model="")
    assert (gemini.chat_model, gemini.embed_model) == ("gemini-3.5-flash-lite", "gemini-embedding-001")
    assert (openai.chat_model, openai.embed_model) == ("gpt-6-luna", "text-embedding-3-small")
    assert openai.api_key_name == "OPENAI_API_KEY"


def test_factory_builds_configured_provider(monkeypatch):
    providers.use_providers(None, None)
    monkeypatch.setattr(providers.settings, "llm_provider", "openai")
    monkeypatch.setattr(providers.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(providers.settings, "chat_model", "gpt-6-luna")
    assert type(providers.get_chat_model()).__name__ == "OpenAIChat"
    providers.use_providers(None, None)
    monkeypatch.setattr(providers.settings, "llm_provider", "gemini")
    assert type(providers.get_chat_model()).__name__ == "GeminiChat"


def test_postgres_url_from_sqlalchemy_is_accepted():
    s = Settings(_env_file=None, database_url="postgresql+psycopg://u:p@h/db", gemini_api_key="k")
    assert s.database_url == "postgresql://u:p@h/db"


def test_tests_cannot_reach_the_internet():
    with pytest.raises(RuntimeError, match="internet"):
        socket.create_connection(("8.8.8.8", 443), timeout=1)


def test_database_errors_are_one_readable_line():
    from app.core.database import explain_db_error

    libpq = (
        'connection failed: connection to server at "127.0.0.1", port 5432 failed: '
        'FATAL:  password authentication failed for user "me"\nMultiple connection attempts failed...'
    )
    assert explain_db_error(Exception(libpq)) == (
        'password authentication failed for user "me". Wrong user or password in DATABASE_URL.'
    )
