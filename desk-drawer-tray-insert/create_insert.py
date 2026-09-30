#!/usr/bin/env python3
"""Divider insert for the wooden tray in the credenza drawer.

The tray is 365.5 x 179.5 x 30 mm inside -- too long for the P2S bed -- so the
insert prints as two halves that sit side by side; the tray's own walls hold
them together. Front is -Y (the side nearest you with the drawer open).

  LEFT half   front: a raised pen shelf -- one round groove each for a pen,
                     pencil, Sharpie and two screwdrivers, a bigger round groove for
                     the Slice pen cutter, each with a finger cup at its seam end
              back: 4 AA and 4 AAA in their own raised slots, and a coin cup
  RIGHT half  right edge: one lane for both car key fobs, standing upright end to end
              front to back: a card pocket (~16 cards, floor raised 4 mm), a tools
              bay (three tool grooves, an allen-key short-arm slot, a pocket for
              strips and Blu-Tack), then a keys bin and a USB-stick bin

Outputs (next to this script):
  desk-drawer-tray-insert-left.stl / -right.stl        the halves
  desk-drawer-tray-insert-fit-test-left.stl / -right   3 mm floorless outlines
  desk-drawer-tray-insert-groove-test.stl              one 100 mm groove of the pen shelf
  desk-drawer-tray-insert-width-test.stl               the front 1 inch of the right half, full height (also -trim-1.0/-1.5/-2.0)
  preview-layout.png                                   top view of both halves

Usage:  ../tools/venv/bin/python create_insert.py
"""
import os
import sys
from typing import NamedTuple

import trimesh
from shapely.geometry import Polygon

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
sys.path.insert(0, TOOLS)
from mesh_shapes import centered_box, scooped_pocket  # noqa: E402
from trimesh_helpers import drop_slivers, from_manifold, to_manifold  # noqa: E402

# ---------------------------------------------------------------------------
# The tray (measured inside) and how the insert sits in it (mm)
# ---------------------------------------------------------------------------
TRAY_W, TRAY_D, TRAY_H = 365.5, 179.5, 30.0
# Per side, against the MEASURED tray. Set by fit tests, not by the tape:
#   1st (CLEAR 0.5): ~1 mm loose all round.  2nd (CLEAR 0, cooled on the plate):
#   the pair had 1 mm of play side to side and 0.5 mm front to back -- so the
#   tray is that much bigger than measured, and the insert takes up all of it.
CLEAR_W = -0.5
CLEAR_D = -0.25
INSERT_W = TRAY_W - 2 * CLEAR_W     # 366.5
INSERT_D = TRAY_D - 2 * CLEAR_D     # 180.0
HALF_W = INSERT_W / 2.0             # 183.25 -- the even split; each half fits the 256 bed
RIGHT_TRIM = 1.0                    # the printed right half came out ~1 mm too wide for the tray
SPLIT_SHIFT = 0.0                   # how far the seam sits left of centre (0 = even halves)

HEIGHT = 22.0                       # low on purpose: the pen grooves' lowest point is 10 mm off the bottom
assert HEIGHT <= TRAY_H - 1.0       # and always 1 mm under the rim so the drawer closes
FLOOR = 1.2
WALL = 1.6
CHAMFER = 2.0                       # outer vertical corners; the tray's are "squarish"
FIT_TEST_H = 3.0

