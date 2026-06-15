import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from data.generate_point_cloud import generate_unit_nm_torus_points, generate_spring_points
from config.constants import N_POINTS, nm_torus
from visualization.point_cloud import plot_3d_point_cloud

# 設定
data_file = 'data/protein_data/sample_conformations.npz'
elements_file = 'data/protein_data/elements_array.txt'


if __name__ == "__main__":
	data = np.load(data_file)['arr_0'].astype('float64')
	num = 4
	curve = data[num]
	plot_3d_point_cloud(curve, title=f": Protein Data{num}", equal_aspect=True)
