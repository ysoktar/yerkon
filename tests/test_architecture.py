"""Rules about the shape of the code, enforced rather than documented.

ADR-0003 says the estimator may not see truth. The previous codebase
violated that and passed 132 tests, because nothing checked the shape of
the dependency, only the behaviour of the parts. A comment would have
failed the same way. This checks it.
"""

import ast
import pathlib

import pytest

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "yerkon"


def imports_of(module_name: str) -> set[str]:
    path = SRC / "{}.py".format(module_name)
    if not path.exists():
        pytest.skip("{} is not built yet".format(module_name))
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_the_estimator_cannot_reach_the_world():
    """ADR-0003. The single most important line in this repository.

    If the estimator can import the world, it can read the receiver's true
    position, and every accuracy number this project produces becomes a
    statement about nothing. That is exactly what happened before.
    """
    forbidden = {"yerkon.world"}
    assert not (imports_of("estimator") & forbidden)


def test_the_link_budget_does_not_depend_on_the_world():
    """Physics should not know about the scenario it is used in.

    The world calls the link budget, never the other way round. Keeping
    the arrow pointing one way is what lets the budget be tested on its
    own, which is where the 5 to 15 km claims are checked.
    """
    assert "yerkon.world" not in imports_of("rf")


def test_hardware_is_data_and_depends_on_nothing_but_evidence():
    internal = {name for name in imports_of("hardware") if name.startswith("yerkon")}
    assert internal <= {"yerkon.evidence"}


def test_every_module_states_what_it_is_for():
    for path in sorted(SRC.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstring = ast.get_docstring(tree)
        assert docstring, "{} has no module docstring".format(path.name)
        assert len(docstring.split()) >= 12, (
            "{}'s docstring says too little to be worth reading".format(path.name)
        )
