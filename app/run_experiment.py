import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.experiment import load_experiment_config
from core.jones import format_jones_polynomial, integrated_jones_polynomial
from data.generate_point_cloud import (
    generate_unit_nm_torus_points,
    generate_unit_sphere_points,
    make_linked_circles,
)
from model.knot import Knot



def _serialize_polynomial(poly: dict) -> list[dict]:
    terms = []
    for exp, coeff in sorted(poly.items(), key=lambda item: str(item[0])):
        if isinstance(exp, tuple):
            exp_value = list(exp)
        else:
            exp_value = exp
        terms.append({"exp": exp_value, "coeff": float(coeff)})
    return terms



def _run_id(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:8]
    return f"{ts}_{prefix}_{suffix}"



def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")



def _append_jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")



def main() -> None:
    parser = argparse.ArgumentParser(description="Run Jones polynomial experiment")
    parser.add_argument(
        "--config",
        default="config/experiment_default.json",
        help="Path to config JSON",
    )
    args = parser.parse_args()

    config = load_experiment_config(args.config)

    run_id = _run_id(config.experiment_name)
    run_dir = Path(config.run_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = run_dir / "metrics.jsonl"

    t0 = time.perf_counter()
    if config.shape == "linked_circles":
        curves = make_linked_circles(config.n_points)
    elif config.shape == "nm_torus":
        curve = generate_unit_nm_torus_points(
            n_points=config.n_points,
            n=config.torus_n,
            m=config.torus_m,
            seed=config.random_seed,
        )
        curves = [curve]
    else:
        raise ValueError(f"Unsupported shape: {config.shape}")
    t1 = time.perf_counter()

    _append_jsonl(
        metrics_path,
        {
            "event": "generate_curves",
            "elapsed_s": t1 - t0,
            "n_curves": len(curves),
            "n_points_first_curve": int(curves[0].shape[0]),
        },
    )

    t2_start = time.perf_counter()
    knot = Knot(curves)
    jones_poly = knot.jones_polynomial
    t2_end = time.perf_counter()

    _append_jsonl(
        metrics_path,
        {
            "event": "compute_jones",
            "elapsed_s": t2_end - t2_start,
            "n_crossings": len(knot.crossings),
            "writhe": knot.writhe,
        },
    )

    integrated_summary = None
    if config.enable_integrated_jones:
        t3_start = time.perf_counter()
        sphere_points = generate_unit_sphere_points(
            n_points=config.integration_points,
            seed=config.random_seed,
        )
        poly_map = integrated_jones_polynomial(curves, sphere_points=sphere_points)
        t3_end = time.perf_counter()

        distinct = len({tuple(sorted(v.items(), key=lambda x: str(x[0]))) for v in poly_map.values()})

        _append_jsonl(
            metrics_path,
            {
                "event": "integrated_jones",
                "elapsed_s": t3_end - t3_start,
                "integration_points": int(config.integration_points),
                "n_projection_directions": len(poly_map),
                "n_distinct_polynomials": distinct,
            },
        )

        integrated_summary = {
            "integration_points": int(config.integration_points),
            "n_projection_directions": len(poly_map),
            "n_distinct_polynomials": distinct,
        }

    total_elapsed = time.perf_counter() - t0
    _append_jsonl(metrics_path, {"event": "total", "elapsed_s": total_elapsed})

    result_payload = {
        "run_id": run_id,
        "jones_polynomial": {
            "terms": _serialize_polynomial(jones_poly),
            "formatted": format_jones_polynomial(jones_poly),
            "n_terms": len(jones_poly),
        },
        "knot_summary": {
            "n_crossings": len(knot.crossings),
            "writhe": knot.writhe,
        },
    }
    if integrated_summary is not None:
        result_payload["integrated_summary"] = integrated_summary

    manifest = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "entrypoint": "app/run_experiment.py",
        "config_path": str(args.config),
        "config": config.to_dict(),
        "artifacts": {
            "result": "result.json",
            "metrics": "metrics.jsonl",
        },
    }

    _write_json(run_dir / "manifest.json", manifest)
    _write_json(run_dir / "result.json", result_payload)

    print(f"run_id: {run_id}")
    print(f"result: {run_dir / 'result.json'}")
    print(f"metrics: {run_dir / 'metrics.jsonl'}")


if __name__ == "__main__":
    main()
