"""Unit tests for the embeddings service."""

from fake_openai_server.errors import DependencyNotReadyError, InferenceError
from fake_openai_server.schemas.embeddings import EmbeddingRequest
from fake_openai_server.services.embeddings import EmbeddingsService


class FakeEmbeddingArray:
    """Simple numpy-like object for tests."""

    def __init__(self, values: list[list[float]]) -> None:
        self._values = values

    def tolist(self) -> list[list[float]]:
        """Return values as nested lists."""

        return self._values


class FakeEmbeddingsModel:
    """Simple embeddings backend for tests."""

    def __init__(self, values: list[list[float]]) -> None:
        self._values = values

    def encode(
        self,
        sentences: list[str],
        *,
        convert_to_numpy: bool,
    ) -> FakeEmbeddingArray:
        """Return fixed embeddings for the provided texts."""

        assert convert_to_numpy is True
        assert len(sentences) == len(self._values)
        return FakeEmbeddingArray(self._values)


def test_embeddings_service_startup_and_create_embedding() -> None:
    """The service should load the model and return OpenAI-compatible embeddings."""

    service = EmbeddingsService(
        model_name="test-model",
        model_loader=lambda _: FakeEmbeddingsModel([[0.1, 0.2], [0.3, 0.4]]),
    )

    service.startup()
    response = service.create_embedding(
        EmbeddingRequest(model="test-model", input=["hello", "world"])
    )

    assert service.is_ready() is True
    assert response.model == "test-model"
    assert response.data[0].embedding == [0.1, 0.2]
    assert response.data[1].index == 1
    assert response.usage.total_tokens == 0


def test_embeddings_service_requires_startup_before_inference() -> None:
    """The service should reject inference until the model is loaded."""

    service = EmbeddingsService(
        model_name="test-model",
        model_loader=lambda _: FakeEmbeddingsModel([[0.1, 0.2]]),
    )

    try:
        service.create_embedding(EmbeddingRequest(model="test-model", input="hello"))
    except DependencyNotReadyError:
        pass
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("DependencyNotReadyError was not raised")


def test_embeddings_service_wraps_model_failures() -> None:
    """The service should hide backend exceptions behind a stable API error."""

    class BrokenEmbeddingsModel:
        def encode(
            self,
            sentences: list[str],
            *,
            convert_to_numpy: bool,
        ) -> FakeEmbeddingArray:
            raise RuntimeError("boom")

    service = EmbeddingsService(
        model_name="test-model",
        model_loader=lambda _: BrokenEmbeddingsModel(),
    )
    service.startup()

    try:
        service.create_embedding(EmbeddingRequest(model="test-model", input="hello"))
    except InferenceError:
        pass
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("InferenceError was not raised")
