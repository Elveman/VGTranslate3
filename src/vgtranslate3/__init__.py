"""
vgtranslate3 – OCR game translator.

Example:
    >>> from vgtranslate3 import translate_image
    >>> with open("screen.png", "rb") as f:
    ...     result = translate_image(f.read(), target_lang="en")
"""

from __future__ import annotations

import json
import os
from importlib.metadata import version as _pkg_version 
from pathlib import Path
from typing import Any, Dict

# ------------------------------------------------------------------------
# Version
# ------------------------------------------------------------------------
try:
    __version__: str = _pkg_version(__name__)
except Exception:
    __version__ = "0.1a1"

# ------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------
_CFG_PATH = Path(
    os.getenv(
        "VGTRANSLATE3_CONFIG",
        Path(__file__).with_name("config.json"),
    )
)


def load_default_config() -> Dict[str, Any]:
    """Вернуть словарь с настройками из файла конфигурации."""
    return json.loads(_CFG_PATH.read_text(encoding="utf-8"))


__all__ = [
    "__version__",
    "load_default_config",
]
