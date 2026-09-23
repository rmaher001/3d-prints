"""Dimensional invariants for the ZTH05 hygrometer-pocket fit gauge.

The gauge exists to answer one question: which square opening actually seats a
Tuya ZTH05 on Richard's P2S. The invariants below guard that the gauge is a
faithful, printable stand-in for the SPILLPROOF2 box's hygrometer window:
the smallest window must equal the pocket measured out of the donor 3mf, the
windows must step by a known increment, and the retaining lip must actually
narrow the opening (else the sensor falls through and the test proves nothing).

    ../tools/venv/bin/python -m pytest test_create_gauge.py -q
"""
import math
import os
import sys

import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import create_gauge as cg

GAUGE = cg.build_gauge()


def _mesh(shape, name):
    path = os.path.join("/tmp", f"_test_{name}.stl")
    cg.save_stl(shape, path)
    return trimesh.load(path)


MESH = _mesh(GAUGE, "zth05_gauge")


def test_dot_count_means_the_same_size_it_did_on_the_first_gauge():
    """Rev 1 printed 1-4 dots as donor+0.00..+0.60. Rev 2 reprints a subset, so a
    dot count must still decode to the same opening or the two prints can't be
    compared side by side."""
    for n, size in zip(cg.DOT_COUNTS, cg.WINDOW_SIZES):
        assert math.isclose(size, cg.SOURCE_POCKET + (n - 1) * cg.STEP, abs_tol=1e-9)


def test_gauge_drops_the_size_the_first_print_disproved():
    """1 dot = the unmodified donor window. The printed gauge would not admit the
    ZTH05 at that size, so reprinting it burns ASA to re-learn a known answer."""
    assert 1 not in cg.DOT_COUNTS
    assert min(cg.WINDOW_SIZES) > cg.SOURCE_POCKET


def test_windows_step_by_known_increment():
    steps = [b - a for a, b in zip(cg.WINDOW_SIZES, cg.WINDOW_SIZES[1:])]
    assert all(math.isclose(s, cg.STEP, abs_tol=1e-9) for s in steps)
    assert cg.STEP > 0


def test_pocket_depth_matches_the_donor_window():
    """Measured off object_321.model: the window holds 43.16 mm square for 12.75 mm
    in from the outer face before the shoulder narrows it. Rev 1 modelled that run
    as 3.69 mm, so it could only test width -- never whether the sensor seats."""
    assert math.isclose(cg.SOURCE_POCKET_DEPTH, 12.75, abs_tol=0.05)
    assert math.isclose(cg.PLATE_T - cg.LIP_T, cg.SOURCE_POCKET_DEPTH, abs_tol=1e-9)


def test_window_stays_full_size_for_the_whole_pocket_depth():
    """If the opening necks anywhere in the 12.75 mm run, the sensor jams part way
    in and the gauge reports a false negative."""
    for (cx, cy), size in zip(cg.window_centers(), cg.WINDOW_SIZES):
        for frac in (0.02, 0.25, 0.5, 0.75, 0.98):
            z = cg.LIP_T + frac * cg.SOURCE_POCKET_DEPTH
            assert not MESH.contains([[cx + size / 2 - 0.3, cy, z]])[0], \
                f"window {size} necks at z={z:.2f}"


def test_every_window_is_open_through_the_plate():
    """A point on each window axis must be air, at mid-plate and above the lip."""
    pts = [[cx, cy, cg.PLATE_T - 0.5] for cx, cy in cg.window_centers()]
    assert not any(MESH.contains(pts)), "windows must be open through the plate"


def test_window_edges_land_where_specified():
    """Just inside each opening is air; just outside is plate material."""
    for (cx, cy), size in zip(cg.window_centers(), cg.WINDOW_SIZES):
        z = cg.PLATE_T - 0.5  # above the lip, where the opening is full size
        inside = MESH.contains([[cx + size / 2 - 0.4, cy, z]])[0]
        outside = MESH.contains([[cx + size / 2 + 0.4, cy, z]])[0]
        assert not inside, f"window {size} should still be open 0.4mm inside its edge"
        assert outside, f"window {size} should be solid plate 0.4mm outside its edge"


def test_lip_narrows_the_opening_so_the_sensor_seats():
    """Without the lip the sensor drops straight through and the fit test is useless."""
    for (cx, cy), size in zip(cg.window_centers(), cg.WINDOW_SIZES):
        z = cg.LIP_T / 2
        on_lip = MESH.contains([[cx + size / 2 - cg.LIP_INSET / 2, cy, z]])[0]
        assert on_lip, f"window {size} must have a retaining lip at the back face"


def test_lip_matches_the_donor_shoulder():
    """The donor box narrows 43.16 -> 41.80 across X; keep the same shoulder."""
    assert math.isclose(cg.SOURCE_POCKET - 2 * cg.LIP_INSET, cg.SOURCE_SHOULDER, abs_tol=1e-9)


def test_gauge_is_one_separate_tile_per_window():
    """Separate coupons, not one plate: a big thin ASA plate warps, and a warped
    plate distorts the openings the gauge exists to measure."""
    assert MESH.is_watertight, "gauge must be watertight to slice"
    assert MESH.body_count == len(cg.WINDOW_SIZES), "each window must be its own tile"


def test_tiles_do_not_touch():
    """Tiles must be genuinely separate, or they warp as one plate again."""
    centers = cg.window_centers()
    for (ax, ay), (bx, by) in zip(centers, centers[1:]):
        if abs(ax - bx) > 1e-9 or abs(ay - by) > 1e-9:
            clear = max(abs(ax - bx), abs(ay - by)) - cg.TILE
            assert clear > 0, "adjacent tiles overlap"


def test_each_tile_is_small_enough_to_stay_flat_in_asa():
    """The whole point of splitting the plate. 60mm is a conservative ceiling for
    an unheated-chamber-free ASA coupon."""
    assert cg.TILE <= 60.0


def test_gauge_fits_the_p2s_bed():
    w, d, h = MESH.bounds[1] - MESH.bounds[0]
    assert max(w, d) < cg.BED, "all four tiles must fit the P2S build plate at once"
    assert math.isclose(h, cg.PLATE_T, abs_tol=0.05)


def test_each_window_is_labelled_by_dot_count():
    """Dots are how you tell the variants apart after printing; one per index+1."""
    for idx, (cx, cy) in enumerate(cg.window_centers()):
        for dot in cg.dot_centers(idx, cx, cy):
            in_dot = MESH.contains([[dot[0], dot[1], cg.PLATE_T - cg.DOT_DEPTH / 2]])[0]
            assert not in_dot, f"variant {idx} dot at {dot} should be a recess"