# ---------------------------------------------------------------------------
# What lives in it (measured by Richard, except where noted)
# ---------------------------------------------------------------------------
CARD = (89.0, 58.0)                 # the biggest card kept in the pocket (read off a photo)
CARD_STACK = 16.0                   # ~16 cards, embossed ones included
FOB_BIG = (95.0, 55.0)              # his numbers
FOB_SMALL = (80.0, 50.0)
AA = (50.5, 14.5)                   # length, diameter
AAA = (44.5, 10.5)
LONGEST_TOOL = 165.0                # estimated from the photo: Wiha precision driver
MAX_PEN_DIA = 16.0                  # assumed (Sharpie cap + clip); the groove strip checks it

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
GROOVE_W = 18.0                     # every groove the same: 0.25 mm a side around the 17.5 mm pen cutter
CUTTER_W = GROOVE_W                 # the pen cutter gets a groove like all the others
CUTTER_L, CUTTER_DIA = 133.5, 17.5  # length from the listing; 17.5 mm is the tapered body's measured maximum
RIDGE = 1.6                         # between grooves and between battery slots
GROOVE_DEPTH = 12.0                 # below the top: items stand proud so a fingertip can pinch them
CUTTER_SLOT_DEPTH = GROOVE_DEPTH
CUP_L = 22.0                        # finger cup at the seam end of every groove, past where the item stops
CUP_EXTRA = 6.0                     # below the groove bottom: a big fingertip, 4 mm of floor left
AA_SLOT = (53.0, 16.0)              # length, width
AAA_SLOT = (47.0, 12.0)
BATTERY_TROUGH_W = 16.0             # finger trough across the middle of the cells
COIN_SCOOP_R = 10.0                 # leaves a flat middle so coins lie flat
SCREWDRIVER_L = 98.0                # the small screwdrivers: ~91 mm by the photo, plus margin
ALLEN_LONG_ARM = 96.0               # measured
HEX_SHORT_ARM = 35.0                # the allen key: 96 mm long arm, 35 mm short arm
TOOLS_EXTRA = 18.5                   # the tools bay reaches this far past the pen shelf's back wall
TOOL_W, TOOL_DEPTH = 11.0, 8.0      # a round groove for each small tool (screwdrivers, hex key)
HEX_STRIP_W, HEX_SLOT_W = 16.0, 10.0 # the allen key's short arm lies in a slot along the bay's right end
TOOL_CUP_L, TOOL_CUP_EXTRA = 16.0, 6.0  # finger cup at the left end of each screwdriver groove
KEYS_W = 56.0                      # the 50 mm brass key and the 45 mm security key, lying lengthwise
FOB_LANE_W = 70.0                   # fobs stand upright: 55 wide plus 7.5 mm a side
CARD_POCKET_D = 62.0                # front to back: the 58 mm card plus 4
CARD_POCKET_DEPTH = 18.0            # the floor is raised only 4 mm, so the stack has room
WIDTH_TEST_D = 25.4                 # the width test is a 1 inch slice
STRIP_X0, STRIP_L = 6.0, 100.0      # the groove test strip, cut from the left half


class Bay(NamedTuple):
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def w(self):
        return self.x1 - self.x0

    @property
    def d(self):
        return self.y1 - self.y0

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2.0


def _slot_block_w(n, slot_w):
    return n * slot_w + (n - 1) * RIDGE


def half_w(side):
    """Width of one half: the seam is off-centre, so the right half is wider."""
    return HALF_W - SPLIT_SHIFT if side == "left" else HALF_W + SPLIT_SHIFT - RIGHT_TRIM


def bays(side):
    """The regions of one half, in that half's own coordinates (front-left = 0,0)."""
    in_x0, in_x1 = WALL, half_w(side) - WALL
    in_y0, in_y1 = WALL, INSERT_D - WALL
    shelf_y1 = in_y0 + 5 * (GROOVE_W + RIDGE) + CUTTER_W
    back_y0 = shelf_y1 + WALL
    if side == "left":
        pen_shelf = Bay(in_x0, in_y0, in_x1, shelf_y1)
        aa = Bay(in_x0, back_y0, in_x0 + _slot_block_w(4, AA_SLOT[1]), in_y1)
        aaa = Bay(aa.x1 + WALL, back_y0, aa.x1 + WALL + _slot_block_w(4, AAA_SLOT[1]), in_y1)
        coins = Bay(aaa.x1 + WALL, back_y0, in_x1, in_y1)
        return {"pen_shelf": pen_shelf, "aa": aa, "aaa": aaa, "coins": coins}
    if side == "right":
        fobs = Bay(in_x1 - FOB_LANE_W, in_y0, in_x1, in_y1)
        x1 = fobs.x0 - WALL
        cards = Bay(in_x0, in_y0, x1, in_y0 + CARD_POCKET_D)
        tools = Bay(in_x0, cards.y1 + WALL, x1, shelf_y1 + TOOLS_EXTRA)
        keys = Bay(in_x0, tools.y1 + WALL, in_x0 + KEYS_W, in_y1)
        open_bin = Bay(keys.x1 + WALL, tools.y1 + WALL, x1, in_y1)
        return {"cards": cards, "tools": tools, "keys": keys, "open_bin": open_bin, "fobs": fobs}
    raise ValueError(f"side must be 'left' or 'right', not {side!r}")


def grooves():
    """(name, Bay) for each groove on the left half's pen shelf, front to back."""
    shelf = bays("left")["pen_shelf"]
    out, y = [], shelf.y0
    for name in ("pen", "pencil", "sharpie", "screwdriver_1", "screwdriver_2"):
        out.append((name, Bay(shelf.x0, y, shelf.x1, y + GROOVE_W)))
        y += GROOVE_W + RIDGE
    out.append(("pen_cutter", Bay(shelf.x0, y, shelf.x1, y + CUTTER_W)))
    return out


