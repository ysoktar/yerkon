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


def test_the_estimator_cannot_reach_the_ranging_module_either():
    """Observations are the seam. ADR-0003.

    ranging imports the world and the link budget, so an estimator that
    imported ranging would inherit a path to the receiver's true
    position. It may import observation, which imports nothing.
    """
    names = imports_of("estimator")
    assert "yerkon.ranging" not in names
    assert "yerkon.rf" not in names


def test_the_observation_type_is_reachable_from_nothing_else():
    """It is the one type the estimator shares with the simulation.

    If it grew an import of its own, whatever it imported would come
    along with it into the estimator.
    """
    assert not {n for n in imports_of("observation") if n.startswith("yerkon")}


def test_ranging_produces_observations_and_not_verdicts():
    """It measures. It does not decide where anything is."""
    names = imports_of("ranging")
    assert "yerkon.observation" in names
    assert "yerkon.estimator" not in names


#: Modules that must never gain a path to a receiver's true position.
#:
#: Named as a list of what must stay clean rather than a list of what is
#: allowed, so that adding another assembly module does not quietly widen
#: the rule. Everything here is either read by the estimator or feeds it.
MUST_NOT_SEE_TRUTH = (
    "evidence",
    "numbers",
    "hardware",
    "regulatory",
    "rf",
    "observation",
    "ranging",
    "estimator",
    "cost",
    "proposal",
)


def test_nothing_the_estimator_touches_can_reach_the_world():
    """The world holds a receiver's true position. ADR-0003.

    The evaluation reads it because comparing an estimate against truth
    is the whole job, and the modules that assemble scenarios read it
    because that is what they assemble. Everything on the path into the
    estimator stays clear of it.
    """
    for module in MUST_NOT_SEE_TRUTH:
        assert "yerkon.world" not in imports_of(module), module
        assert "yerkon.evaluate" not in imports_of(module), module


def test_the_link_budget_does_not_depend_on_the_world():
    """Physics should not know about the scenario it is used in.

    The world calls the link budget, never the other way round. Keeping
    the arrow pointing one way is what lets the budget be tested on its
    own, which is where the 5 to 15 km claims are checked.
    """
    assert "yerkon.world" not in imports_of("rf")


def test_hardware_is_data_and_depends_on_nothing_but_evidence():
    """And on the file the figures nobody published come from."""
    internal = {name for name in imports_of("hardware") if name.startswith("yerkon")}
    assert internal <= {"yerkon.evidence", "yerkon.settings"}


ALLOWED_TO_ASSUME = {"settings", "evidence"}


def _constructs_an_assumption(tree: ast.AST) -> bool:
    """Whether the module builds a Sourced value marked ASSUMPTION.

    Looks for the construction rather than the word, because comparing
    against ASSUMPTION is exactly what a costing has to do to report how
    much of itself rests on one.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name != "Sourced":
            continue
        for argument in list(node.args) + [kw.value for kw in node.keywords]:
            if (
                isinstance(argument, ast.Attribute)
                and argument.attr == "ASSUMPTION"
            ):
                return True
    return False


def test_no_module_writes_an_assumption_of_its_own():
    """ADR-0016. The settings file is the whole list, or it is no list.

    A placeholder buried in a function is a placeholder nobody will ever
    find, and this project's costings rest almost entirely on
    placeholders. `settings.py` builds them from the file; `evidence.py`
    defines the word. Everywhere else, an assumption written in code
    would be a figure that never appears on the list somebody is working
    through.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.stem in ALLOWED_TO_ASSUME or path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _constructs_an_assumption(tree):
            offenders.append(str(path.relative_to(SRC)))
    assert not offenders, (
        "these construct an assumption instead of reading one from "
        "defaults.toml: {}".format(", ".join(offenders))
    )


def test_every_figure_the_settings_file_holds_says_what_it_affects():
    """A number nobody can act on is a number nobody will replace."""
    from yerkon.settings import DEFAULTS

    for key, entry in DEFAULTS.entries.items():
        assert entry.affects.strip(), key
        assert entry.sourced.note.strip(), key
        assert entry.sourced.unit.strip(), key


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


def test_the_model_does_not_know_about_its_front_ends():
    """design is what the app and the command line both configure.

    If it could import the confirmation panel, the panel's wording would
    start deciding what the model does.
    """
    assert "yerkon.proposal" not in imports_of("design")


def test_the_panel_does_not_do_its_own_physics():
    """ADR-0009. The consequences shown must be the ones the model runs on.

    The panel may ask design.derive what follows from an edit. The moment
    it works a link budget out for itself, the numbers a person confirms
    and the numbers the simulation uses can drift apart, and nothing
    would catch it.
    """
    names = imports_of("proposal")
    assert "yerkon.design" in names
    assert "yerkon.world" not in names

    text = (SRC / "proposal.py").read_text(encoding="utf-8")
    for physics in ("evaluate_link", "usable_range_m(", "two_ray"):
        assert physics not in text, (
            "proposal.py calls {} directly instead of asking design".format(physics)
        )


def test_nothing_that_ships_stands_on_flat_ground():
    """ADR-0021. A plane is a test instrument, not a place.

    Two of the three scenarios stood on one, and it looked like the
    neutral choice. It is the most favourable ground this model can
    draw: every reflection off it arrives at the specular angle the
    two-ray term assumes, and nothing can obstruct anything, so the one
    error the dissection could not measure was the one the terrain made
    impossible. A comment saying "use real ground" would rot; this will
    not.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "world.py":
            continue          # where flat_terrain is defined, and documented
        if "flat_terrain" in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(SRC)))
    assert not offenders, (
        "these build a level surface instead of standing on real or rolling "
        "ground: {}".format(", ".join(offenders))
    )
