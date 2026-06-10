#!/usr/bin/env python3
"""Carrier/sled generator for the garage-street-bt-proxy-poe BLE proxy.

Holds an Olimex ESP32-POE-ISO-EA (Rev M) board vertically inside a length of
1.5" Schedule-40 PVC *electrical* conduit, with a refillable desiccant basket
on top. See README.md for the full enclosure design and assembly notes.

Tube axis = +Z (the conduit stands vertical in service):
  - Board mounts vertical: RJ45/cable end DOWN, U.FL antenna end UP.
  - N perforated centering discs on a back spine grip the PCB *above* the
    RJ45; the RJ45 + plug + cable bend region stays open below (not modeled).
  - A perforated desiccant basket (cup + friction lid) sits at the top.
  - Axial flow holes through every disc keep drainage/airflow open top->bottom
    so the tube breathes and sheds condensation out the bottom grommet.

Outputs (next to this script):
  garage-street-bt-proxy-carrier.stl      the sled + basket   (print 1)
  garage-street-bt-proxy-basket-lid.stl   the friction lid    (print 2)

Print: PETG or ASA (NOT PLA -- a capped conduit in sun softens PLA). Vertical,
as modeled (Z up); every feature is support-free in that orientation. Use a
brim (tall part, small footprint).

Usage:  ../tools/venv/bin/python create_carrier.py
"""
import math
import os
import sys

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
sys.path.insert(0, TOOLS)
from step_primitives import cut, fuse, make_box, make_cylinder, save_stl  # noqa: E402
from bbox import print_dimensions  # noqa: E402

# ---------------------------------------------------------------------------
# Parameters (mm). Cited values are verified; tune the *_CLEAR values to your
# printer after a test print.
# ---------------------------------------------------------------------------
# Conduit & slip fit
CONDUIT_ID = 40.9            # 1.5" Sch-40 PVC ID (OD 1.900", wall 0.145" -> ID 1.610")
FIT_CLEAR = 1.0             # diametral clearance; carrier OD = CONDUIT_ID - FIT_CLEAR
CARRIER_R = (CONDUIT_ID - FIT_CLEAR) / 2.0   # ~19.95

# Board (Olimex ESP32-POE-ISO-EA Rev M; verified vs Olimex Rev J+ drawing)
BOARD_W = 28.0
BOARD_T = 1.6
BOARD_L = 98.15
SLOT_CLEAR = 0.4            # per side, board <-> disc slot (FDM tolerance)

# Layout along Z
BOTTOM_OVERHANG = 26.0       # board length hanging below the carrier (RJ45 + plug clearance); NOT modeled
GRIP_LEN = BOARD_L - BOTTOM_OVERHANG          # carrier grips this much of the upper board (~72)
DISC_T = 4.0
N_DISCS = 3
SPINE_W = 8.0               # spine width (X)
SPINE_BACK_Y = -12.0        # spine reaches from the slot back toward the -Y wall to here

# Desiccant basket (top)
BASKET_H = 30.0
BASKET_WALL = 2.5
BASKET_FLOOR = 2.5
PERF_D = 1.5               # perforation dia -- MUST be < your smallest silica-gel bead
PERF_RING_R = 12.0
PERF_COUNT = 6

# Flow / drain holes through each disc
FLOW_D = 4.0
FLOW_R = 15.5
FLOW_ANGLES = [45, 135, 225, 315]

# Friction lid
LID_CLEAR = 0.3            # radial, lid plug <-> cup bore
LID_PLUG_H = 6.0
LID_TOP_T = 2.0
LID_PULL_D = 7.0           # center pull-hole (doubles as airflow)

# Antenna channel: vertical notch in the basket wall, street-facing (+X) side,
# so the U.FL antenna can run up the wall to the very top if desired.
ANTENNA_CHANNEL = True
ANT_W = 6.0
ANT_DEPTH = 2.0

CARRIER_H = GRIP_LEN + BASKET_H


def _disc_centers():
    if N_DISCS == 1:
        return [GRIP_LEN / 2.0]
    step = (GRIP_LEN - DISC_T) / (N_DISCS - 1)
    return [DISC_T / 2.0 + i * step for i in range(N_DISCS)]


def _disc(z_center):
    return make_cylinder(CARRIER_R, DISC_T, z=z_center - DISC_T / 2.0)


def _spine():
    """Back-side bar (-Y) tying all discs together; stays inside the bore."""
    y0 = SPINE_BACK_Y
    # Stop 0.01 short of the slot's back face: avoids a coincident cut plane
    # (robust across OCCT versions) and keeps the spine clear of board space.
    # Disc overlap still ties all discs + basket into one body.
    y1 = -(BOARD_T / 2.0 + SLOT_CLEAR) - 0.01
    return make_box(-SPINE_W / 2.0, y0, 0.0, SPINE_W, y1 - y0, GRIP_LEN)


