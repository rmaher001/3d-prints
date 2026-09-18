"""Tests for the shared trimesh shape helpers."""
import numpy as np
import pytest

from mesh_shapes import centered_box, rounded_slot


def test_box_is_centered_on_the_origin_by_default():
    b = centered_box(10, 4, 2)
    np.testing.assert_allclose(b.bounds.mean(axis=0), [0, 0, 0], atol=1e-9)
    np.testing.assert_allclose(b.extents, [10, 4, 2])


def test_box_moves_to_its_center():
    b = centered_box(10, 4, 2, (5, -3, 1))
    np.testing.assert_allclose(b.bounds.mean(axis=0), [5, -3, 1], atol=1e-9)


def test_slot_has_rounded_ends_and_the_right_envelope():
    s = rounded_slot(length=9.0, width=3.0, depth=2.0)
    np.testing.assert_allclose(s.extents, [9.0, 3.0, 2.0], atol=0.02)
    # a square slot would contain its corners; a rounded one does not
    corner = np.array([[4.4, 1.4, 0.0]])
    assert not s.contains(corner)[0]
    assert s.contains(np.array([[0.0, 0.0, 0.0]]))[0]


@pytest.mark.parametrize(
    "along,through,expected",
    [
        ("x", "z", [9.0, 3.0, 2.0]),
        ("x", "y", [9.0, 2.0, 3.0]),
        ("z", "x", [2.0, 3.0, 9.0]),
    ],
)
def test_slot_orientation_puts_each_axis_where_asked(along, through, expected):
    """`length` runs along `along`; `depth` runs along `through` and drills it."""
    s = rounded_slot(9.0, 3.0, 2.0, along=along, through=through)
    np.testing.assert_allclose(s.extents, expected, atol=0.02)


def test_slot_is_a_single_watertight_solid():
    s = rounded_slot(9.0, 3.0, 2.0)
    assert s.is_watertight
    assert len(s.split(only_watertight=False)) == 1


def test_slot_sits_at_its_center():
    s = rounded_slot(9.0, 3.0, 2.0, center=(1, 2, 3))
    np.testing.assert_allclose(s.bounds.mean(axis=0), [1, 2, 3], atol=1e-6)
