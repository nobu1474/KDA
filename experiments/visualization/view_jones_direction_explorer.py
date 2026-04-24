import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.constants import N_POINTS, RANDOM_SEED
from core.jones import integrated_jones_polynomial
from data.generate_point_cloud import generate_unit_nm_torus_points
from visualization.jones_interactive import launch_interactive_jones_direction_explorer


if __name__ == "__main__":
    nmtorus_points_3d = generate_unit_nm_torus_points(N_POINTS, seed=RANDOM_SEED)
    curves = [nmtorus_points_3d]

    import time
    start_time = time.time()
    poly_map = integrated_jones_polynomial(
        curves,
        Number_of_projections=10000,
        RANDOM_SEED=RANDOM_SEED,
        show_progress=True,
    )
    end_time = time.time()
    print(f"実行時間：{(end_time - start_time)//60} 分 {(end_time - start_time)%60} 秒") #計測結果を表示

    launch_interactive_jones_direction_explorer(
        curves,
        poly_map,
        title="Interactive Jones polynomial explorer",
        host="127.0.0.1",
        port=8050,
        debug=False,
        run_server=True,
    )
