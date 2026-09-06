"""Generic dataclass-to-flat-dict serialization used to build table rows."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from locbench3d.tables.serialize import flatten_dataclass


class Color(str, Enum):
    RED = "RED"


@dataclass(frozen=True)
class Inner:
    value: Optional[float]
    color: Color


@dataclass(frozen=True)
class Outer:
    name: str
    inner: Inner
    tags: list
    lookup: dict


def test_flatten_prefixes_nested_dataclass_fields():
    obj = Outer(name="x", inner=Inner(value=1.5, color=Color.RED), tags=["a", "b"], lookup={"k": 1})
    flat = flatten_dataclass(obj)
    assert flat["name"] == "x"
    assert flat["inner_value"] == 1.5
    assert flat["inner_color"] == "RED"


def test_flatten_joins_lists_and_dicts_to_strings():
    obj = Outer(name="x", inner=Inner(value=None, color=Color.RED), tags=["a", "b"], lookup={"k": 1})
    flat = flatten_dataclass(obj)
    assert flat["tags"] == "a|b"
    assert "k:1" in flat["lookup"]


def test_flatten_none_returns_empty_dict():
    assert flatten_dataclass(None) == {}


def test_flatten_applies_prefix():
    obj = Inner(value=2.0, color=Color.RED)
    flat = flatten_dataclass(obj, prefix="acc_")
    assert flat == {"acc_value": 2.0, "acc_color": "RED"}
