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


# --- scooped_pocket ---------------------------------------------------------
# A pocket cutter whose two bottom edges along X are rounded, so coins slide up
# and out instead of wedging in a square corner.

from mesh_shapes import scooped_pocket  # noqa: E402


def test_scooped_pocket_has_the_requested_envelope_sitting_on_its_floor():
    p = scooped_pocket(40.0, 30.0, 20.0, radius=8.0, floor_center=(5.0, -2.0, 1.0))
    np.testing.assert_allclose(p.bounds[0], [5 - 20, -2 - 15, 1.0], atol=0.02)
    np.testing.assert_allclose(p.bounds[1], [5 + 20, -2 + 15, 21.0], atol=0.02)


def test_scooped_pocket_rounds_the_bottom_edges_but_keeps_the_floor():
    p = scooped_pocket(40.0, 30.0, 20.0, radius=8.0)
    in_the_corner = [[0.0, -15 + 0.5, 0.5]]      # inside the radius: must be left solid
    floor_middle = [[0.0, 0.0, 0.5]]
    up_the_wall = [[0.0, -15 + 0.5, 12.0]]       # above the radius: square wall again
    on_the_curve = [[0.0, -12.0, 5.0]]           # inside the arc, outside both boxes
    assert not p.contains(in_the_corner)[0]
    assert p.contains(floor_middle)[0]
    assert p.contains(up_the_wall)[0]
    assert p.contains(on_the_curve)[0]


def test_scooped_pocket_leaves_the_ends_square():
    """Only the edges along X are scooped; the X ends stay vertical walls."""
    p = scooped_pocket(40.0, 30.0, 20.0, radius=8.0)
    assert p.contains([[20 - 0.5, 0.0, 0.5]])[0]


@pytest.mark.parametrize("depth, radius", [
    (30.0, 15.5),    # wider than half the depth
    (50.0, 20.0),    # as tall as the pocket: no wall left above the curve
    (50.0, 20.5),    # taller than the pocket
    (30.0, 0.0),
])
def test_scooped_pocket_refuses_a_radius_that_does_not_fit(depth, radius):
    with pytest.raises(ValueError):
        scooped_pocket(40.0, depth, 20.0, radius=radius)


@pytest.mark.parametrize("radius", [12.0, 15.0])
def test_scooped_pocket_stays_inside_its_height_with_a_big_radius(radius):
    """The edge cylinders are 2r tall; past half the height they must not poke out the top."""
    p = scooped_pocket(40.0, 30.0, 20.0, radius=radius)
    np.testing.assert_allclose(p.extents, [40.0, 30.0, 20.0], atol=0.02)


def test_scooped_pocket_with_radius_half_the_depth_is_a_half_pipe():
    """No flat strip left: the two curves meet in the middle of the floor."""
    p = scooped_pocket(40.0, 30.0, 20.0, radius=15.0)
    assert p.is_watertight
    assert p.contains([[0.0, 0.0, 0.5]])[0]
    assert not p.contains([[0.0, 15 - 0.5, 0.5]])[0]
