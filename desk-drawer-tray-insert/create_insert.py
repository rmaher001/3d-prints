#!/usr/bin/env python3
"""Divider insert for the wooden tray in the credenza drawer.

The tray is 365.5 x 179.5 x 30 mm inside -- too long for the P2S bed -- so the
insert prints as two halves that sit side by side; the tray's own walls hold
them together. Front is -Y (the side nearest you with the drawer open).

  LEFT half   front: a raised pen shelf -- one round groove each for a pen,
                     pencil, Sharpie and two screwdrivers, a flat letter-opener
                     slot, and a finger trough across the middle
              back: 4 AA and 4 AAA in their own raised slots, and a coin cup
  RIGHT half  right edge: one lane for both car key fobs, end to end
              front to back: a raised card pocket (~10 cards), a USB / SD
              bin, an open bin; the bins' wall lines up with the pen shelf

Outputs (next to this script):
  desk-drawer-tray-insert-left.stl / -right.stl        the halves
  desk-drawer-tray-insert-fit-test-left.stl / -right   3 mm floorless outlines
  desk-drawer-tray-insert-groove-test.stl              a 25 mm slice of the pen shelf
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
HALF_W = INSERT_W / 2.0             # 183.25 -- each half fits the 256 bed
HEIGHT = TRAY_H - 1.0               # stop 1 mm under the rim so the drawer closes
FLOOR = 1.2
WALL = 1.6
CHAMFER = 2.0                       # outer vertical corners; the tray's are "squarish"
FIT_TEST_H = 3.0

# ---------------------------------------------------------------------------
# What lives in it (measured by Richard, except where noted)
# ---------------------------------------------------------------------------
CARD = (85.6, 54.0)                 # ID-1 card: health insurance card and the like
CARD_STACK = 10.0                   # ~10 cards, embossed ones included
FOB_BIG = (95.0, 55.0)
FOB_SMALL = (80.0, 50.0)
AA = (50.5, 14.5)                   # length, diameter
AAA = (44.5, 10.5)
LONGEST_TOOL = 165.0                # estimated from the photo: Wiha precision driver
MAX_PEN_DIA = 16.0                  # assumed (Sharpie cap + clip); the groove strip checks it

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
GROOVE_W = 17.0                     # round-bottom groove, one item each
OPENER_W = 24.0                     # flat slot for a slim letter opener
RIDGE = 1.6                         # between grooves and between battery slots
GROOVE_DEPTH = 16.0                 # below the top: a 16 mm item lies flush
TROUGH_W = 25.0                     # finger trough across the middle of the grooves
TROUGH_DEPTH = 6.0                  # below the groove bottoms
AA_SLOT = (53.0, 16.0)              # length, width
AAA_SLOT = (47.0, 12.0)
BATTERY_TROUGH_W = 16.0             # finger trough across the middle of the cells
COIN_SCOOP_R = 10.0                 # leaves a flat middle so coins lie flat
FOB_LANE_W = 87.0
CARD_POCKET_D = 60.0                # front to back
CARD_POCKET_DEPTH = 14.0            # the cards sit on a raised floor this far down
FINGER_DIP_R = 12.0                 # reaches ~9 mm under each end of the stack
FINGER_DIP_DEPTH = 8.0              # below the raised floor: a fingertip, not a well
STRIP_X0, STRIP_L = 6.0, 25.0       # the groove test strip, cut from the left half


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


def bays(side):
    """The regions of one half, in that half's own coordinates (front-left = 0,0)."""
    in_x0, in_x1 = WALL, HALF_W - WALL
    in_y0, in_y1 = WALL, INSERT_D - WALL
    shelf_y1 = in_y0 + 5 * (GROOVE_W + RIDGE) + OPENER_W
    back_y0 = shelf_y1 + WALL
    if side == "left":
        pen_shelf = Bay(in_x0, in_y0, in_x1, shelf_y1)
        aa = Bay(in_x0, back_y0, in_x0 + _slot_block_w(4, AA_SLOT[1]), in_y1)
        aaa = Bay(aa.x1 + WALL, back_y0, aa.x1 + WALL + _slot_block_w(4, AAA_SLOT[1]), in_y1)
        coins = Bay(aaa.x1 + WALL, back_y0, in_x1, in_y1)
        return {"pen_shelf": pen_shelf, "aa": aa, "aaa": aaa, "coins": coins}
    if side == "right":
        # the USB / open-bin wall lines up with the left half's pen-shelf wall
        fobs = Bay(in_x1 - FOB_LANE_W, in_y0, in_x1, in_y1)
        x1 = fobs.x0 - WALL
        cards = Bay(in_x0, in_y0, x1, in_y0 + CARD_POCKET_D)
        usb = Bay(in_x0, cards.y1 + WALL, x1, shelf_y1)
        open_bin = Bay(in_x0, back_y0, x1, in_y1)
        return {"cards": cards, "usb": usb, "open_bin": open_bin, "fobs": fobs}
    raise ValueError(f"side must be 'left' or 'right', not {side!r}")


