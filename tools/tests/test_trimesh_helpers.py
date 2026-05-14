"""Tests for trimesh ↔ manifold3d round-trip."""
import numpy as np
import pytest
import trimesh

from trimesh_helpers import to_manifold, from_manifold


def test_round_trip_preserves_bbox():
    box = trimesh.creation.box(extents=[10, 20, 30])
    mani = to_manifold(box)
    back = from_manifold(mani)
    np.testing.assert_allclose(back.bounds[0], box.bounds[0], atol=1e-3)
    np.testing.assert_allclose(back.bounds[1], box.bounds[1], atol=1e-3)


def test_manifold_supports_boolean():
    a = to_manifold(trimesh.creation.box(extents=[10, 10, 10]))
    b = to_manifold(trimesh.creation.box(extents=[10, 10, 10]).apply_translation([5, 0, 0]))
    union = a + b
    back = from_manifold(union)
    # Union along x: total extent should be 15 (10 + 5 overlap shift)
    assert round(back.bounds[1][0] - back.bounds[0][0], 2) == 15.0
