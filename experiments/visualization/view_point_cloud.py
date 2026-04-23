import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_unit_nm_torus_points
from config.constants import N_POINTS, nm_torus
from visualization.point_cloud import plot_3d_point_cloud


if __name__ == "__main__":
	nmtorus_points_3d = generate_unit_nm_torus_points(N_POINTS)
	plot_3d_point_cloud(nmtorus_points_3d, title=nm_torus)
	