"""API tests for the FastAPI applications."""

from fastapi.testclient import TestClient

from fake_openai_server.app import create_embeddings_app, create_reranker_app
from fake_openai_server.config import EmbeddingsSettings, RerankerSettings
from fake_openai_server.services.embeddings import EmbeddingsService
from fake_openai_server.services.reranker import RerankerService


class FakeEmbeddingArray:
    """Simple numpy-like object for API tests."""

    def __init__(self, values: list[list[float]]) -> None:
        self._values = values

    def tolist(self) -> list[list[float]]:
        """Return values as nested lists."""

        return self._values


class FakeEmbeddingsModel:
    """Simple embeddings backend for API tests."""

    def encode(
        self,
        sentences: list[str],
        *,
        convert_to_numpy: bool,
    ) -> FakeEmbeddingArray:
        """Return predictable embeddings for the provided texts."""

        assert convert_to_numpy is True
        return FakeEmbeddingArray(
            [[float(index), float(index + 1)] for index, _ in enumerate(sentences)]
        )


class FakeRerankerModel:
    """Simple reranker backend for API tests."""

    def predict(self, sentences: list[tuple[str, str]]) -> list[float]:
        """Return descending scores based on the document position."""

        return [float(index) for index in range(len(sentences))]


def test_embeddings_api_exposes_openapi_health_and_inference() -> None:
    """The embeddings app should expose the contract, health probes, and endpoint."""

    app = create_embeddings_app(
        EmbeddingsSettings(model_name="test-embedding-model"),
        service=EmbeddingsService(
            model_name="test-embedding-model",
            model_loader=lambda _: FakeEmbeddingsModel(),
        ),
    )

    with TestClient(app) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")
        response = client.post(
            "/v1/embeddings",
            json={"model": "test-embedding-model", "input": ["a", "b"]},
        )
        openapi = client.get("/openapi.json")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert response.status_code == 200
    assert response.json()["data"][1]["embedding"] == [1.0, 2.0]
    assert openapi.status_code == 200
    assert "/v1/embeddings" in openapi.json()["paths"]
    assert "/health/ready" in openapi.json()["paths"]


def test_embeddings_api_returns_openai_style_validation_error() -> None:
    """Invalid embeddings input should return the shared error shape."""

    app = create_embeddings_app(
        EmbeddingsSettings(model_name="test-embedding-model"),
        service=EmbeddingsService(
            model_name="test-embedding-model",
            model_loader=lambda _: FakeEmbeddingsModel(),
        ),
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/embeddings",
            json={"model": "test-embedding-model", "input": []},
        )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "invalid_request_error"
    assert response.json()["error"]["code"] == "validation_error"


def test_rerank_api_returns_ranked_results() -> None:
    """The rerank app should expose readiness and sorted ranking results."""

    app = create_reranker_app(
        RerankerSettings(model_name="test-reranker-model"),
        service=RerankerService(
            model_name="test-reranker-model",
            model_loader=lambda _: FakeRerankerModel(),
        ),
    )

    with TestClient(app) as client:
        ready = client.get("/health/ready")
        response = client.post(
            "/v1/rerank",
            json={
                "model": "test-reranker-model",
                "query": "what",
                "documents": ["a", "b", "c"],
            },
        )

    assert ready.status_code == 200
    assert response.status_code == 200
    assert [item["document"]["text"] for item in response.json()["results"]] == [
        "c",
        "b",
        "a",
    ]


def test_rerank_api_returns_openai_style_internal_error() -> None:
    """Unexpected reranker failures should return the shared internal error shape."""

    class BrokenRerankerModel:
        def predict(self, sentences: list[tuple[str, str]]) -> list[float]:
            raise RuntimeError("boom")

    app = create_reranker_app(
        RerankerSettings(model_name="test-reranker-model"),
        service=RerankerService(
            model_name="test-reranker-model",
            model_loader=lambda _: BrokenRerankerModel(),
        ),
    )

    with TestClient(app) as client:
        response = client.post(
            "/v1/rerank",
            json={
                "model": "test-reranker-model",
                "query": "what",
                "documents": ["a", "b"],
            },
        )

    assert response.status_code == 500
    assert response.json()["error"]["type"] == "server_error"
    assert response.json()["error"]["code"] == "inference_failed"