def tool_grooves():
    """The three round tool grooves, at the back of the tools bay, each running the bay's width."""
    bay = bays("right")["tools"]
    out, y = [], bay.y1
    for _ in range(3):
        out.append(Bay(bay.x0, y - TOOL_W, bay.x1, y))
        y -= TOOL_W + RIDGE
    return out


def battery_slots(kind):
    """The four slots of the 'aa' or 'aaa' region; cells lie front to back."""
    length, width = {"aa": AA_SLOT, "aaa": AAA_SLOT}[kind]
    region = bays("left")[kind]
    y0 = region.cy - length / 2
    return [Bay(region.x0 + i * (width + RIDGE), y0, region.x0 + i * (width + RIDGE) + width,
                y0 + length) for i in range(4)]


def slot_depth(kind):
    """Deep enough that the cell lies just under the top."""
    return {"aa": AA, "aaa": AAA}[kind][1] + 1.0


def _block(height, side):
    c, w, d = CHAMFER, half_w(side), INSERT_D
    outline = Polygon([(c, 0), (w - c, 0), (w, c), (w, d - c), (w - c, d),
                       (c, d), (0, d - c), (0, c)])
    return trimesh.creation.extrude_polygon(outline, height)


def _prism(bay, z0, z1):
    return centered_box(bay.w, bay.d, z1 - z0, (bay.cx, bay.cy, (z0 + z1) / 2.0))


def _round_groove(bay, bottom, top, along="x"):
    """A half-pipe cutter over the bay: its short side is the diameter."""
    length, across = (bay.w, bay.d) if along == "x" else (bay.d, bay.w)
    return scooped_pocket(length, across, top - bottom, across / 2.0, (bay.cx, bay.cy, bottom),
                          along=along)


def _cutters(side, name, bay, top):
    """What to subtract for one region of the full-height half."""
    if name == "pen_shelf":
        bottom = HEIGHT - GROOVE_DEPTH
        cuts = [_round_groove(g, HEIGHT - (CUTTER_SLOT_DEPTH if n == "pen_cutter" else GROOVE_DEPTH), top)
                for n, g in grooves()]
        for n, g in grooves():
            cup = Bay(g.x1 - CUP_L, g.y0, g.x1, g.y1)
            cuts.append(_round_groove(cup, HEIGHT - (CUTTER_SLOT_DEPTH if n == "pen_cutter" else GROOVE_DEPTH)
                                      - CUP_EXTRA, top))
        return cuts
    if name in ("aa", "aaa"):
        bottom = HEIGHT - slot_depth(name)
        slots = battery_slots(name)
        cuts = [_round_groove(s, bottom, top, along="y") for s in slots]
        trough = Bay(slots[0].x0, bay.cy - BATTERY_TROUGH_W / 2, slots[-1].x1,
                     bay.cy + BATTERY_TROUGH_W / 2)
        return cuts + [_prism(trough, bottom - 3.0, top)]     # 3.5 mm of floor left
    if name == "coins":
        return [scooped_pocket(bay.w, bay.d, top - FLOOR, COIN_SCOOP_R, (bay.cx, bay.cy, FLOOR))]
    if name == "cards":
        deck = HEIGHT - CARD_POCKET_DEPTH
        return [_prism(bay, deck, top)]
    if name == "tools":
        grooves_ = tool_grooves()
        front = grooves_[-1]
        pocket = Bay(bay.x0, bay.y0, bay.x1 - HEX_STRIP_W - WALL, front.y0 - WALL)
        sx = bay.x1 - HEX_STRIP_W / 2.0
        slot = Bay(sx - HEX_SLOT_W / 2.0, bay.y0, sx + HEX_SLOT_W / 2.0, front.cy)
        cups = [_round_groove(Bay(g.x0, g.y0, g.x0 + TOOL_CUP_L, g.y1), HEIGHT - TOOL_DEPTH - TOOL_CUP_EXTRA, top)
                for g in grooves_[:2]]
        return ([_round_groove(g, HEIGHT - TOOL_DEPTH, top) for g in grooves_] + cups + [_prism(pocket, FLOOR, top)]
                + [_round_groove(slot, HEIGHT - TOOL_DEPTH, top, along="y")])
    return [_prism(bay, FLOOR, top)]


