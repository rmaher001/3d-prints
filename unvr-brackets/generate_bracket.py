"""Generate UNVR anti-tip bracket STL.

Z-step bracket that hooks over the UNVR top edge.
Back plate velcros to wood panel; front lip prevents tipping.

Side-view profile:
        ┌─┐
        │ │  Back plate (velcro to wood)
        │ │
   ┌────┘ │
   │      │  Shelf (spans UNVR top edge)
   │ ┌────┘
   │ │
   │ │       Front lip (prevents tipping)
   └─┘

Coordinate system (mounting orientation):
  X: width (centered at 0)
  Y: depth (0 = wood panel, +Y = toward front)
  Z: height (0 = bottom of front lip)
"""

import sys
from pathlib import Path

sys.path.insert(0, "/Users/richard/3d-prints/tools")
from mesh_primitives import make_box, combine


# ── Dimensions ───────────────────────────────────────────────

WIDTH = 50.0          # along UNVR length (X)
WALL = 4.0            # wall thickness
BACK_H = 50.0         # back plate height
FRONT_H = 50.0        # front lip height
CHANNEL = 50.0        # inner channel depth
TOTAL_DEPTH = WALL + CHANNEL + WALL  # 58mm
TOTAL_HEIGHT = FRONT_H + WALL + BACK_H  # 104mm

# Derived Y positions (0 = wood panel side)
BACK_Y = WALL / 2                           # back plate center Y
SHELF_Y = TOTAL_DEPTH / 2                   # shelf center Y
FRONT_Y = TOTAL_DEPTH - WALL / 2            # front lip center Y

# Derived Z positions (0 = bottom of front lip)
FRONT_Z = 0.0
SHELF_Z = FRONT_H                           # bottom of shelf
BACK_Z = FRONT_H + WALL                     # bottom of back plate


# ── Build meshes ─────────────────────────────────────────────

parts = []

# 1. Back plate: against wood panel, upper portion
parts.append(make_box(WIDTH, WALL, BACK_H, cx=0, cy=BACK_Y, cz=BACK_Z))

# 2. Shelf: horizontal, spans full depth
parts.append(make_box(WIDTH, TOTAL_DEPTH, WALL, cx=0, cy=SHELF_Y, cz=SHELF_Z))

# 3. Front lip: front side, lower portion
parts.append(make_box(WIDTH, WALL, FRONT_H, cx=0, cy=FRONT_Y, cz=FRONT_Z))


# ── Combine and save ─────────────────────────────────────────

bracket = combine(parts)
out_path = Path(__file__).parent / "unvr_anti_tip_bracket.stl"
bracket.save(str(out_path))

# ── Verify dimensions ────────────────────────────────────────

mins = bracket.vectors.reshape(-1, 3).min(axis=0)
maxs = bracket.vectors.reshape(-1, 3).max(axis=0)
dims = maxs - mins

print(f"Saved: {out_path}")
print(f"Bounding box:")
print(f"  X (width):  {dims[0]:.1f}mm  (spec: {WIDTH}mm)")
print(f"  Y (depth):  {dims[1]:.1f}mm  (spec: {TOTAL_DEPTH}mm)")
print(f"  Z (height): {dims[2]:.1f}mm  (spec: {TOTAL_HEIGHT}mm)")
print(f"  Channel:    {CHANNEL:.1f}mm")
print(f"\nPrint recommendation:")
print(f"  Lay on 100mm side face for zero overhangs and strong layer bonding.")
print(f"  Print 2-3 brackets, spaced along the UNVR top edge.")
