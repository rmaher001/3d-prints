"""Invariants for the desk drawer tray insert.

Three things have to hold. The halves must drop into the wooden tray (365.5 x
179.5 x 30 inside) and each fit the P2S bed. Every bay must be a real opening
with a floor under it and walls between it and its neighbours. And the things
Richard measured must actually fit the bays meant for them, with the finger
room he asked for.

    ../tools/venv/bin/python -m pytest test_create_insert.py -q
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import create_insert as ci

SIDES = ("left", "right")
HALVES = {side: ci.build_half(side) for side in SIDES}
FIT_TESTS = {side: ci.build_half(side, fit_test=True) for side in SIDES}


def _solid(mesh, x, y, z):
    return bool(mesh.contains([[x, y, z]])[0])


# --- it fits the tray and the printer --------------------------------------

@pytest.mark.parametrize("side", SIDES)
def test_each_half_has_the_planned_envelope(side):
    w, d, h = HALVES[side].extents
    assert math.isclose(w, ci.HALF_W, abs_tol=0.02)
    assert math.isclose(d, ci.INSERT_D, abs_tol=0.02)
    assert math.isclose(h, ci.HEIGHT, abs_tol=0.02)


FIT_TESTED = (364.5, 178.5)     # printed 2026-09-23: fit, but ~1 mm loose all around


def test_the_halves_take_up_the_looseness_the_fit_test_showed():
    """The measured tray (365.5 x 179.5) is evidently a little bigger than measured:
    outlines built 1 mm under it dropped in with ~1 mm to spare on every side.
    Richard: "1mm ... on all sides" -- so the pair grows 1 mm per side (2 mm each
    way) over what was fit-tested."""
    across = HALVES["left"].extents[0] + HALVES["right"].extents[0]
    front_to_back = max(m.extents[1] for m in HALVES.values())
    assert math.isclose(across, FIT_TESTED[0] + 2.0, abs_tol=0.02), f"{across:.2f} mm across"
    assert math.isclose(front_to_back, FIT_TESTED[1] + 2.0, abs_tol=0.02), f"{front_to_back:.2f} mm deep"


def test_walls_stay_below_the_rim():
    assert max(m.extents[2] for m in HALVES.values()) <= ci.TRAY_H - 1.0 + 0.01


@pytest.mark.parametrize("side", SIDES)
def test_each_half_fits_the_bed(side):
    w, d, _ = HALVES[side].extents
    assert w <= 256 and d <= 256


@pytest.mark.parametrize("side", SIDES)
def test_each_half_is_one_printable_body(side):
    m = HALVES[side]
    assert m.is_watertight
    assert m.body_count == 1


@pytest.mark.parametrize("side", SIDES)
def test_the_outer_corners_are_chamfered(side):
    """A square corner would sit on any wood rounding or glue in the tray's corner."""
    m = HALVES[side]
    z = ci.HEIGHT / 2
    for x, y in ((0.3, 0.3), (ci.HALF_W - 0.3, 0.3), (0.3, ci.INSERT_D - 0.3),
                 (ci.HALF_W - 0.3, ci.INSERT_D - 0.3)):
        assert not _solid(m, x, y, z), f"corner at ({x}, {y}) is square"
    assert _solid(m, ci.CHAMFER + 0.5, 0.3, z), "the wall next to the chamfer is missing"


# --- every bay is a real opening -------------------------------------------

def _bay_cases():
    for side in SIDES:
        for name in ci.bays(side):
            yield side, name


@pytest.mark.parametrize("side, name", list(_bay_cases()))
def test_every_bay_is_open_with_a_floor_under_it(side, name):
    m, bay = HALVES[side], ci.bays(side)[name]
    assert not _solid(m, bay.cx, bay.cy, ci.HEIGHT - 0.5), f"{name} is closed at the top"
    assert _solid(m, bay.cx, bay.cy, ci.FLOOR / 2), f"{name} has no floor"
    if name != "badge":                       # the badge pocket has a raised floor
        assert not _solid(m, bay.cx, bay.cy, ci.FLOOR + 0.5), f"{name} is not cut to the floor"


