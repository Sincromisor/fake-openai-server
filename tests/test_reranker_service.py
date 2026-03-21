"""Unit tests for the reranker service."""

from fake_openai_server.errors import DependencyNotReadyError, InferenceError
from fake_openai_server.schemas.rerank import RerankRequest
from fake_openai_server.services.reranker import RerankerService


class FakeRerankerModel:
    """Simple reranker backend for tests."""

    def __init__(self, scores: list[float]) -> None:
        self._scores = scores

    def predict(self, sentences: list[tuple[str, str]]) -> list[float]:
        """Return fixed scores for query-document pairs."""

        assert len(sentences) == len(self._scores)
        return self._scores


def test_reranker_service_startup_and_rerank() -> None:
    """The service should load the model and return sorted rerank results."""

    captured_loader_calls: list[tuple[str, str]] = []

    service = RerankerService(
        model_name="test-model",
        device="cpu",
        model_loader=lambda model_name, device: _capture_reranker_loader_call(
            captured_loader_calls,
            model_name,
            device,
            FakeRerankerModel([0.2, 0.9, 0.4]),
        ),
    )

    service.startup()
    response = service.rerank(
        RerankRequest(
            model="test-model",
            query="q",
            documents=["a", "b", "c"],
            top_n=2,
        )
    )

    assert service.is_ready() is True
    assert captured_loader_calls == [("test-model", "cpu")]
    assert [result.document.text for result in response.results] == ["b", "c"]
    assert [result.index for result in response.results] == [1, 2]
    assert response.usage.total_tokens == 0


def test_reranker_service_requires_startup_before_inference() -> None:
    """The service should reject inference until the model is loaded."""

    service = RerankerService(
        model_name="test-model",
        device="cpu",
        model_loader=lambda _, __: FakeRerankerModel([0.1]),
    )

    try:
        service.rerank(
            RerankRequest(model="test-model", query="q", documents=["document"])
        )
    except DependencyNotReadyError:
        pass
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("DependencyNotReadyError was not raised")


def test_reranker_service_wraps_model_failures() -> None:
    """The service should hide backend exceptions behind a stable API error."""

    class BrokenRerankerModel:
        def predict(self, sentences: list[tuple[str, str]]) -> list[float]:
            raise RuntimeError("boom")

    service = RerankerService(
        model_name="test-model",
        device="cpu",
        model_loader=lambda _, __: BrokenRerankerModel(),
    )
    service.startup()

    try:
        service.rerank(
            RerankRequest(model="test-model", query="q", documents=["document"])
        )
    except InferenceError:
        pass
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("InferenceError was not raised")


def _capture_reranker_loader_call(
    calls: list[tuple[str, str]],
    model_name: str,
    device: str,
    model: FakeRerankerModel,
) -> FakeRerankerModel:
    """Record loader arguments and return the fake model."""

    calls.append((model_name, device))
    return model
