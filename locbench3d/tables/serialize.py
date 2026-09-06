"""Generic dataclass-to-flat-dict serialization for building table rows.

Nested dataclasses are flattened with an underscore-joined prefix, enums
become their string value, and lists/dicts become a compact ``"a|b"`` /
``"k:v|k2:v2"`` string so every result fits one spreadsheet cell without
losing information. This is the one shared mechanism every table builder
in this package uses, so a result dataclass's fields (and any evidence
attached to it) survive into every exported table the same way.
"""
from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any


def flatten_dataclass(obj: Any, prefix: str = "") -> dict:
    if obj is None:
        return {}
    if not dataclasses.is_dataclass(obj):
        return {prefix.rstrip("_"): obj}

    result: dict = {}
    for f in dataclasses.fields(obj):
        value = getattr(obj, f.name)
        key = f"{prefix}{f.name}"
        if dataclasses.is_dataclass(value):
            result.update(flatten_dataclass(value, prefix=f"{key}_"))
        elif isinstance(value, Enum):
            result[key] = value.value
        elif isinstance(value, (list, tuple)):
            result[key] = "|".join(
                v.value if isinstance(v, Enum) else str(v) for v in value
            )
        elif isinstance(value, dict):
            result[key] = "|".join(f"{k}:{v}" for k, v in value.items())
        else:
            result[key] = value
    return result