def _slot_box():
    """Board through-slot: a tall box on the axis the PCB slides down into."""
    w = BOARD_W + 2 * SLOT_CLEAR
    t = BOARD_T + 2 * SLOT_CLEAR
    return make_box(-w / 2.0, -t / 2.0, 0.0, w, t, GRIP_LEN + 0.01)


def _flow_holes(z_center):
    holes = None
    for a in FLOW_ANGLES:
        x = FLOW_R * math.cos(math.radians(a))
        y = FLOW_R * math.sin(math.radians(a))
        h = make_cylinder(FLOW_D / 2.0, DISC_T + 0.02, x=x, y=y, z=z_center - DISC_T / 2.0 - 0.01)
        holes = h if holes is None else fuse(holes, h)
    return holes


def _basket():
    z0 = GRIP_LEN
    outer = make_cylinder(CARRIER_R, BASKET_H, z=z0)
    cavity = make_cylinder(CARRIER_R - BASKET_WALL, BASKET_H - BASKET_FLOOR + 0.01, z=z0 + BASKET_FLOOR)
    return cut(outer, cavity)


def _perf_ring(z_base, thickness, with_center=True):
    """Vertical holes in a ring (+ optional center) for floor / lid airflow."""
    holes = None
    for i in range(PERF_COUNT):
        a = 2 * math.pi * i / PERF_COUNT
        x = PERF_RING_R * math.cos(a)
        y = PERF_RING_R * math.sin(a)
        h = make_cylinder(PERF_D / 2.0, thickness + 0.02, x=x, y=y, z=z_base - 0.01)
        holes = h if holes is None else fuse(holes, h)
    if with_center:
        holes = fuse(holes, make_cylinder(PERF_D / 2.0, thickness + 0.02, z=z_base - 0.01))
    return holes


def _antenna_channel():
    z0 = GRIP_LEN
    return make_box(CARRIER_R - ANT_DEPTH, -ANT_W / 2.0, z0 - 0.01, ANT_DEPTH + 1.0, ANT_W, BASKET_H + 0.02)


def build_carrier():
    disc_zs = _disc_centers()
    solid = _spine()
    for z in disc_zs:
        solid = fuse(solid, _disc(z))
    solid = fuse(solid, _basket())

    solid = cut(solid, _slot_box())
    for z in disc_zs:
        solid = cut(solid, _flow_holes(z))
    solid = cut(solid, _perf_ring(GRIP_LEN, BASKET_FLOOR))     # basket floor perforations
    if ANTENNA_CHANNEL:
        solid = cut(solid, _antenna_channel())
    return solid


def build_lid():
    bore_r = CARRIER_R - BASKET_WALL
    top = make_cylinder(CARRIER_R, LID_TOP_T)
    plug = make_cylinder(bore_r - LID_CLEAR, LID_PLUG_H, z=LID_TOP_T)
    lid = fuse(top, plug)
    lid = cut(lid, _perf_ring(0.0, LID_TOP_T + LID_PLUG_H, with_center=False))
    lid = cut(lid, make_cylinder(LID_PULL_D / 2.0, LID_TOP_T + LID_PLUG_H + 0.02, z=-0.01))   # center pull
    return lid


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print("garage-street-bt-proxy carrier generator")
    print(f"  conduit ID:  {CONDUIT_ID} mm (1.5\" Sch-40)")
    print(f"  carrier OD:  {2 * CARRIER_R:.1f} mm  (fit clearance {FIT_CLEAR} mm)")
    print(f"  grip length: {GRIP_LEN:.1f} mm over {N_DISCS} discs")
    print(f"  basket:      {BASKET_H} mm, perf {PERF_D} mm (set < your bead size!)")
    print("=" * 48)

    print("\n--- carrier (sled + basket) ---")
    carrier = build_carrier()
    print_dimensions(carrier)
    carrier_path = os.path.join(script_dir, "garage-street-bt-proxy-carrier.stl")
    save_stl(carrier, carrier_path)
    print(f"  Saved: {carrier_path}")

    print("\n--- basket lid ---")
    lid = build_lid()
    print_dimensions(lid)
    lid_path = os.path.join(script_dir, "garage-street-bt-proxy-basket-lid.stl")
    save_stl(lid, lid_path)
    print(f"  Saved: {lid_path}")

    print("\nDone. Print vertical (Z up) in PETG/ASA, brim on. No supports.")


if __name__ == "__main__":
    main()
