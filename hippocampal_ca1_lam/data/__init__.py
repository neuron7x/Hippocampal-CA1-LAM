from __future__ import annotations

import importlib
import sys

_PKG = importlib.import_module("data")
sys.modules[__name__] = _PKG
sys.modules[f"{__name__}.biophysical_parameters"] = importlib.import_module(
    "data.biophysical_parameters"
)

__all__ = getattr(_PKG, "__all__", [])
