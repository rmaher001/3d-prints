"""Tests for the one-piece standing case: case + 20 mm open-backed foot."""
import os
import sys

import numpy as np
import pytest
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from create_standing_case import (
    BASE_T,
    HEEL_REACH,
    LIFT_MM,
    SCALE_XY,
    SOURCE_STEP,
    build,
    scaled_case,
)
from step_primitives import get_bbox, load_step


@pytest.fixture(scope="module")
def parts():
    case = scaled_case()
    return case, build()


def _section_z_extent(mesh, y):
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    assert sec is not None, f"no material at y={y}"
    pts = np.vstack(sec.discrete)
    return pts[:, 2].min(), pts[:, 2].max()


def test_case_part_is_unchanged(parts):
    """Above the foot, every cross-section still matches the case exactly."""
    case, standing = parts
    y_top = case.bounds[0, 1]
    for offset in (2.0, 12.0, 30.0, 55.0):
        y = y_top + offset
        a = case.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]).to_2D()[0].area
        b = standing.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]).to_2D()[0].area
        assert b == pytest.approx(a, abs=0.05), f"case cross-section changed at y={y:.1f}"
    assert standing.volume > case.volume, "the foot should add material"


def test_part_is_lift_taller_than_the_case(parts):
    case, standing = parts
    assert standing.extents[1] == pytest.approx(case.extents[1] + LIFT_MM, abs=0.01)
    assert standing.bounds[1, 1] == pytest.approx(case.bounds[1, 1], abs=0.01), "grows downward only"


def test_width_is_unchanged(parts):
    case, standing = parts
    assert standing.extents[0] == pytest.approx(case.extents[0], abs=0.01)


def test_foot_reaches_back_for_stability(parts):
    """The base must run well past the case's back, or an 82 mm part topples."""
    case, standing = parts
    case_back = case.bounds[1, 2]
    overhang = standing.bounds[1, 2] - case_back
    assert overhang == pytest.approx(HEEL_REACH, abs=0.01), f"heel reaches {overhang:.1f} mm"
    bottom = standing.bounds[0, 1]
    lo, hi = _section_z_extent(standing, bottom + BASE_T / 2)
    assert hi == pytest.approx(standing.bounds[1, 2], abs=0.01), "the base plate carries the heel"
    assert lo == pytest.approx(0.0, abs=0.01), "and reaches the front face"


def test_skirt_back_is_open(parts):
    case, standing = parts
    mid_skirt = case.bounds[0, 1] - LIFT_MM / 2
    sec = standing.section(plane_origin=[0, mid_skirt, 0], plane_normal=[0, 1, 0])
    pts = np.vstack(sec.discrete)
    back = case.bounds[1, 2]
    assert pts[:, 2].max() <= back + 0.01, "nothing sticks out past the case back up the skirt"
    # no wall across the back: no material in the middle of the opening
    middle = pts[(np.abs(pts[:, 0]) < 15) & (pts[:, 2] > back - 2.0)]
    assert len(middle) == 0, "the back of the skirt must stay open"


def test_foot_is_solid_underneath(parts):
    """Richard asked for a solid bottom: the base plate carries no holes."""
    _, standing = parts
    bottom = standing.bounds[0, 1]
    sec = standing.section(plane_origin=[0, bottom + BASE_T / 2, 0], plane_normal=[0, 1, 0])
    assert len(sec.discrete) == 1, "base plate should be one unbroken outline"


def test_skirt_walls_are_plain(parts):
    """Richard dropped the skirt slots: the walls are solid, the back vents."""
    case, standing = parts
    x_half = case.extents[0] / 2.0
    y_top = case.bounds[0, 1]
    wall_points = np.array([[0.0, y_top - 6.0, 1.0],            # front wall
                            [0.0, y_top - 13.5, 1.0],           # front wall
                            [x_half - 0.9, y_top - 9.5, 8.0],   # right side wall
                            [-(x_half - 0.9), y_top - 9.5, 16.0]])  # left side wall
    inside = standing.contains(wall_points)
    assert inside.all(), f"skirt walls should be unbroken, got {inside}"


def test_prints_as_one_solid(parts):
    _, standing = parts
    assert standing.is_watertight
    assert len(standing.split(only_watertight=False)) == 1


def test_case_is_actually_scaled_to_the_printed_size(parts):
    """The fit-critical scale has to reach the mesh, not just the constant."""
    case, _ = parts
    xmin, ymin, _, xmax, ymax, _ = get_bbox(load_step(SOURCE_STEP))
    assert case.extents[0] == pytest.approx((xmax - xmin) * SCALE_XY, abs=0.02)
    assert case.extents[1] == pytest.approx((ymax - ymin) * SCALE_XY, abs=0.02)
