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


# --- drop_slivers -------------------------------------------------------------
# A boolean where a curve meets a flat face tangentially can leave a flat sheet of
# triangles behind: no volume, nothing to print, but a second "body".

from trimesh_helpers import drop_slivers  # noqa: E402


def _sheet():
    return trimesh.Trimesh(vertices=[[500, 0, 0], [501, 0, 0], [500, 1, 0]],
                           faces=[[0, 1, 2], [0, 2, 1]], process=False)


def test_a_zero_volume_sliver_is_dropped():
    body = trimesh.creation.box(extents=(10, 10, 10))
    cleaned = drop_slivers(trimesh.util.concatenate([body, _sheet()]))
    assert cleaned.body_count == 1
    assert np.isclose(cleaned.volume, 1000.0)


def test_a_single_body_comes_back_unchanged():
    body = trimesh.creation.box(extents=(10, 10, 10))
    assert np.isclose(drop_slivers(body).volume, 1000.0)


def test_two_real_bodies_are_refused_not_merged_away():
    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(10, 10, 10)).apply_translation([50, 0, 0])
    with pytest.raises(ValueError):
        drop_slivers(trimesh.util.concatenate([a, b]))
