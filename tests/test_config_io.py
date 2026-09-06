"""YAML experiment configuration loading."""
import textwrap

from locbench3d.experiment.config_io import load_experiment_config

SAMPLE_YAML = textwrap.dedent(
    """
    template:
      width_m: 10.0
      length_m: 10.0
      height_m: 4.0
      frame_duration_s: 0.001
      guard_duration_s: 0.0002
    variables:
      method: ["UWB_SS_TWR", "UWB_DS_TWR"]
      anchor_count: [4, 5]
    n_repeats: 15
    seed: 3
    range_bin_edges_m: [0, 5, 10, 20]
    hard_requirements:
      max_3d_p95_m: 2.0
      min_availability: 0.8
    """
)


def test_load_experiment_config_parses_template_and_variables(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text(SAMPLE_YAML)
    config = load_experiment_config(str(path))
    assert config.design.template.width_m == 10.0
    assert config.design.variables["method"] == ["UWB_SS_TWR", "UWB_DS_TWR"]
    assert config.n_repeats == 15
    assert config.seed == 3
    assert config.range_bin_edges_m == [0, 5, 10, 20]


def test_load_experiment_config_builds_hard_requirements(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text(SAMPLE_YAML)
    config = load_experiment_config(str(path))
    assert config.hard_requirements.max_3d_p95_m == 2.0
    assert config.hard_requirements.min_availability == 0.8


def test_load_experiment_config_defaults_when_optional_fields_absent(tmp_path):
    minimal = textwrap.dedent(
        """
        template:
          width_m: 5.0
          length_m: 5.0
          height_m: 3.0
          frame_duration_s: 0.001
          guard_duration_s: 0.0
        variables:
          method: ["UWB_SS_TWR"]
        """
    )
    path = tmp_path / "cfg.yaml"
    path.write_text(minimal)
    config = load_experiment_config(str(path))
    assert config.hard_requirements is None
    assert config.n_repeats > 0
