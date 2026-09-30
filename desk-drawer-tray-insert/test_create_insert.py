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
WIDTH_TEST = ci.build_width_test()
LEFT, RIGHT = ci.bays("left"), ci.bays("right")


def _solid(mesh, x, y, z):
    return bool(mesh.contains([[x, y, z]])[0])


# --- it fits the tray and the printer --------------------------------------

@pytest.mark.parametrize("side", SIDES)
def test_each_half_has_the_planned_envelope(side):
    w, d, h = HALVES[side].extents
    assert math.isclose(w, ci.half_w(side), abs_tol=0.02)
    assert math.isclose(d, ci.INSERT_D, abs_tol=0.02)
    assert math.isclose(h, ci.HEIGHT, abs_tol=0.02)


FIT_TESTED = (365.5, 179.5)     # 2nd fit test, cooled on the plate (2026-09-23)
PLAY = (1.0, 0.5)               # what Richard measured left over: side to side, front to back


def test_the_halves_take_up_the_play_the_fit_test_showed():
    """The tray is bigger than the tape said. The 2nd outline pair left 1 mm of
    play side to side and 0.5 mm front to back; the insert grows by exactly that."""
    across = HALVES["left"].extents[0] + HALVES["right"].extents[0]
    front_to_back = max(m.extents[1] for m in HALVES.values())
    assert math.isclose(across, FIT_TESTED[0] + PLAY[0] - ci.RIGHT_TRIM, abs_tol=0.02), f"{across:.2f} mm across"
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
    for x, y in ((0.3, 0.3), (ci.half_w(side) - 0.3, 0.3), (0.3, ci.INSERT_D - 0.3),
                 (ci.half_w(side) - 0.3, ci.INSERT_D - 0.3)):
        assert not _solid(m, x, y, z), f"corner at ({x}, {y}) is square"
    assert _solid(m, ci.CHAMFER + 0.5, 0.3, z), "the wall next to the chamfer is missing"


@pytest.mark.parametrize("side", SIDES)
def test_every_region_keeps_a_full_outer_wall(side):
    m, z = HALVES[side], ci.HEIGHT - 0.5
    for name, b in ci.bays(side).items():
        assert b.x0 >= ci.WALL - 1e-6 and b.y0 >= ci.WALL - 1e-6, f"{name} eats the outer wall"
        assert b.x1 <= ci.half_w(side) - ci.WALL + 1e-6 and b.y1 <= ci.INSERT_D - ci.WALL + 1e-6, \
            f"{name} eats the outer wall"
    for x, y in ((ci.WALL / 2, ci.INSERT_D / 2), (ci.half_w(side) - ci.WALL / 2, ci.INSERT_D / 2),
                 (ci.half_w(side) / 2, ci.WALL / 2), (ci.half_w(side) / 2, ci.INSERT_D - ci.WALL / 2)):
        assert _solid(m, x, y, z), f"outer wall missing at ({x:.1f}, {y:.1f})"


def test_bays_refuses_an_unknown_side():
    with pytest.raises(ValueError):
        ci.bays("middle")


# --- the layout that was approved ------------------------------------------

def test_the_approved_regions_and_nothing_else():
    assert set(LEFT) == {"pen_shelf", "aa", "aaa", "coins"}
    assert set(RIGHT) == {"cards", "tools", "keys", "open_bin", "fobs"}


def test_front_to_back_order_on_the_right():
    """Cards at the front, then USB/SD, then the open bin -- as drawn."""
    assert RIGHT["cards"].y0 < RIGHT["tools"].y0 < RIGHT["open_bin"].y0


