import unittest

import numpy as np

from core.polyline_complex import (
    build_vr_filtration_from_distances,
    polyline_hausdorff_distance,
    polylines_from_curve,
)


class PolylineComplexTests(unittest.TestCase):
    def test_symmetric_polyline_hausdorff_uses_both_directed_distances(self):
        P = np.array([(0.0, 0.0), (4.0, 0.0)])
        Q = np.array([(-2.0, -3.0), (-2.0, 3.0), (4.0, 1.0)])

        self.assertAlmostEqual(polyline_hausdorff_distance(P, Q), np.sqrt(13.0))

    def test_one_stage_quantisation_preserves_largest_positive_birth(self):
        D = np.array([
            [0.0, 1.0, 5.0],
            [1.0, 0.0, 5.0],
            [5.0, 5.0, 0.0],
        ])

        filtration = build_vr_filtration_from_distances(
            3,
            D,
            max_dimension=1,
            max_stages=1,
        )

        self.assertEqual(filtration[(0, 1)], 5.0)
        self.assertEqual(filtration[(0, 2)], 5.0)
        self.assertEqual(filtration[(1, 2)], 5.0)

    def test_polylines_from_curve_keeps_tail_edges(self):
        curve = np.arange(18, dtype=float).reshape(6, 3)

        polylines = polylines_from_curve(curve, k=2)

        self.assertEqual([len(poly) for poly in polylines], [3, 3, 2])
        np.testing.assert_array_equal(polylines[-1], curve[4:6])


if __name__ == "__main__":
    unittest.main()
