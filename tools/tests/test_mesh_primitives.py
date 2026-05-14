"""Tests for numpy-stl primitives."""
import numpy as np
import pytest
from stl import mesh

from mesh_primitives import make_box, make_cylinder, make_ring, combine, flip_z


def _extents(m: mesh.Mesh) -> tuple[np.ndarray, np.ndarray]:
    v = m.vectors.reshape(-1, 3)
    return v.min(axis=0), v.max(axis=0)


def test_make_box_default_centered_xy_bottom_at_z0():
    m = make_box(10, 20, 30)
    mins, maxs = _extents(m)
    np.testing.assert_allclose(mins, [-5, -10, 0])
    np.testing.assert_allclose(maxs, [5, 10, 30])
    assert len(m.vectors) == 12  # 12 triangles, 6 faces


def test_make_box_offset_center():
    m = make_box(10, 20, 30, cx=100, cy=200, cz=50)
    mins, maxs = _extents(m)
    np.testing.assert_allclose(mins, [95, 190, 50])
    np.testing.assert_allclose(maxs, [105, 210, 80])


def test_make_cylinder_bbox_radius():
    m = make_cylinder(r=5, h=10, n=64)
    mins, maxs = _extents(m)
    # n=64 segments → outer radius slightly less than r in some dirs; allow 1% tol
    np.testing.assert_allclose(mins[:2], [-5, -5], atol=0.05)
    np.testing.assert_allclose(maxs[:2], [5, 5], atol=0.05)
    np.testing.assert_allclose(mins[2], 0)
    np.testing.assert_allclose(maxs[2], 10)


def test_make_ring_has_inner_hole():
    # Ring with outer 10, inner 5: no vertex should be closer than ~5 from center in xy
    m = make_ring(r_outer=10, r_inner=5, h=2, n=64)
    v = m.vectors.reshape(-1, 3)
    xy_radii = np.sqrt(v[:, 0] ** 2 + v[:, 1] ** 2)
    # All vertices on outer or inner rim; tolerate the n=64 chord error
    assert xy_radii.min() >= 5 - 0.05
    assert xy_radii.max() <= 10 + 0.05


def test_combine_preserves_triangle_count():
    a = make_box(1, 1, 1)
    b = make_box(1, 1, 1, cx=10)
    c = combine([a, b])
    assert len(c.vectors) == len(a.vectors) + len(b.vectors)


def test_flip_z_mirrors_around_max_z_over_2():
    m = make_box(10, 10, 20)  # spans z=[0,20]
    flipped = flip_z(m, max_z=20)
    mins, maxs = _extents(flipped)
    np.testing.assert_allclose(mins[2], 0)
    np.testing.assert_allclose(maxs[2], 20)
    # A vertex originally at z=0 should now be at z=20 and vice versa
    orig_v = m.vectors.reshape(-1, 3)
    flip_v = flipped.vectors.reshape(-1, 3)
    # vertex order is reversed per triangle; just check z-coords are mirrored
    assert sorted((20 - orig_v[:, 2]).tolist()) == sorted(flip_v[:, 2].tolist())