@pytest.mark.parametrize("side", SIDES)
def test_neighbouring_bays_are_separated_by_a_wall(side):
    m, b = HALVES[side], ci.bays(side)
    z = ci.HEIGHT / 2
    pairs = {
        "left": [("pens_front", "pens_middle"), ("pens_middle", "pens_back"),
                 ("pens_back", "aaa"), ("aaa", "aa"),
                 ("aaa", "coins"), ("coins", "open_bin"), ("aa", "open_bin")],
        "right": [("usb", "badge"), ("badge", "fobs"), ("usb", "fobs")],
    }[side]
    for a, c in pairs:
        p, q = b[a], b[c]
        if math.isclose(p.y1 + ci.WALL, q.y0, abs_tol=0.01):      # c is behind a
            x = (max(p.x0, q.x0) + min(p.x1, q.x1)) / 2
            assert _solid(m, x, p.y1 + ci.WALL / 2, z), f"no wall between {a} and {c}"
        else:                                                     # c is right of a
            assert math.isclose(p.x1 + ci.WALL, q.x0, abs_tol=0.01), f"{a}/{c} do not touch"
            y = (max(p.y0, q.y0) + min(p.y1, q.y1)) / 2
            assert _solid(m, p.x1 + ci.WALL / 2, y, z), f"no wall between {a} and {c}"


# --- the measured things fit ------------------------------------------------

def test_the_badge_has_room_on_every_side():
    """Stood upright: the 70 mm side runs across, the 110 mm side front to back.
    The sides get finger room; the ends gave some up (3 mm) to line the USB wall
    up with the left half, which Richard approved."""
    bay = ci.bays("right")["badge"]
    long_side, short_side = ci.BADGE
    assert (bay.w - short_side) / 2 >= 5.0
    assert (bay.d - long_side) / 2 >= 3.0


def test_the_cards_lie_in_the_badge_pocket():
    bay = ci.bays("right")["badge"]
    assert ci.CARD[1] < bay.w and ci.CARD[0] < bay.d


def test_both_fobs_fit_end_to_end_with_finger_room_beside_them():
    bay = ci.bays("right")["fobs"]
    assert ci.FOB_BIG[0] + ci.FOB_SMALL[0] <= bay.d
    assert (bay.w - ci.FOB_BIG[1]) / 2 >= 10.0
    assert (bay.w - ci.FOB_SMALL[1]) / 2 >= 10.0


def test_the_fob_lane_has_no_divider():
    m, bay = HALVES["right"], ci.bays("right")["fobs"]
    for y in range(int(bay.y0) + 2, int(bay.y1) - 1, 5):
        assert not _solid(m, bay.cx, y, ci.HEIGHT / 2), f"something blocks the lane at y={y}"


@pytest.mark.parametrize("name, cell", [("aa", "AA"), ("aaa", "AAA")])
def test_batteries_lie_flat_in_their_bay(name, cell):
    bay = ci.bays("left")[name]
    length, dia = getattr(ci, cell)
    assert length < bay.d, f"{cell} does not lie front to back"
    nested_two_layers = dia + dia * math.sin(math.radians(60))
    assert ci.FLOOR + nested_two_layers < ci.HEIGHT, f"a second layer of {cell} sticks out"


def test_three_full_length_channels_one_for_the_letter_opener():
    """Pens, screwdrivers and the letter opener: three channels the same size."""
    channels = [ci.bays("left")[n] for n in ("pens_front", "pens_middle", "pens_back")]
    for bay in channels:
        assert bay.w >= ci.LONGEST_TOOL
        assert math.isclose(bay.d, ci.PEN_CHANNEL, abs_tol=0.01)


