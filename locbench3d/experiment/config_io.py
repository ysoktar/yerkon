"""Load an experiment configuration from YAML.

The YAML schema is documented in docs/FIELD_DEFINITIONS.md and mirrored by
the example files in examples/. Nothing here invents a default numeric
threshold the user did not ask for: ``hard_requirements`` is ``None``
unless the file supplies one, and every requirement field inside it stays
``None`` unless set explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import yaml

from locbench3d.experiment.generator import ExperimentDesign
from locbench3d.experiment.schema import ScenarioTemplate
from locbench3d.feasibility.requirements import HardRequirements

_DEFAULT_N_REPEATS = 20
_DEFAULT_SEED = 0
_DEFAULT_RANGE_BINS = [0, 5, 10, 20, 40, 100]


@dataclass(frozen=True)
class ExperimentConfig:
    design: ExperimentDesign
    n_repeats: int
    seed: int
    range_bin_edges_m: list[float]
    hard_requirements: Optional[HardRequirements]
    gnss_log_path: Optional[str]


def load_experiment_config(path: str) -> ExperimentConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if "template" not in raw or "variables" not in raw:
        raise ValueError("experiment config must have 'template' and 'variables' keys")

    template = ScenarioTemplate(**raw["template"])
    design = ExperimentDesign(template=template, variables=raw["variables"])

    hard_requirements = None
    if raw.get("hard_requirements"):
        hard_requirements = HardRequirements(**raw["hard_requirements"])

    return ExperimentConfig(
        design=design,
        n_repeats=raw.get("n_repeats", _DEFAULT_N_REPEATS),
        seed=raw.get("seed", _DEFAULT_SEED),
        range_bin_edges_m=raw.get("range_bin_edges_m", list(_DEFAULT_RANGE_BINS)),
        hard_requirements=hard_requirements,
        gnss_log_path=raw.get("gnss_log_path"),
    )
