"""Tests for bbox.print_dimensions dispatch."""
import numpy as np
import pytest
import trimesh

from bbox import print_dimensions, get_extents
from mesh_primitives import make_box as mesh_make_box
from step_primitives import make_box as step_make_box


def test_get_extents_on_stl_mesh():
    m = mesh_make_box(10, 20, 30)
    mins, maxs, dims = get_extents(m)
    np.testing.assert_allclose(dims, [10, 20, 30])


def test_get_extents_on_ocp_shape():
    s = step_make_box(0, 0, 0, 10, 20, 30)
    mins, maxs, dims = get_extents(s)
    np.testing.assert_allclose(dims, [10, 20, 30], atol=1e-4)


def test_get_extents_on_trimesh():
    tm = trimesh.creation.box(extents=[10, 20, 30])
    mins, maxs, dims = get_extents(tm)
    np.testing.assert_allclose(dims, [10, 20, 30])


def test_print_dimensions_prints_something(capsys):
    m = mesh_make_box(1, 2, 3)
    print_dimensions(m)
    out = capsys.readouterr().out
    assert "1" in out and "2" in out and "3" in out


def test_print_dimensions_rejects_unknown_type():
    with pytest.raises(TypeError):
        print_dimensions(object())