def grooves():
    """(name, Bay) for each groove on the left half's pen shelf, front to back."""
    shelf = bays("left")["pen_shelf"]
    out, y = [], shelf.y0
    for name in ("pen", "pencil", "sharpie", "screwdriver_1", "screwdriver_2"):
        out.append((name, Bay(shelf.x0, y, shelf.x1, y + GROOVE_W)))
        y += GROOVE_W + RIDGE
    out.append(("letter_opener", Bay(shelf.x0, y, shelf.x1, y + OPENER_W)))
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


def _block(height):
    c, w, d = CHAMFER, HALF_W, INSERT_D
    outline = Polygon([(c, 0), (w - c, 0), (w, c), (w, d - c), (w - c, d),
                       (c, d), (0, d - c), (0, c)])
    return trimesh.creation.extrude_polygon(outline, height)


def _prism(bay, z0, z1):
    return centered_box(bay.w, bay.d, z1 - z0, (bay.cx, bay.cy, (z0 + z1) / 2.0))


def _finger_dips(bay, z0, z1):
    """Half-discs at mid-depth of both short ends, inside the pocket's footprint."""
    inside = to_manifold(_prism(bay, z0, z1))
    dips = None
    for x in (bay.x0, bay.x1):
        post = trimesh.creation.cylinder(radius=FINGER_DIP_R, height=z1 - z0, sections=64)
        post.apply_translation([x, bay.cy, (z0 + z1) / 2.0])
        dip = to_manifold(post) ^ inside
        dips = dip if dips is None else dips + dip
    return dips


def _round_groove(bay, bottom, top, along="x"):
    """A half-pipe cutter over the bay: its short side is the diameter."""
    length, across = (bay.w, bay.d) if along == "x" else (bay.d, bay.w)
    return scooped_pocket(length, across, top - bottom, across / 2.0, (bay.cx, bay.cy, bottom),
                          along=along)


def _cutters(side, name, bay, top):
    """What to subtract for one region of the full-height half."""
    if name == "pen_shelf":
        bottom = HEIGHT - GROOVE_DEPTH
        cuts = [_round_groove(g, bottom, top) if n != "letter_opener" else _prism(g, bottom, top)
                for n, g in grooves()]
        trough = Bay(bay.cx - TROUGH_W / 2, bay.y0, bay.cx + TROUGH_W / 2, bay.y1)
        return cuts + [_prism(trough, bottom - TROUGH_DEPTH, top)]
    if name in ("aa", "aaa"):
        bottom = HEIGHT - slot_depth(name)
        slots = battery_slots(name)
        cuts = [_round_groove(s, bottom, top, along="y") for s in slots]
        trough = Bay(slots[0].x0, bay.cy - BATTERY_TROUGH_W / 2, slots[-1].x1,
                     bay.cy + BATTERY_TROUGH_W / 2)
        return cuts + [_prism(trough, bottom - 5.0, top)]
    if name == "coins":
        return [scooped_pocket(bay.w, bay.d, top - FLOOR, COIN_SCOOP_R, (bay.cx, bay.cy, FLOOR))]
    if name == "cards":
        deck = HEIGHT - CARD_POCKET_DEPTH
        return [_prism(bay, deck, top), _finger_dips(bay, deck - FINGER_DIP_DEPTH, top)]
    return [_prism(bay, FLOOR, top)]


def build_half(side, fit_test=False):
    """One half as a watertight mesh. `fit_test` gives the 3 mm floorless outline."""
    height = FIT_TEST_H if fit_test else HEIGHT
    solid = to_manifold(_block(height))
    top = height + 1.0                                  # cut clean through the top
    for name, bay in bays(side).items():
        if fit_test:
            solid = solid - to_manifold(_prism(bay, -1.0, top))
            continue
        for cut in _cutters(side, name, bay, top):
            solid = solid - (cut if not isinstance(cut, trimesh.Trimesh) else to_manifold(cut))
    return drop_slivers(from_manifold(solid))


def build_groove_strip():
    """A 25 mm slice across the pen shelf, to try every pen and screwdriver."""
    shelf = bays("left")["pen_shelf"]
    keep = centered_box(STRIP_L, shelf.y1 + WALL, HEIGHT + 2,
                        (STRIP_X0 + STRIP_L / 2, (shelf.y1 + WALL) / 2, HEIGHT / 2))
    mesh = from_manifold(to_manifold(build_half("left")) ^ to_manifold(keep))
    mesh.merge_vertices()
    return mesh


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
            ax.plot(pts[:, 0] + i * HALF_W, pts[:, 1], color="#5b4f3a", lw=1)
        for name, bay in bays(side).items():
            ax.text(bay.cx + i * HALF_W, bay.cy, name.replace("_", " "),
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
    save_preview(os.path.join(here, "preview-layout.png"))


if __name__ == "__main__":
    main()
