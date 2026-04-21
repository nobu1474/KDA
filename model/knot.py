from typing import Dict, List, Optional, Union

import numpy as np

from core.crossings import find_crossings
from core.jones import (
    _convert_A_poly_to_t_poly,
    _normalize_bracket_to_jones_in_A,
    format_jones_polynomial,
    kauffman_bracket,
)

Exponent = Union[int, tuple]
Polynomial = Dict[Exponent, float]


class Knot:
    """Container for curves and lazy Jones polynomial computation."""

    def __init__(self, curves: List[np.ndarray], projection_vector: Optional[np.ndarray] = None):
        self.curves = curves
        self.projection_vector = (
            np.array([0.0, 0.0, 1.0])
            if projection_vector is None
            else np.asarray(projection_vector, dtype=float)
        )

        self._crossings: Optional[List[dict]] = None
        self._writhe: Optional[int] = None
        self._bracket_A: Optional[Polynomial] = None
        self._normalized_A: Optional[Polynomial] = None
        self._jones_t: Optional[Polynomial] = None

    def _ensure_crossings(self) -> None:
        if self._crossings is None:
            self._crossings = find_crossings(
                self.curves,
                projection_vector=self.projection_vector,
            )

    def _ensure_writhe(self) -> None:
        if self._writhe is None:
            self._ensure_crossings()
            self._writhe = int(sum(int(crossing["sign"]) for crossing in self._crossings))

    def _ensure_bracket(self) -> None:
        if self._bracket_A is None:
            self._ensure_crossings()
            self._bracket_A = kauffman_bracket(self._crossings)

    def _ensure_normalized_A(self) -> None:
        if self._normalized_A is None:
            self._ensure_bracket()
            self._normalized_A = _normalize_bracket_to_jones_in_A(
                self._bracket_A,
                self._crossings,
            )

    def _ensure_jones_t(self) -> None:
        if self._jones_t is None:
            self._ensure_normalized_A()
            self._jones_t = _convert_A_poly_to_t_poly(self._normalized_A)

    @property
    def crossings(self) -> List[dict]:
        self._ensure_crossings()
        return self._crossings

    @property
    def writhe(self) -> int:
        self._ensure_writhe()
        return self._writhe

    @property
    def jones_polynomial(self) -> Polynomial:
        self._ensure_jones_t()
        return self._jones_t

    @property
    def jones_polynomial_str(self) -> str:
        return format_jones_polynomial(self.jones_polynomial)

    @property
    def jones_polynomial_latex(self) -> str:
        return format_jones_polynomial(self.jones_polynomial, use_latex=True)

    def refresh(self) -> None:
        """Clear cached values to force recomputation."""
        self._crossings = None
        self._writhe = None
        self._bracket_A = None
        self._normalized_A = None
        self._jones_t = None
