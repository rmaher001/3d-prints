"""Invariants for the desk drawer tray insert (rev 3).

Three things have to hold. The halves must drop into the wooden tray and each fit
the P2S bed. Every region must be what it claims -- a bin open to its floor, or a
raised shelf whose items sit near the top. And the things Richard keeps in the
tray must fit the places meant for them: one pen per groove, one battery per
slot, a stack of cards in a pocket he can pinch.

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
STRIP = ci.build_groove_strip()
LEFT, RIGHT = ci.bays("left"), ci.bays("right")


def _solid(mesh, x, y, z):
    return bool(mesh.contains([[x, y, z]])[0])


# --- it fits the tray and the printer --------------------------------------

@pytest.mark.parametrize("side", SIDES)
def test_each_half_has_the_planned_envelope(side):
    w, d, h = HALVES[side].extents
    assert math.isclose(w, ci.HALF_W, abs_tol=0.02)
    assert math.isclose(d, ci.INSERT_D, abs_tol=0.02)
    assert math.isclose(h, ci.HEIGHT, abs_tol=0.02)


FIT_TESTED = (365.5, 179.5)     # 2nd fit test, cooled on the plate (2026-09-23)
PLAY = (1.0, 0.5)               # what Richard measured left over: side to side, front to back


def test_the_halves_take_up_the_play_the_fit_test_showed():
    """The tray is bigger than the tape said. The 2nd outline pair left 1 mm of
    play side to side and 0.5 mm front to back; the insert grows by exactly that."""
    across = HALVES["left"].extents[0] + HALVES["right"].extents[0]
    front_to_back = max(m.extents[1] for m in HALVES.values())
    assert math.isclose(across, FIT_TESTED[0] + PLAY[0], abs_tol=0.02), f"{across:.2f} mm across"
    assert math.isclose(front_to_back, FIT_TESTED[1] + PLAY[1], abs_tol=0.02), f"{front_to_back:.2f} mm deep"


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


@pytest.mark.parametrize("side", SIDES)
def test_every_region_keeps_a_full_outer_wall(side):
    m, z = HALVES[side], ci.HEIGHT - 0.5
    for name, b in ci.bays(side).items():
        assert b.x0 >= ci.WALL - 1e-6 and b.y0 >= ci.WALL - 1e-6, f"{name} eats the outer wall"
        assert b.x1 <= ci.HALF_W - ci.WALL + 1e-6 and b.y1 <= ci.INSERT_D - ci.WALL + 1e-6, \
            f"{name} eats the outer wall"
    for x, y in ((ci.WALL / 2, ci.INSERT_D / 2), (ci.HALF_W - ci.WALL / 2, ci.INSERT_D / 2),
                 (ci.HALF_W / 2, ci.WALL / 2), (ci.HALF_W / 2, ci.INSERT_D - ci.WALL / 2)):
        assert _solid(m, x, y, z), f"outer wall missing at ({x:.1f}, {y:.1f})"


def test_bays_refuses_an_unknown_side():
    with pytest.raises(ValueError):
        ci.bays("middle")


# --- the layout that was approved ------------------------------------------

def test_the_approved_regions_and_nothing_else():
    assert set(LEFT) == {"pen_shelf", "aa", "aaa", "coins"}
    assert set(RIGHT) == {"cards", "usb", "open_bin", "fobs"}


def test_front_to_back_order_on_the_right():
    """Cards at the front, then USB/SD, then the open bin -- as drawn."""
    assert RIGHT["cards"].y0 < RIGHT["usb"].y0 < RIGHT["open_bin"].y0


@pytest.mark.parametrize("side", SIDES)
def test_neighbouring_regions_are_separated_by_a_wall(side):
    m, b = HALVES[side], ci.bays(side)
    z = ci.HEIGHT - 0.5          # at the very top, above every raised shelf
    pairs = {
        "left": [("pen_shelf", "aa"), ("pen_shelf", "aaa"), ("pen_shelf", "coins"),
                 ("aa", "aaa"), ("aaa", "coins")],
        "right": [("cards", "usb"), ("usb", "open_bin"), ("cards", "fobs"),
                  ("usb", "fobs"), ("open_bin", "fobs")],
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


def test_the_right_halfs_bin_wall_lines_up_with_the_pen_shelf_wall():
    wall_y = LEFT["pen_shelf"].y1 + ci.WALL / 2
    z = ci.HEIGHT - 0.5
    assert math.isclose(RIGHT["usb"].y1, LEFT["pen_shelf"].y1, abs_tol=0.01)
    assert _solid(HALVES["left"], LEFT["pen_shelf"].cx, wall_y, z)
    assert _solid(HALVES["right"], RIGHT["usb"].cx, wall_y, z), "right half's wall is not in line"


@pytest.mark.parametrize("side, name", [("left", "coins"), ("right", "usb"),
                                        ("right", "open_bin"), ("right", "fobs")])
def test_the_bins_are_open_down_to_the_floor(side, name):
    m, bay = HALVES[side], ci.bays(side)[name]
    assert not _solid(m, bay.cx, bay.cy, ci.FLOOR + 0.5), f"{name} is not cut to the floor"
    assert _solid(m, bay.cx, bay.cy, ci.FLOOR / 2), f"{name} has no floor"


# --- pens, pencil, Sharpie, screwdrivers, letter opener --------------------

def test_one_groove_per_item_plus_the_letter_opener_slot():
    names = [n for n, _ in ci.grooves()]
    assert names == ["pen", "pencil", "sharpie", "screwdriver_1", "screwdriver_2", "letter_opener"]


def test_the_grooves_fill_the_pen_shelf_front_to_back():
    g = ci.grooves()
    shelf = LEFT["pen_shelf"]
    assert math.isclose(g[0][1].y0, shelf.y0, abs_tol=0.01)
    assert math.isclose(g[-1][1].y1, shelf.y1, abs_tol=0.01)


@pytest.mark.parametrize("name, groove", ci.grooves()[:5])
def test_each_round_groove_takes_the_fattest_item_below_the_top(name, groove):
    """A 16 mm item lies in it with room at the sides and without poking out."""
    assert groove.w >= ci.LONGEST_TOOL
    assert groove.d >= ci.MAX_PEN_DIA + 1.0
    assert ci.GROOVE_DEPTH >= ci.MAX_PEN_DIA


@pytest.mark.parametrize("name, groove", ci.grooves())
def test_each_groove_is_cut_to_its_depth_on_a_raised_shelf(name, groove):
    m = HALVES["left"]
    bottom = ci.HEIGHT - ci.GROOVE_DEPTH
    x = groove.x0 + 20.0                      # clear of the finger trough
    assert not _solid(m, x, groove.cy, bottom + 0.5), f"{name} is not cut to its depth"
    assert _solid(m, x, groove.cy, bottom - 0.5), f"{name} has no raised floor under it"


def test_round_grooves_have_round_bottoms_and_the_opener_slot_is_flat():
    m = HALVES["left"]
    x = 20.0
    z = ci.HEIGHT - ci.GROOVE_DEPTH + 0.8     # just above the bottom
    pen = dict(ci.grooves())["pen"]
    assert _solid(m, x, pen.y0 + 0.8, z), "pen groove has a square bottom corner"
    # a true half-pipe: a quarter of the way across, 1 mm up, is still under the curve
    bottom = ci.HEIGHT - ci.GROOVE_DEPTH
    assert _solid(m, x, pen.y0 + pen.d / 4, bottom + 1.0), "pen groove is flat-bottomed"
    opener = dict(ci.grooves())["letter_opener"]
    assert not _solid(m, x, opener.y0 + 0.8, z), "letter opener slot is not flat"


def test_ridges_separate_neighbouring_grooves():
    m = HALVES["left"]
    g = [b for _, b in ci.grooves()]
    for a, b in zip(g, g[1:]):
        assert _solid(m, 20.0, (a.y1 + b.y0) / 2, ci.HEIGHT - 1.0), "grooves run into each other"


def test_a_finger_trough_crosses_the_grooves_so_items_can_be_lifted():
    m, shelf = HALVES["left"], LEFT["pen_shelf"]
    under = ci.HEIGHT - ci.GROOVE_DEPTH - 2.0
    for _, g in ci.grooves():
        assert not _solid(m, shelf.cx, g.cy, under), "no trough under the middle of a groove"
    assert _solid(m, shelf.cx, shelf.cy, ci.FLOOR / 2), "the trough went through the floor"


# --- batteries ---------------------------------------------------------------

@pytest.mark.parametrize("kind, cell", [("aa", ci.AA), ("aaa", ci.AAA)])
def test_four_battery_slots_each_holding_one_cell_below_the_top(kind, cell):
    slots = ci.battery_slots(kind)
    length, dia = cell
    assert len(slots) == 4
    for s in slots:
        assert s.d >= length + 1.0, "cell does not lie in the slot"
        assert s.w >= dia + 1.0, "slot too narrow for the cell"
        assert ci.slot_depth(kind) - dia >= 0.5, "cell sits flush with, or above, the top"
    region = LEFT[kind]
    eps = 1e-6                                # float noise, e.g. 68.80000000000001
    assert all(region.x0 - eps <= s.x0 and s.x1 <= region.x1 + eps
               and region.y0 - eps <= s.y0 and s.y1 <= region.y1 + eps
               for s in slots), "a slot is outside its region"


@pytest.mark.parametrize("kind", ["aa", "aaa"])
def test_battery_slots_are_separate_and_raised(kind):
    m = HALVES["left"]
    slots = ci.battery_slots(kind)
    bottom = ci.HEIGHT - ci.slot_depth(kind)
    y = slots[0].y0 + 3.0                     # clear of the finger trough
    for s in slots:
        assert not _solid(m, s.cx, y, bottom + 0.8)
        assert _solid(m, s.cx, y, bottom - 0.5), "slot has no raised floor"
    for a, b in zip(slots, slots[1:]):
        assert _solid(m, (a.x1 + b.x0) / 2, y, ci.HEIGHT - 1.0), "slots run into each other"


@pytest.mark.parametrize("kind", ["aa", "aaa"])
def test_a_finger_trough_crosses_the_battery_slots(kind):
    m = HALVES["left"]
    s = ci.battery_slots(kind)[0]
    assert not _solid(m, s.cx, s.cy, ci.HEIGHT - ci.slot_depth(kind) - 2.0)


# --- coins -----------------------------------------------------------------

def test_the_coin_cup_is_scooped_with_a_flat_middle():
    m, bay = HALVES["left"], LEFT["coins"]
    corner = ci.FLOOR + 1.0
    assert _solid(m, bay.cx, bay.y0 + 1.0, corner), "front edge of the coin cup is square"
    assert _solid(m, bay.cx, bay.y1 - 1.0, corner), "back edge of the coin cup is square"
    assert not _solid(m, bay.cx, bay.cy, corner), "the coin cup has no flat middle"
    assert bay.d - 2 * ci.COIN_SCOOP_R >= 10.0, "coins would lie tilted"
    # a 10 mm curve: 3 mm in and 8 mm up is already open; a bigger one would still be solid
    assert not _solid(m, bay.cx, bay.y0 + 3.0, ci.FLOOR + 8.0), "the scoop is bigger than planned"


# --- cards -----------------------------------------------------------------

def test_the_card_pocket_takes_ten_cards_lying_flat():
    bay = RIGHT["cards"]
    assert bay.w >= ci.CARD[0] + 4.0 and bay.d >= ci.CARD[1] + 4.0
    assert ci.CARD_POCKET_DEPTH >= ci.CARD_STACK + 2.0


def test_the_card_pocket_has_a_raised_floor():
    m, bay = HALVES["right"], RIGHT["cards"]
    deck = ci.HEIGHT - ci.CARD_POCKET_DEPTH
    assert _solid(m, bay.cx, bay.cy, deck - 1.0), "card pocket floor is not raised"
    assert not _solid(m, bay.cx, bay.cy, deck + 1.0), "card pocket is not open above its floor"


def test_the_finger_dips_reach_under_the_card_ends():
    m, bay = HALVES["right"], RIGHT["cards"]
    room = (bay.w - ci.CARD[0]) / 2
    z = ci.HEIGHT - ci.CARD_POCKET_DEPTH - 1.0
    for x in (bay.x0 + room + 3.0, bay.x1 - room - 3.0):
        assert not _solid(m, x, bay.cy, z), f"no finger dip under the card end at x={x:.1f}"
    assert _solid(m, bay.cx, bay.cy, z), "the dips have eaten the whole floor"
    x = bay.x0 + 3.0
    deck = ci.HEIGHT - ci.CARD_POCKET_DEPTH
    assert not _solid(m, x, bay.cy, deck - ci.FINGER_DIP_DEPTH + 0.5), "dip is shallower than planned"
    assert _solid(m, x, bay.cy, deck - ci.FINGER_DIP_DEPTH - 0.5), "dip goes deeper than planned"


# --- key fobs ----------------------------------------------------------------

def test_both_fobs_fit_end_to_end_with_finger_room_beside_them():
    bay = RIGHT["fobs"]
    assert ci.FOB_BIG[0] + ci.FOB_SMALL[0] <= bay.d
    assert (bay.w - ci.FOB_BIG[1]) / 2 >= 10.0
    assert (bay.w - ci.FOB_SMALL[1]) / 2 >= 10.0


def test_the_fob_lane_has_no_divider():
    m, bay = HALVES["right"], RIGHT["fobs"]
    for y in range(int(bay.y0) + 2, int(bay.y1) - 1, 5):
        assert not _solid(m, bay.cx, y, ci.HEIGHT / 2), f"something blocks the lane at y={y}"


# --- the prints for checking before the real one ---------------------------

@pytest.mark.parametrize("side", SIDES)
def test_the_fit_test_is_a_short_floorless_outline_of_the_same_footprint(side):
    t, full = FIT_TESTS[side], HALVES[side]
    assert math.isclose(t.extents[2], ci.FIT_TEST_H, abs_tol=0.02)
    assert math.isclose(t.extents[0], full.extents[0], abs_tol=0.02)
    assert math.isclose(t.extents[1], full.extents[1], abs_tol=0.02)
    assert t.is_watertight and t.body_count == 1
    for bay in ci.bays(side).values():
        assert not _solid(t, bay.cx, bay.cy, ci.FLOOR / 2), "fit test has a floor"
        assert not _solid(t, bay.cx, bay.cy, ci.FIT_TEST_H - 0.3), "fit test has a lid"


def test_the_groove_strip_is_a_short_slice_of_the_real_pen_shelf():
    """Prints in minutes; every pen and screwdriver can be tried in its groove."""
    w, d, h = STRIP.extents
    assert math.isclose(w, ci.STRIP_L, abs_tol=0.02)
    assert d >= LEFT["pen_shelf"].y1 and math.isclose(h, ci.HEIGHT, abs_tol=0.02)
    assert STRIP.is_watertight and STRIP.body_count == 1
    x = STRIP.bounds[0][0] + ci.STRIP_L / 2
    for name, g in ci.grooves():
        bottom = ci.HEIGHT - ci.GROOVE_DEPTH
        assert not _solid(STRIP, x, g.cy, bottom + 0.8), f"{name} groove missing from the strip"
        assert _solid(STRIP, x, g.cy, bottom - 0.5), f"{name} groove in the strip has no floor"


def test_the_preview_shows_both_halves_side_by_side(tmp_path):
    import matplotlib.image as mpimg
    out = tmp_path / "preview.png"
    drawn_width = ci.save_preview(str(out))
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    h, w = mpimg.imread(str(out)).shape[:2]
    assert w / h > 1.6, "the picture is not wide"
    assert math.isclose(drawn_width, ci.INSERT_W, abs_tol=0.5), "the halves are not side by side"


def test_main_writes_every_print_file_and_the_preview(tmp_path):
    ci.main(str(tmp_path))
    for name in ("left", "right", "fit-test-left", "fit-test-right", "groove-test"):
        f = tmp_path / f"desk-drawer-tray-insert-{name}.stl"
        assert f.stat().st_size > 1000, f"{f.name} missing or empty"
    assert (tmp_path / "preview-layout.png").exists()
