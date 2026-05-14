"""Unit tests for modify_case helpers."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modify_case import expand_vertices_radial, group_vertices_by_quadrant


def test_radial_push_moves_vertex_outward():
    # Two vertices on the +X axis from origin. Centroid is at (1, 0).
    # Push 0.5mm radially outward from centroid.
    v = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]], dtype=float)
    expand_vertices_radial(v, [0, 1], 0.5)
    # Vertex 0 was at distance 1 from centroid (1,0), in -X direction → moves to -0.5
    # Vertex 1 was at distance 1 from centroid (1,0), in +X direction → moves to 2.5
    np.testing.assert_allclose(v[0, 0], -0.5)
    np.testing.assert_allclose(v[1, 0], 2.5)
    np.testing.assert_allclose(v[:, 1:], 0)  # Y, Z unchanged


def test_radial_push_zero_at_centroid():
    # 3 vertices forming an equilateral-ish triangle plus one at the centroid.
    v = np.array([
        [1.0, 0.0, 0.0],
        [-0.5, 0.866, 0.0],
        [-0.5, -0.866, 0.0],
        [0.0, 0.0, 0.0],  # exactly at centroid
    ], dtype=float)
    original_centroid_vert = v[3].copy()
    expand_vertices_radial(v, [0, 1, 2, 3], 0.3)
    # Centroid vertex should be unchanged (dist == 0 guard).
    np.testing.assert_allclose(v[3], original_centroid_vert)


def test_radial_push_only_affects_xy():
    v = np.array([[2.0, 0.0, 5.0], [-2.0, 0.0, 5.0]], dtype=float)
    expand_vertices_radial(v, [0, 1], 0.1)
    # Z column must be unchanged.
    np.testing.assert_allclose(v[:, 2], 5.0)


def test_quadrant_grouping_partitions_into_4():
    # 8 vertices, 2 per quadrant.
    v = np.array([
        [1.0, 1.0, 0.0],   # RU
        [2.0, 2.0, 0.0],   # RU
        [1.0, -1.0, 0.0],  # RL
        [3.0, -2.0, 0.0],  # RL
        [-1.0, 1.0, 0.0],  # LU
        [-2.0, 3.0, 0.0],  # LU
        [-1.0, -1.0, 0.0], # LL
        [-2.0, -2.0, 0.0], # LL
    ], dtype=float)
    groups = group_vertices_by_quadrant(v, list(range(8)), 0.0, 0.0)
    assert sorted(groups[("R", "U")]) == [0, 1]
    assert sorted(groups[("R", "L")]) == [2, 3]
    assert sorted(groups[("L", "U")]) == [4, 5]
    assert sorted(groups[("L", "L")]) == [6, 7]


def test_quadrant_grouping_uses_strict_inequality():
    # A vertex exactly on the X=cx axis goes to L (not R) per `>` semantics.
    v = np.array([[0.0, 1.0, 0.0]], dtype=float)
    groups = group_vertices_by_quadrant(v, [0], 0.0, 0.0)
    assert groups[("L", "U")] == [0]
    assert groups[("R", "U")] == []