def build_half(side, fit_test=False):
    """One half as a watertight mesh. `fit_test` gives the 3 mm floorless outline."""
    height = FIT_TEST_H if fit_test else HEIGHT
    solid = to_manifold(_block(height, side))
    top = height + 1.0                                  # cut clean through the top
    for name, bay in bays(side).items():
        if fit_test:
            solid = solid - to_manifold(_prism(bay, -1.0, top))
            continue
        for cut in _cutters(side, name, bay, top):
            solid = solid - (cut if not isinstance(cut, trimesh.Trimesh) else to_manifold(cut))
    return drop_slivers(from_manifold(solid))


def build_groove_strip():
    """One 100 mm groove of the pen shelf; every round groove is the same, so it tries every item."""
    depth = grooves()[0][1].y1 + RIDGE
    keep = centered_box(STRIP_L, depth, HEIGHT + 2,
                        (STRIP_X0 + STRIP_L / 2, depth / 2, HEIGHT / 2))
    mesh = from_manifold(to_manifold(build_half("left")) ^ to_manifold(keep))
    mesh.merge_vertices()
    return mesh


def build_width_test():
    """The front WIDTH_TEST_D mm (1 inch) of the real right half: full height and width, real interior."""
    keep = centered_box(half_w("right") + 2, WIDTH_TEST_D, HEIGHT + 2,
                        (half_w("right") / 2, WIDTH_TEST_D / 2, HEIGHT / 2))
    mesh = from_manifold(to_manifold(build_half("right")) ^ to_manifold(keep))
    mesh.merge_vertices()
    return mesh


def build_width_ladder(trims=(1.0, 1.5, 2.0)):
    """The width test at several trims, to find the width that drops in smoothly."""
    global RIGHT_TRIM
    saved, out = RIGHT_TRIM, []
    try:
        for t in trims:
            RIGHT_TRIM = t
            out.append(("trim-%.1f" % t, build_width_test()))
    finally:
        RIGHT_TRIM = saved
    return out


def save_preview(path):
    """Top view of both halves as built, sliced 3 mm under the top."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(14, 7.4))
    for i, side in enumerate(("left", "right")):
        mesh = build_half(side)
        section = mesh.section(plane_origin=[0, 0, HEIGHT - 3.0], plane_normal=[0, 0, 1])
        planar, to_3d = section.to_2D()
        for line in planar.discrete:
            pts = trimesh.transform_points(
                trimesh.util.stack_3D(line), to_3d)[:, :2]
            ax.plot(pts[:, 0] + i * half_w("left"), pts[:, 1], color="#5b4f3a", lw=1)
        for name, bay in bays(side).items():
            ax.text(bay.cx + i * half_w("left"), bay.cy, name.replace("_", " "),
                    ha="center", va="center", fontsize=10)
    ax.text(INSERT_W / 2, -8, "FRONT", ha="center", fontsize=11, weight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, dpi=110, bbox_inches="tight", facecolor="white")
    drawn_width = ax.dataLim.width                      # how far across the outlines reach
    plt.close(fig)
    return drawn_width


def main(here=None):
    here = here or os.path.dirname(os.path.abspath(__file__))
    for side in ("left", "right"):
        for fit_test, suffix in ((False, ""), (True, "-fit-test")):
            mesh = build_half(side, fit_test=fit_test)
            out = os.path.join(here, f"desk-drawer-tray-insert{suffix}-{side}.stl")
            mesh.export(out)
            w, d, h = mesh.extents
            print(f"{os.path.basename(out)}: {w:.2f} x {d:.2f} x {h:.2f} mm, "
                  f"{mesh.volume / 1000:.0f} cm3")
    strip = build_groove_strip()
    strip.export(os.path.join(here, "desk-drawer-tray-insert-groove-test.stl"))
    print("desk-drawer-tray-insert-groove-test.stl: %.2f x %.2f x %.2f mm" % tuple(strip.extents))
    for name, m in build_width_ladder():
        m.export(os.path.join(here, "desk-drawer-tray-insert-width-test-%s.stl" % name))
        print("width test %s: %.2f mm wide" % (name, m.extents[0]))
    wt = build_width_test()
    wt.export(os.path.join(here, "desk-drawer-tray-insert-width-test.stl"))
    print("desk-drawer-tray-insert-width-test.stl: %.2f x %.2f x %.2f mm" % tuple(wt.extents))
    save_preview(os.path.join(here, "preview-layout.png"))


if __name__ == "__main__":
    main()
