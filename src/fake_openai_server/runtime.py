"""Runtime helpers shared by multiple services."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

_DEVICE_PATTERN = re.compile(r"^(cpu|mps|cuda(?::\d+)?)$")


def validate_accelerator_device(device: str) -> str:
    """Validate a sentence-transformers accelerator device string."""

    normalized_device = device.strip().lower()
    if not normalized_device:
        raise ValueError("accelerator device must not be empty")
    if not _DEVICE_PATTERN.fullmatch(normalized_device):
        raise ValueError(
            "accelerator device must be one of: cpu, mps, cuda, or cuda:<index>"
        )
    return normalized_device


AcceleratorDevice = Annotated[str, AfterValidator(validate_accelerator_device)]