def test_the_right_halfs_divider_lines_up_with_the_left_halfs():
    left, right = HALVES["left"], HALVES["right"]
    wall_y = ci.bays("left")["pens_middle"].y1 + ci.WALL / 2
    z = ci.HEIGHT - 1.0          # above the badge's raised floor: only a wall is solid here
    assert _solid(left, ci.HALF_W / 2, wall_y, z)
    usb = ci.bays("right")["usb"]
    assert _solid(right, usb.cx, wall_y, z), "right half's wall is not in line"
    assert math.isclose(usb.y1, ci.bays("left")["pens_middle"].y1, abs_tol=0.01)


# --- the shaped bays ---------------------------------------------------------

def test_the_coin_cup_is_scooped_at_the_front_and_back_edges():
    m, bay = HALVES["left"], ci.bays("left")["coins"]
    corner = ci.FLOOR + 1.0
    assert _solid(m, bay.cx, bay.y0 + 1.0, corner), "front edge of the coin cup is square"
    assert _solid(m, bay.cx, bay.y1 - 1.0, corner), "back edge of the coin cup is square"
    assert not _solid(m, bay.cx, bay.cy, corner), "the coin cup has no flat middle"
    flat = bay.d - 2 * ci.COIN_SCOOP_R
    assert flat >= 10.0, f"only {flat:.1f} mm of flat floor -- coins would lie tilted"


def test_the_badge_sits_on_a_raised_floor_near_the_top():
    m, bay = HALVES["right"], ci.bays("right")["badge"]
    deck = ci.HEIGHT - ci.BADGE_POCKET_DEPTH
    assert _solid(m, bay.cx, bay.cy, deck - 1.0), "badge pocket floor is not raised"
    assert not _solid(m, bay.cx, bay.cy, deck + 1.0), "badge pocket is not open above its floor"


def test_bays_refuses_an_unknown_side():
    with pytest.raises(ValueError):
        ci.bays("middle")


def test_the_finger_dips_reach_under_the_badge_edge():
    m, bay = HALVES["right"], ci.bays("right")["badge"]
    room = (bay.w - ci.BADGE[1]) / 2
    z = ci.HEIGHT - ci.BADGE_POCKET_DEPTH - 1.0
    for x in (bay.x0 + room + 1.0, bay.x1 - room - 1.0):
        assert not _solid(m, x, bay.cy, z), f"no finger dip under the badge at x={x:.1f}"
    assert _solid(m, bay.cx, bay.cy, z), "the dips have eaten the whole floor"


def test_the_finger_dips_stop_short_of_the_base():
    """Deep enough for a fingertip, not a well that swallows coins and crumbs."""
    m, bay = HALVES["right"], ci.bays("right")["badge"]
    deck = ci.HEIGHT - ci.BADGE_POCKET_DEPTH
    x = bay.x0 + 3.0
    assert not _solid(m, x, bay.cy, deck - ci.FINGER_DIP_DEPTH + 0.5)
    assert _solid(m, x, bay.cy, deck - ci.FINGER_DIP_DEPTH - 0.5), "dip goes deeper than planned"


# --- fit-test outlines -------------------------------------------------------

@pytest.mark.parametrize("side", SIDES)
def test_the_fit_test_is_a_short_floorless_outline_of_the_same_footprint(side):
    t, full = FIT_TESTS[side], HALVES[side]
    assert math.isclose(t.extents[2], ci.FIT_TEST_H, abs_tol=0.02)
    assert math.isclose(t.extents[0], full.extents[0], abs_tol=0.02)
    assert math.isclose(t.extents[1], full.extents[1], abs_tol=0.02)
    assert t.is_watertight and t.body_count == 1
    for bay in ci.bays(side).values():
        assert not _solid(t, bay.cx, bay.cy, ci.FLOOR / 2), "fit test has a floor"


def test_the_preview_is_written_as_a_png(tmp_path):
    out = tmp_path / "preview.png"
    ci.save_preview(str(out))
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
