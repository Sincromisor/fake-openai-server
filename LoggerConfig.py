"""Backward-compatible logging config shim."""

from fake_openai_server.logging import build_logging_config


class LoggerConfig:
    """Compat wrapper for older imports."""

    @classmethod
    def generate(cls, log_file: str | None = None, stdout: bool = True) -> dict:
        """Return the shared logging config used by the new package layout."""

        return build_logging_config(level="INFO", json_logs=stdout, log_file=log_file)
