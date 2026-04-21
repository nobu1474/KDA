import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class ExperimentConfig:
    experiment_name: str = "nm_torus_jones"
    shape: str = "nm_torus"

    n_points: int = 500
    random_seed: int = 42

    integration_points: int = 50
    enable_integrated_jones: bool = False

    torus_n: int = 2
    torus_m: int = 3

    run_root: str = "outputs/runs"

    def to_dict(self) -> dict:
        return asdict(self)



def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return ExperimentConfig(**data)
