import socket
from types import SimpleNamespace

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


class FakeGeminiFiles:
    """Stands in for client.files: the video is 'processing' once, then ready."""

    def __init__(self, final_state):
        from google.genai import types
        self.types, self.final_state, self.log = types, final_state, []

    def _file(self, state):
        return self.types.File(name="files/abc", state=state)

    def upload(self, file, config):
        self.log.append(("upload", config.mime_type))
        return self._file(self.types.FileState.PROCESSING)

    def get(self, name):
        self.log.append(("get", name))
        return self._file(self.final_state)

    def delete(self, name):
        self.log.append(("delete", name))


def gemini_with_files(monkeypatch, files):
    from app.providers.gemini import GeminiChat
    monkeypatch.setattr("app.providers.gemini.time.sleep", lambda s: None)
    chat = GeminiChat(api_key="test", model="gemini-test")
    answer = SimpleNamespace(text=" [00:01] Hello. ")
    chat._client = SimpleNamespace(files=files, models=SimpleNamespace(generate_content=lambda **kw: answer))
    return chat


def test_gemini_video_uploads_waits_answers_and_cleans_up(monkeypatch):
    from google.genai import types
    files = FakeGeminiFiles(types.FileState.ACTIVE)
    chat = gemini_with_files(monkeypatch, files)
    assert chat.describe_video(b"video", "video/mp4", "transcribe") == "[00:01] Hello."
    assert files.log == [("upload", "video/mp4"), ("get", "files/abc"), ("delete", "files/abc")]


def test_gemini_video_that_fails_processing_is_reported_and_deleted(monkeypatch):
    from google.genai import types
    files = FakeGeminiFiles(types.FileState.FAILED)
    chat = gemini_with_files(monkeypatch, files)
    with pytest.raises(ProviderError, match="couldn't process the video"):
        chat.describe_video(b"video", "video/mp4", "transcribe")
    assert files.log[-1] == ("delete", "files/abc")


def test_openai_explains_it_cannot_read_video():
    from app.providers.openai import OpenAIChat
    with pytest.raises(ProviderError, match="LLM_PROVIDER=gemini"):
        OpenAIChat(api_key="test", model="gpt-test").describe_video(b"video", "video/mp4", "transcribe")
