#!/usr/bin/env python3
"""Divider insert for the wooden tray in the credenza drawer.

The tray is 365.5 x 179.5 x 30 mm inside -- too long for the P2S bed -- so the
insert prints as two halves that sit side by side; the tray's own walls hold
them together. Front is -Y (the side nearest you with the drawer open).

  LEFT half   front: three channels -- pens, screwdrivers, the letter opener
              middle: AAA and AA, lying flat
              back: coin cup (scooped floor) and an open bin
  RIGHT half  right edge: one lane for both car key fobs, end to end
              badge + cards pocket (raised floor, finger dips), USB / SD bin;
              the wall between them lines up with the left half's

Outputs (next to this script):
  desk-drawer-tray-insert-left.stl / -right.stl        the halves
  desk-drawer-tray-insert-fit-test-left.stl / -right   3 mm floorless outlines
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
from trimesh_helpers import from_manifold, to_manifold  # noqa: E402

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
BADGE = (110.0, 70.0)               # badge in its holder, long x short
CARD = (85.6, 54.0)                 # ID-1 credit card; lies on top of the badge
FOB_BIG = (95.0, 55.0)
FOB_SMALL = (80.0, 50.0)
AA = (50.5, 14.5)                   # length, diameter
AAA = (44.5, 10.5)
LONGEST_TOOL = 165.0                # estimated from the photo: Wiha precision driver

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
PEN_CHANNEL = 28.0
BATTERY_BAY = 53.0                  # front to back; AA lie in it lengthwise
COIN_CUP_W = 70.0
COIN_SCOOP_R = 10.0                 # leaves a flat middle in the 33 mm cup so coins lie flat
FOB_LANE_W = 87.0
BADGE_POCKET_DEPTH = 12.0           # the badge sits on a raised floor this far down
FINGER_DIP_R = 14.0                 # reaches ~4 mm under the badge's long edges
FINGER_DIP_DEPTH = 8.0              # below the raised floor: a fingertip, not a well


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


def bays(side):
    """The openings of one half, in that half's own coordinates (front-left = 0,0)."""
    in_x0, in_x1 = WALL, HALF_W - WALL
    in_y0, in_y1 = WALL, INSERT_D - WALL
    if side == "left":
        mid = HALF_W / 2.0
        y = in_y0
        pens_front = Bay(in_x0, y, in_x1, y + PEN_CHANNEL)
        y = pens_front.y1 + WALL
        pens_middle = Bay(in_x0, y, in_x1, y + PEN_CHANNEL)
        y = pens_middle.y1 + WALL
        pens_back = Bay(in_x0, y, in_x1, y + PEN_CHANNEL)          # the letter opener
        y = pens_back.y1 + WALL
        aaa = Bay(in_x0, y, mid - WALL / 2, y + BATTERY_BAY)
        aa = Bay(mid + WALL / 2, y, in_x1, y + BATTERY_BAY)
        y = aa.y1 + WALL
        coins = Bay(in_x0, y, in_x0 + COIN_CUP_W, in_y1)
        open_bin = Bay(coins.x1 + WALL, y, in_x1, in_y1)
        return {"pens_front": pens_front, "pens_middle": pens_middle, "pens_back": pens_back,
                "aaa": aaa, "aa": aa, "coins": coins, "open_bin": open_bin}
    if side == "right":
        # the USB / badge wall lines up with the left half's wall behind the
        # second pen channel, so the two halves read as one grid
        split = bays("left")["pens_middle"].y1
        fobs = Bay(in_x1 - FOB_LANE_W, in_y0, in_x1, in_y1)
        usb = Bay(in_x0, in_y0, fobs.x0 - WALL, split)
        badge = Bay(in_x0, split + WALL, usb.x1, in_y1)
        return {"fobs": fobs, "badge": badge, "usb": usb}
    raise ValueError(f"side must be 'left' or 'right', not {side!r}")


def _block(height):
    c, w, d = CHAMFER, HALF_W, INSERT_D
    outline = Polygon([(c, 0), (w - c, 0), (w, c), (w, d - c), (w - c, d),
                       (c, d), (0, d - c), (0, c)])
    return trimesh.creation.extrude_polygon(outline, height)


def _prism(bay, z0, z1):
    return centered_box(bay.w, bay.d, z1 - z0, (bay.cx, bay.cy, (z0 + z1) / 2.0))


def _finger_dips(bay, z0, z1):
    """Half-discs cut into the raised floor at mid-length of both long sides."""
    inside = to_manifold(_prism(bay, z0, z1))
    dips = None
    for x in (bay.x0, bay.x1):
        post = trimesh.creation.cylinder(radius=FINGER_DIP_R, height=z1 - z0, sections=64)
        post.apply_translation([x, bay.cy, (z0 + z1) / 2.0])
        dip = to_manifold(post) ^ inside
        dips = dip if dips is None else dips + dip
    return dips


def build_half(side, fit_test=False):
    """One half as a watertight mesh. `fit_test` gives the 3 mm floorless outline."""
    height = FIT_TEST_H if fit_test else HEIGHT
    solid = to_manifold(_block(height))
    top = height + 1.0                                  # cut clean through the top
    for name, bay in bays(side).items():
        if fit_test:
            solid = solid - to_manifold(_prism(bay, -1.0, top))
        elif name == "coins":
            solid = solid - to_manifold(scooped_pocket(
                bay.w, bay.d, top - FLOOR, COIN_SCOOP_R, (bay.cx, bay.cy, FLOOR)))
        elif name == "badge":
            deck = HEIGHT - BADGE_POCKET_DEPTH
            solid = solid - to_manifold(_prism(bay, deck, top))
            solid = solid - _finger_dips(bay, deck - FINGER_DIP_DEPTH, top)
        else:
            solid = solid - to_manifold(_prism(bay, FLOOR, top))
    mesh = from_manifold(solid)
    mesh.merge_vertices()
    return mesh


def save_preview(path):
    """Top view of both halves as built, sliced just above the floor."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(14, 7.4))
    for i, side in enumerate(("left", "right")):
        mesh = build_half(side)
        section = mesh.section(plane_origin=[0, 0, FLOOR + 0.5], plane_normal=[0, 0, 1])
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
    plt.close(fig)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for side in ("left", "right"):
        for fit_test, suffix in ((False, ""), (True, "-fit-test")):
            mesh = build_half(side, fit_test=fit_test)
            out = os.path.join(here, f"desk-drawer-tray-insert{suffix}-{side}.stl")
            mesh.export(out)
            w, d, h = mesh.extents
            print(f"{os.path.basename(out)}: {w:.2f} x {d:.2f} x {h:.2f} mm, "
                  f"{mesh.volume / 1000:.0f} cm3")
    save_preview(os.path.join(here, "preview-layout.png"))


if __name__ == "__main__":
    main()