@pytest.mark.parametrize("side", SIDES)
def test_neighbouring_regions_are_separated_by_a_wall(side):
    m, b = HALVES[side], ci.bays(side)
    z = ci.HEIGHT - 0.5          # at the very top, above every raised shelf
    pairs = {
        "left": [("pen_shelf", "aa"), ("pen_shelf", "aaa"), ("pen_shelf", "coins"),
                 ("aa", "aaa"), ("aaa", "coins")],
        "right": [("cards", "tools"), ("tools", "open_bin"), ("cards", "fobs"),
                  ("tools", "fobs"), ("open_bin", "fobs"), ("tools", "keys"), ("keys", "open_bin")],
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


def test_the_tools_bay_reaches_a_little_past_the_pen_shelf_to_make_room_for_the_strips():
    assert RIGHT["tools"].y1 > LEFT["pen_shelf"].y1
    assert math.isclose(RIGHT["tools"].y1, LEFT["pen_shelf"].y1 + ci.TOOLS_EXTRA, abs_tol=0.01)


@pytest.mark.parametrize("side, name", [("left", "coins"),
                                        ("right", "open_bin"), ("right", "keys"),
                                        ("right", "fobs")])
def test_the_bins_are_open_down_to_the_floor(side, name):
    m, bay = HALVES[side], ci.bays(side)[name]
    assert not _solid(m, bay.cx, bay.cy, ci.FLOOR + 0.5), f"{name} is not cut to the floor"
    assert _solid(m, bay.cx, bay.cy, ci.FLOOR / 2), f"{name} has no floor"


# --- pens, pencil, Sharpie, screwdrivers, pen cutter ------------------------------------

def test_one_groove_per_item_plus_the_pen_cutter_slot():
    names = [n for n, _ in ci.grooves()]
    assert names == ["pen", "pencil", "sharpie", "screwdriver_1", "screwdriver_2", "pen_cutter"]


def test_the_grooves_fill_the_pen_shelf_front_to_back():
    g = ci.grooves()
    shelf = LEFT["pen_shelf"]
    assert math.isclose(g[0][1].y0, shelf.y0, abs_tol=0.01)
    assert math.isclose(g[-1][1].y1, shelf.y1, abs_tol=0.01)


@pytest.mark.parametrize("name, groove", ci.grooves()[:5])
def test_each_round_groove_holds_the_fattest_item_and_it_stands_proud(name, groove):
    """A 16 mm item lies in it with room at the sides, held below its widest point,
    and stands proud of the top so a fingertip can pinch it."""
    # the tool lies against the far wall: flat groove, then it may overhang the cup by up to half the cup
    assert groove.w - ci.CUP_L / 2.0 >= ci.LONGEST_TOOL
    assert groove.d >= ci.MAX_PEN_DIA + 1.0
    assert ci.GROOVE_DEPTH >= ci.MAX_PEN_DIA / 2.0 + 2.0      # deeper than its centre line
    assert ci.GROOVE_DEPTH < ci.MAX_PEN_DIA                   # so it stands proud


def test_every_groove_is_the_same_size():
    sizes = {(round(g.d, 3)) for _, g in ci.grooves()}
    assert len(sizes) == 1
    assert ci.CUTTER_SLOT_DEPTH == ci.GROOVE_DEPTH


@pytest.mark.parametrize("name, groove", ci.grooves())
def test_each_groove_is_cut_to_its_depth_on_a_raised_shelf(name, groove):
    m = HALVES["left"]
    depth = ci.CUTTER_SLOT_DEPTH if name == "pen_cutter" else ci.GROOVE_DEPTH
    bottom = ci.HEIGHT - depth
    x = groove.x0 + 20.0                      # clear of the finger trough
    assert not _solid(m, x, groove.cy, bottom + 0.5), f"{name} is not cut to its depth"
    assert _solid(m, x, groove.cy, bottom - 0.5), f"{name} has no raised floor under it"


def test_every_groove_including_the_pen_cutters_has_a_round_bottom():
    m = HALVES["left"]
    x = 20.0
    z = ci.HEIGHT - ci.GROOVE_DEPTH + 0.8     # just above the bottom
    pen = dict(ci.grooves())["pen"]
    assert _solid(m, x, pen.y0 + 0.8, z), "pen groove has a square bottom corner"
    # a true half-pipe: a quarter of the way across, 1 mm up, is still under the curve
    bottom = ci.HEIGHT - ci.GROOVE_DEPTH
    assert _solid(m, x, pen.y0 + pen.d / 4, bottom + 1.0), "pen groove is flat-bottomed"
    cutter = dict(ci.grooves())["pen_cutter"]
    cbottom = ci.HEIGHT - ci.CUTTER_SLOT_DEPTH
    assert _solid(m, x, cutter.y0 + 0.8, cbottom + 0.8), "pen cutter groove has a square bottom corner"
    assert _solid(m, x, cutter.y0 + cutter.d / 4, cbottom + 1.0), "pen cutter groove is flat-bottomed"


def test_the_pen_cutter_groove_holds_the_slice_10513():
    """133.5 long, 17.5 at the thick end (measured): the groove is longer and just wider than that."""
    cutter = dict(ci.grooves())["pen_cutter"]
    assert cutter.w >= ci.CUTTER_L and cutter.d >= ci.CUTTER_DIA + 0.4
    assert ci.CUTTER_SLOT_DEPTH >= ci.CUTTER_DIA / 2.0 + 2.0


# --- key fobs ----------------------------------------------------------------

def test_both_fobs_stand_upright_end_to_end_with_room_beside_them():
    bay = RIGHT["fobs"]
    assert ci.FOB_BIG[0] + ci.FOB_SMALL[0] <= bay.d
    assert (bay.w - ci.FOB_BIG[1]) / 2 >= 7.0       # they stand upright, so the lane is only as wide as a fob
    assert (bay.w - ci.FOB_SMALL[1]) / 2 >= 7.0


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


def test_the_groove_strip_is_one_groove_of_the_real_pen_shelf():
    """All the round grooves are the same, so one long enough for a pen tests every item."""
    name, g = ci.grooves()[0]
    w, d, h = STRIP.extents
    assert math.isclose(w, ci.STRIP_L, abs_tol=0.02) and ci.STRIP_L >= 100
    assert math.isclose(d, g.y1 + ci.RIDGE, abs_tol=0.02) and math.isclose(h, ci.HEIGHT, abs_tol=0.02)
    assert STRIP.is_watertight and STRIP.body_count == 1
    x = STRIP.bounds[0][0] + ci.STRIP_L / 2
    bottom = ci.HEIGHT - ci.GROOVE_DEPTH
    assert not _solid(STRIP, x, g.cy, bottom + 0.8), "the groove is missing from the strip"
    assert _solid(STRIP, x, g.cy, bottom - 0.5), "the groove in the strip has no floor"


def test_the_preview_shows_both_halves_side_by_side(tmp_path):
    import matplotlib.image as mpimg
    out = tmp_path / "preview.png"
    drawn_width = ci.save_preview(str(out))
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    h, w = mpimg.imread(str(out)).shape[:2]
    assert w / h > 1.6, "the picture is not wide"
    assert math.isclose(drawn_width, ci.INSERT_W - ci.RIGHT_TRIM, abs_tol=0.5), "the halves are not side by side"


def test_main_writes_every_print_file_and_the_preview(tmp_path):
    ci.main(str(tmp_path))
    for name in ("left", "right", "fit-test-left", "fit-test-right", "groove-test"):
        f = tmp_path / f"desk-drawer-tray-insert-{name}.stl"
        assert f.stat().st_size > 1000, f"{f.name} missing or empty"
    assert (tmp_path / "preview-layout.png").exists()

# --- restored, then updated for the current design ---------------------------

def test_ridges_separate_neighbouring_grooves():
    m = HALVES["left"]
    g = [b for _, b in ci.grooves()]
    for a, b in zip(g, g[1:]):
        assert _solid(m, 20.0, (a.y1 + b.y0) / 2, ci.HEIGHT - 1.0), "grooves run into each other"


def test_each_groove_has_its_own_finger_cup_at_the_seam_end():
    """Items are shorter than their groove; the empty end is a deeper cup you reach from above,
    so one item can be lifted while every neighbour is still in place."""
    m, shelf = HALVES["left"], LEFT["pen_shelf"]
    bottom = ci.HEIGHT - ci.GROOVE_DEPTH
    x_in, x_out = shelf.x1 - ci.CUP_L / 2.0, shelf.x0 + 40.0
    for name, g in ci.grooves():
        assert not _solid(m, x_in, g.cy, bottom - ci.CUP_EXTRA + 0.8), f"{name} has no cup"
        assert _solid(m, x_in, g.cy, bottom - ci.CUP_EXTRA - 0.5), f"{name} cup has no floor"
        assert _solid(m, x_out, g.cy, bottom - 0.5), f"{name} groove floor is missing"
    for (_, a), (_, b) in zip(ci.grooves(), ci.grooves()[1:]):
        y = (a.y1 + b.y0) / 2.0
        assert _solid(m, x_in, y, ci.HEIGHT - 0.5), "a ridge between two cups is gone"


def test_there_is_no_scoop_across_the_middle_of_the_grooves():
    m, shelf = HALVES["left"], LEFT["pen_shelf"]
    bottom = ci.HEIGHT - ci.GROOVE_DEPTH
    for _, g in ci.grooves():
        assert _solid(m, shelf.cx, g.cy, bottom - 0.5), "something is cut across the grooves' middle"



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


def test_the_coin_cup_is_scooped_with_a_flat_middle():
    m, bay = HALVES["left"], LEFT["coins"]
    corner = ci.FLOOR + 1.0
    assert _solid(m, bay.cx, bay.y0 + 1.0, corner), "front edge of the coin cup is square"
    assert _solid(m, bay.cx, bay.y1 - 1.0, corner), "back edge of the coin cup is square"
    assert not _solid(m, bay.cx, bay.cy, corner), "the coin cup has no flat middle"
    assert bay.d - 2 * ci.COIN_SCOOP_R >= 10.0, "coins would lie tilted"
    # a 10 mm curve: 3 mm in and 8 mm up is already open; a bigger one would still be solid
    assert not _solid(m, bay.cx, bay.y0 + 3.0, ci.FLOOR + 8.0), "the scoop is bigger than planned"


def test_the_card_pocket_takes_sixteen_cards_lying_flat_and_fits_them_snugly_front_to_back():
    bay = RIGHT["cards"]
    assert bay.w >= ci.CARD[0] + 4.0
    assert ci.CARD[1] + 3.0 <= bay.d <= ci.CARD[1] + 8.0
    assert ci.CARD_POCKET_DEPTH >= ci.CARD_STACK + 2.0 and ci.CARD_STACK >= 16.0


def test_the_card_pocket_floor_is_raised_only_a_little_and_has_no_scoops():
    m, bay = HALVES["right"], RIGHT["cards"]
    deck = ci.HEIGHT - ci.CARD_POCKET_DEPTH
    assert deck <= 5.0, "the card floor is raised more than it needs to be"
    for x in (bay.x0 + 3.0, bay.cx, bay.x1 - 3.0):
        assert _solid(m, x, bay.cy, deck - 1.0), f"card pocket floor is not solid at x={x:.1f}"
        assert not _solid(m, x, bay.cy, deck + 1.0), f"card pocket is not open at x={x:.1f}"


def test_the_keys_bay_and_the_usb_stick_bay_are_split_by_a_wall():
    keys, sticks = RIGHT["keys"], RIGHT["open_bin"]
    assert math.isclose(keys.x1 + ci.WALL, sticks.x0, abs_tol=0.01)
    assert keys.w >= 55.0, "the 50 mm brass key and the 45 mm security key must lie lengthwise"
    assert sticks.w >= 48.0, "a modern stick is up to ~48 mm"
    assert keys.d >= 40.0 and sticks.d >= 40.0, "the keys and sticks bins got too shallow"

    assert _solid(HALVES["right"], keys.x1 + ci.WALL / 2, keys.cy, ci.HEIGHT - 0.5)


def test_the_halves_add_up_to_the_tray():
    assert math.isclose(ci.half_w("left") + ci.half_w("right"), ci.INSERT_W - ci.RIGHT_TRIM, abs_tol=1e-6)
    assert max(ci.half_w("left"), ci.half_w("right")) <= 256.0 - 2.0     # the P2S bed


def test_the_tools_bay_has_three_round_tool_grooves_and_a_pocket_for_strips_and_blu_tack():
    m, bay = HALVES["right"], RIGHT["tools"]
    gs = ci.tool_grooves()
    assert len(gs) == 3
    bottom = ci.HEIGHT - ci.TOOL_DEPTH
    for g in gs:
        assert not _solid(m, g.cx, g.cy, bottom + 0.8), "a tool groove is missing"
        assert _solid(m, g.cx, g.cy, bottom - 0.5), "a tool groove has no floor"
    pocket_d = gs[-1].y0 - ci.WALL - bay.y0          # in front of the front-most groove
    assert pocket_d >= 20.0, "the strips and Blu-Tack pocket is too shallow"
    assert not _solid(m, bay.cx, bay.y0 + pocket_d / 2, ci.FLOOR + 0.5), "the pocket is not open"
    # a screwdriver lies against the right end; it may overhang its left cup by up to half the cup
    assert bay.w - ci.TOOL_CUP_L / 2.0 >= ci.SCREWDRIVER_L
    assert bay.w >= ci.ALLEN_LONG_ARM   # the allen key's long arm lies in the front groove, which has no cup


def test_the_width_test_is_a_one_inch_slice_cut_from_the_real_right_half():
    """The front 25.4 mm of the real half, full height and width: real walls, floors and bays."""
    w, d, h = WIDTH_TEST.extents
    assert math.isclose(w, ci.half_w("right"), abs_tol=0.02)
    assert math.isclose(d, 25.4, abs_tol=0.02) and math.isclose(h, ci.HEIGHT, abs_tol=0.02)
    assert WIDTH_TEST.is_watertight and WIDTH_TEST.body_count == 1
    for x in (0.3, w - 0.3):
        assert not _solid(WIDTH_TEST, x, 0.3, ci.HEIGHT / 2), "a front corner is not chamfered"
    cards, fobs = RIGHT["cards"], RIGHT["fobs"]
    deck = ci.HEIGHT - ci.CARD_POCKET_DEPTH
    assert _solid(WIDTH_TEST, cards.cx, 10.0, deck - 1.0) and not _solid(WIDTH_TEST, cards.cx, 10.0, deck + 1.0), \
        "the real card pocket floor is not in the slice"
    assert _solid(WIDTH_TEST, fobs.cx, 10.0, ci.FLOOR / 2) and not _solid(WIDTH_TEST, fobs.cx, 10.0, ci.FLOOR + 0.5), \
        "the real fob lane is not in the slice"
    assert _solid(WIDTH_TEST, cards.x1 + ci.WALL / 2, 10.0, ci.HEIGHT - 0.5), "the wall between the bays is missing"


def test_the_width_ladder_has_three_slices_each_narrower_than_the_last():
    ladder = ci.build_width_ladder()
    widths = [round(m.extents[0], 2) for _, m in ladder]
    assert widths == [182.25, 181.75, 181.25]
    assert [name for name, _ in ladder] == ["trim-1.0", "trim-1.5", "trim-2.0"]
    for _, m in ladder:
        assert m.is_watertight and math.isclose(m.extents[2], ci.HEIGHT, abs_tol=0.02)
    assert ci.RIGHT_TRIM == 1.0, "the ladder must not change the real trim"


def test_the_allen_key_has_a_slot_for_its_short_arm_at_the_end_of_the_front_tool_groove():
    """An L key lies flat: its long arm in the front tool groove, its short arm in a round slot
    running forward from the groove's right end at the same height."""
    m, bay = HALVES["right"], RIGHT["tools"]
    front = ci.tool_grooves()[-1]
    sx = bay.x1 - ci.HEX_STRIP_W / 2.0
    bottom = ci.HEIGHT - ci.TOOL_DEPTH
    for y in (front.cy, front.y0 - 6.0, bay.y0 + 4.0):
        assert not _solid(m, sx, y, bottom + 0.8), f"the short-arm slot is missing at y={y:.1f}"
        assert _solid(m, sx, y, bottom - 0.5), f"the short-arm slot has no floor at y={y:.1f}"
    assert front.cy - bay.y0 >= ci.HEX_SHORT_ARM + 5.0, "the allen key's 35 mm short arm does not fit"
    x_wall = bay.x1 - ci.HEX_STRIP_W - ci.WALL / 2.0
    assert _solid(m, x_wall, bay.y0 + 10.0, ci.HEIGHT - 0.5), "no wall between the strips pocket and the slot"
    assert not _solid(m, bay.x0 + 20.0, bay.y0 + 10.0, ci.FLOOR + 0.5), "the strips pocket is not open"


def test_each_screwdriver_groove_has_a_finger_cup_at_its_left_end_but_the_allen_key_groove_does_not():
    """Same idea as the pen grooves: the tool stops short of the cup, a fingertip goes under its end."""
    m, bay = HALVES["right"], RIGHT["tools"]
    gs = ci.tool_grooves()                       # back to front; the front one holds the allen key
    bottom = ci.HEIGHT - ci.TOOL_DEPTH
    cx = bay.x0 + ci.TOOL_CUP_L / 2.0
    for g in gs[:2]:
        assert not _solid(m, cx, g.cy, bottom - ci.TOOL_CUP_EXTRA + 0.8), "no cup in a screwdriver groove"
        assert _solid(m, cx, g.cy, bottom - ci.TOOL_CUP_EXTRA - 0.5), "the cup has no floor"
    assert _solid(m, cx, gs[2].cy, bottom - 0.5), "the allen key groove should have no cup"
    assert _solid(m, cx, (gs[0].y0 + gs[1].y1) / 2.0, ci.HEIGHT - 0.5), "the ridge between two cups is gone"


# --- dimensions the README promises, pinned against the mesh ----------------

def test_every_cup_and_scoop_leaves_at_least_3_mm_of_floor():
    assert ci.HEIGHT - ci.GROOVE_DEPTH - ci.CUP_EXTRA >= 3.0, "pen cup floor"
    assert ci.HEIGHT - ci.CUTTER_SLOT_DEPTH - ci.CUP_EXTRA >= 3.0, "pen cutter cup floor"
    assert ci.HEIGHT - ci.TOOL_DEPTH - ci.TOOL_CUP_EXTRA >= 3.0, "screwdriver cup floor"
    for kind in ("aa", "aaa"):
        assert ci.HEIGHT - ci.slot_depth(kind) - 3.0 >= 3.0, f"{kind} trough floor"
    m, sh = HALVES["left"], LEFT["pen_shelf"]
    g = ci.grooves()[0][1]
    cup_x = sh.x1 - ci.CUP_L / 2.0
    cup_bottom = ci.HEIGHT - ci.GROOVE_DEPTH - ci.CUP_EXTRA
    assert _solid(m, cup_x, g.cy, cup_bottom - 0.5) and _solid(m, cup_x, g.cy, 3.0 - 0.1), "no 3 mm floor under a pen cup"


def test_the_finger_cups_have_the_lengths_the_readme_states():
    m, sh = HALVES["left"], LEFT["pen_shelf"]
    g = ci.grooves()[0][1]
    z = ci.HEIGHT - ci.GROOVE_DEPTH - ci.CUP_EXTRA + 1.0
    assert not _solid(m, sh.x1 - ci.CUP_L + 1.0, g.cy, z), "a pen cup is shorter than CUP_L"
    assert _solid(m, sh.x1 - ci.CUP_L - 1.0, g.cy, z), "a pen cup is longer than CUP_L"
    mr, bay = HALVES["right"], RIGHT["tools"]
    t = ci.tool_grooves()[0]
    zt = ci.HEIGHT - ci.TOOL_DEPTH - ci.TOOL_CUP_EXTRA + 1.0
    assert not _solid(mr, bay.x0 + ci.TOOL_CUP_L - 1.0, t.cy, zt), "a tool cup is shorter than TOOL_CUP_L"
    assert _solid(mr, bay.x0 + ci.TOOL_CUP_L + 1.0, t.cy, zt), "a tool cup is longer than TOOL_CUP_L"


def test_the_tool_grooves_and_the_allen_slot_have_the_widths_the_readme_states():
    m, bay = HALVES["right"], RIGHT["tools"]
    x = bay.x0 + 50.0
    z = ci.HEIGHT - 0.5
    for g in ci.tool_grooves():
        assert not _solid(m, x, g.y0 + 0.5, z) and not _solid(m, x, g.y1 - 0.5, z), "a tool groove is narrower than TOOL_W"
        assert _solid(m, x, g.y0 - ci.RIDGE / 2.0, z), "no ridge in front of a tool groove"
    front = ci.tool_grooves()[-1]
    sx = bay.x1 - ci.HEX_STRIP_W / 2.0
    y = bay.y0 + 10.0
    half = ci.HEX_SLOT_W / 2.0
    assert not _solid(m, sx - half + 0.5, y, z) and not _solid(m, sx + half - 0.5, y, z), "the allen slot is narrower than HEX_SLOT_W"
    assert _solid(m, sx - half - 0.5, y, z) and _solid(m, sx + half + 0.5, y, z), "the allen slot is wider than HEX_SLOT_W"
    assert not _solid(m, sx, front.y0 - 0.3, ci.HEIGHT - ci.TOOL_DEPTH + 0.8), "the slot does not reach the groove"


def test_the_ridges_between_tool_grooves_and_the_wall_to_the_pocket_are_the_stated_thickness():
    m, bay = HALVES["right"], RIGHT["tools"]
    gs = ci.tool_grooves()
    x, z = bay.x0 + 50.0, ci.HEIGHT - 0.5
    for a, b in zip(gs, gs[1:]):                         # back to front: b is in front of a
        assert _solid(m, x, b.y1 + 0.2, z) and _solid(m, x, a.y0 - 0.2, z), "a ridge between tool grooves is too thin"
    front = gs[-1]
    assert _solid(m, x, front.y0 - 0.2, z) and _solid(m, x, front.y0 - ci.WALL + 0.2, z), "the wall to the strips pocket is too thin"
    assert not _solid(m, x, front.y0 - ci.WALL - 0.3, z), "the strips pocket starts too late"
