"""Tests for ASGI factories and runtime commands."""

from fastapi import FastAPI

from fake_openai_server import asgi
from fake_openai_server.config import EmbeddingsSettings, RerankerSettings


def test_create_embeddings_api_builds_fastapi_app(monkeypatch) -> None:
    """The embeddings factory should build the configured FastAPI app."""

    monkeypatch.setattr(
        asgi,
        "get_embeddings_settings",
        lambda: EmbeddingsSettings(model_name="embedding-model"),
    )

    app = asgi.create_embeddings_api()

    assert isinstance(app, FastAPI)
    assert app.title == "Fake OpenAI Embeddings API"


def test_create_reranker_api_builds_fastapi_app(monkeypatch) -> None:
    """The reranker factory should build the configured FastAPI app."""

    monkeypatch.setattr(
        asgi,
        "get_reranker_settings",
        lambda: RerankerSettings(model_name="reranker-model"),
    )

    app = asgi.create_reranker_api()

    assert isinstance(app, FastAPI)
    assert app.title == "Fake OpenAI Rerank API"


def test_run_embeddings_uses_console_entrypoint_settings(monkeypatch) -> None:
    """The embeddings runtime command should launch uvicorn with env-backed settings."""

    calls: list[dict[str, object]] = []
    settings = EmbeddingsSettings(
        model_name="embedding-model",
        host="127.0.0.1",
        port=18081,
    )

    monkeypatch.setattr(asgi, "get_embeddings_settings", lambda: settings)
    monkeypatch.setattr(
        asgi,
        "_create_embeddings_api_from_settings",
        lambda _: object(),
    )
    monkeypatch.setattr(
        asgi.uvicorn,
        "run",
        lambda app, **kwargs: calls.append({"app": app, **kwargs}),
    )

    asgi.run_embeddings()

    assert calls == [
        {
            "app": "fake_openai_server.asgi:create_embeddings_api",
            "factory": True,
            "host": "127.0.0.1",
            "port": 18081,
            "log_config": None,
        }
    ]


def test_run_reranker_uses_console_entrypoint_settings(monkeypatch) -> None:
    """The reranker runtime command should launch uvicorn with env-backed settings."""

    calls: list[dict[str, object]] = []
    settings = RerankerSettings(
        model_name="reranker-model",
        host="127.0.0.1",
        port=18082,
    )

    monkeypatch.setattr(asgi, "get_reranker_settings", lambda: settings)
    monkeypatch.setattr(
        asgi,
        "_create_reranker_api_from_settings",
        lambda _: object(),
    )
    monkeypatch.setattr(
        asgi.uvicorn,
        "run",
        lambda app, **kwargs: calls.append({"app": app, **kwargs}),
    )

    asgi.run_reranker()

    assert calls == [
        {
            "app": "fake_openai_server.asgi:create_reranker_api",
            "factory": True,
            "host": "127.0.0.1",
            "port": 18082,
            "log_config": None,
        }
    ]
