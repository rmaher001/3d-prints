#!/usr/bin/env python3
"""
ESP32-C6 + C4001 Enclosure — Clean Rebuild

Target design:
  • Two halves (BASE + LID), matched width 37mm
  • ESP32 groove 33mm long (fits 30mm ESP32-C6 with clearance)
  • Floor deepened 2mm for more wire room
  • USB-C cutout top lowered to align with connector after deepen
  • 4 identical standoffs on BASE floor: plain cylinders, R=3.85, Z=0-2 (2mm tall)
    with M3 clearance hole R=1.5

Input:  ~/Downloads/esp32-s3-c4001-enclosure.stl
Output: esp32-c6-c4001-enclosure.v3.stl
"""

import os
import numpy as np
import trimesh
import manifold3d as m3d


SOURCE_STL = os.path.expanduser("~/Downloads/esp32-s3-c4001-enclosure.stl")

# --- Geometry constants ---
EXTENSION = 3.0                 # width/groove extension
LOW_X_CUT = 110.0               # inside LOW-X piece — both standoffs stay, end shifts
HIGH_X_SHIFT_BOUND = 128.0      # boundary between LOW-X and HIGH-X pieces
HIGH_X_GROOVE_CUT = 155.0       # past the USB-C cutout (X=140-152) so the cutout stays its original width

GROOVE_DEEPEN = 2.0
HEIGHT_ADD = 3.0
FLOOR_Z = 2.0
FLOOR_BLEND = 0.5
TOP_Z = 7.5
TOP_BLEND = 0.5

STAND_R_OUT = 3.85
STAND_R_IN = 0.75      # match source's small pilot hole (~1.5mm dia)
STAND_Z_LOW = 0.0
STAND_HEIGHT = 2.0

# Source standoff centers (in LOW-X piece). X=120.855 shifts to 123.855 with the stretch.
SRC_STAND_1 = (99.145, 114.9)
SRC_STAND_2 = (123.855, 114.9)   # post-stretch position
MIRROR_Y = 141.1                  # mirror across cavity center Y=128


def to_manifold(mesh, tolerance=0.01):
    verts = np.ascontiguousarray(mesh.vertices.astype(np.float32))
    faces = np.ascontiguousarray(mesh.faces.astype(np.uint32))
    return m3d.Manifold(m3d.Mesh(vert_properties=verts, tri_verts=faces, tolerance=tolerance))


def from_manifold(mani):
    mesh = mani.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties[:, :3]),
                           faces=np.asarray(mesh.tri_verts))


def stretch_x(mesh, ext):
    """Both halves grow by ext. HIGH-X piece also has its far wall shifted extra
    so the ESP32 groove interior lengthens by ext (from 30mm to 30+ext mm)."""
    v = mesh.vertices.copy()
    orig = v[:, 0]
    low_mask = (orig <= HIGH_X_SHIFT_BOUND) & (orig > LOW_X_CUT)
    high_mask = orig >= HIGH_X_SHIFT_BOUND
    groove_mask = orig > HIGH_X_GROOVE_CUT
    v[low_mask, 0] += ext
    v[high_mask, 0] += ext
    v[groove_mask, 0] += ext
    return trimesh.Trimesh(vertices=v, faces=mesh.faces)


def deepen_floor_and_raise_top(mesh, deepen, raise_top):
    """Z<=FLOOR_Z shifts down; Z>=TOP_Z+TOP_BLEND shifts up. Smooth blends at edges."""
    v = mesh.vertices.copy()
    z = v[:, 2]
    offset = np.zeros_like(z)
    offset[z <= FLOOR_Z] = -deepen
    bl = (z > FLOOR_Z) & (z < FLOOR_Z + FLOOR_BLEND)
    offset[bl] = -deepen * (1.0 - (z[bl] - FLOOR_Z) / FLOOR_BLEND)
    offset[z >= TOP_Z + TOP_BLEND] = raise_top
    bh = (z > TOP_Z) & (z < TOP_Z + TOP_BLEND)
    offset[bh] = raise_top * ((z[bh] - TOP_Z) / TOP_BLEND)
    v[:, 2] += offset
    return trimesh.Trimesh(vertices=v, faces=mesh.faces)


def lower_usbc_cutout(mesh, drop):
    """Lower only the 2 top corners of the USB-C cutout at X=93."""
    v = mesh.vertices.copy()
    mask = ((v[:, 0] <= 95.25) & (v[:, 1] > 110.5) & (v[:, 1] < 145.5)
            & (v[:, 2] > 6.9) & (v[:, 2] < 7.1))
    v[mask, 2] -= drop
    return trimesh.Trimesh(vertices=v, faces=mesh.faces)


def make_standoff(x, y):
    """Plain cylindrical standoff with a through-hole that pierces the floor too."""
    outer = m3d.Manifold.cylinder(height=STAND_HEIGHT, radius_low=STAND_R_OUT,
                                   radius_high=STAND_R_OUT, circular_segments=32).translate([x, y, STAND_Z_LOW])
    # Inner pin extends from below floor (Z=-3) up through the standoff (Z=2) — 5mm tall
    inner = m3d.Manifold.cylinder(height=5.0, radius_low=STAND_R_IN,
                                   radius_high=STAND_R_IN, circular_segments=32).translate([x, y, -3.0])
    return outer, inner


def chop_source_standoff(mani, x, y):
    """Remove the source standoff above Z=2. R=4.0 is wider than the 3.85 body
    but narrower than the 4.145mm distance to the nearest wall (inner X=95)."""
    chopper = m3d.Manifold.cylinder(height=10.0, radius_low=4.0, radius_high=4.0,
                                     circular_segments=32)
    return mani - chopper.translate([x, y, 2.01])


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print("ESP32-C6 C4001 Enclosure — v3 clean rebuild")
    print("=" * 48)

    mesh = trimesh.load(SOURCE_STL)
    print(f"Source: {mesh.extents[0]:.1f} x {mesh.extents[1]:.1f} x {mesh.extents[2]:.1f} mm")

    # 1. Stretch X — both pieces grow by EXTENSION; groove also grows by EXTENSION
    mesh = stretch_x(mesh, EXTENSION)
    for c in mesh.split(only_watertight=False):
        print(f"  piece X:{c.bounds[0][0]:.1f}-{c.bounds[1][0]:.1f} ({c.extents[0]:.1f}mm)")

    # 2. Deepen floor, raise top
    mesh = deepen_floor_and_raise_top(mesh, GROOVE_DEEPEN, HEIGHT_ADD)
    print(f"Z: floor -{GROOVE_DEEPEN}mm, top +{HEIGHT_ADD}mm")

    # 3. Lower USB-C cutout top to align with deepened connector position
    mesh = lower_usbc_cutout(mesh, GROOVE_DEEPEN)
    print(f"USB-C cutout top: -{GROOVE_DEEPEN}mm")

    # 4. Split into pieces
    parts = list(mesh.split(only_watertight=False))
    low_idx = min(range(len(parts)), key=lambda i: parts[i].bounds[0][0])
    high_idx = 1 - low_idx

    # 4a. Create a single clean ESP32 groove by filling the entire original cavity
    # then subtracting one 29x18.5mm pocket. This avoids the "box inside a box"
    # appearance that adding rails caused.
    ESP_L = 29.0
    ESP_W = 18.5
    ESP_X_CENTER = 150.5
    ESP_Y_CENTER = 128.0
    gx0, gx1 = ESP_X_CENTER - ESP_W/2, ESP_X_CENTER + ESP_W/2   # 141.25, 159.75
    gy0, gy1 = ESP_Y_CENTER - ESP_L/2, ESP_Y_CENTER + ESP_L/2   # 113.5, 142.5

    # Use actual HIGH-X piece bounds to determine safe filler region.
    # The filler must cover the entire interior cavity without protruding
    # past the outer walls.
    hb = parts[high_idx].bounds  # [[xmin,ymin,zmin],[xmax,ymax,zmax]]
    print(f"HIGH-X bounds: X={hb[0][0]:.1f}-{hb[1][0]:.1f}, Y={hb[0][1]:.1f}-{hb[1][1]:.1f}, Z={hb[0][2]:.1f}-{hb[1][2]:.1f}")

    # Inset filler by wall thickness (~2mm) from outer bounds so it stays inside
    WALL_T = 2.0
    CX0 = hb[0][0] + WALL_T
    CX1 = hb[1][0] - WALL_T
    CY0 = hb[0][1] + WALL_T
    CY1 = hb[1][1] - WALL_T
    # Z: from actual floor to actual ceiling (within the cavity)
    CZ0 = hb[0][2]
    CZ1 = hb[1][2]

    high_mani = to_manifold(parts[high_idx], tolerance=0.01)

    # Step 1: Fill the entire cavity with a solid block (union with part).
    # The block overlaps the cavity interior and merges into the walls.
    filler = m3d.Manifold.cube([CX1 - CX0, CY1 - CY0, CZ1 - CZ0], center=False) \
        .translate([CX0, CY0, CZ0])
    high_filled = high_mani + filler
    print(f"Filler: X={CX0:.1f}-{CX1:.1f}, Y={CY0:.1f}-{CY1:.1f}, Z={CZ0:.1f}-{CZ1:.1f}")

    # Step 2: Subtract the ESP32 groove — a single clean rectangular cut.
    # Cuts from below floor to ceiling to create one clean pocket.
    groove = m3d.Manifold.cube([ESP_W, ESP_L, CZ1 - CZ0], center=False) \
        .translate([gx0, gy0, CZ0])
    high_mani = high_filled - groove

    parts[high_idx] = from_manifold(high_mani)
    print(f"ESP32 groove: X={gx0:.1f}-{gx1:.1f} ({ESP_W}mm), Y={gy0:.1f}-{gy1:.1f} ({ESP_L}mm)")

    low_mani = to_manifold(parts[low_idx], tolerance=0.01)

    # 5. Remove source standoffs (their 6mm tall bodies above Z=2)
    low_mani = chop_source_standoff(low_mani, *SRC_STAND_1)
    low_mani = chop_source_standoff(low_mani, *SRC_STAND_2)
    print("Chopped source standoffs")

    # 6. Add 4 uniform standoffs at the 4 corners
    standoff_positions = [
        SRC_STAND_1,                           # (99.145, 114.9)
        SRC_STAND_2,                           # (123.855, 114.9)
        (SRC_STAND_1[0], MIRROR_Y),            # (99.145, 141.1)
        (SRC_STAND_2[0], MIRROR_Y),            # (123.855, 141.1)
    ]
    for (x, y) in standoff_positions:
        outer, inner = make_standoff(x, y)
        low_mani = low_mani + outer    # add the standoff post
        low_mani = low_mani - inner    # subtract the through-hole (pierces floor)
        print(f"  Standoff: ({x}, {y}), R_out={STAND_R_OUT}, R_in={STAND_R_IN}, Z={STAND_Z_LOW}-{STAND_Z_LOW+STAND_HEIGHT} (through)")

    parts[low_idx] = from_manifold(low_mani)
    combined = trimesh.util.concatenate(parts)

    output = os.path.join(script_dir, "esp32-c6-c4001-enclosure.v3.stl")
    combined.export(output)
    print(f"\nSaved: {output}")
    print(f"Final: {combined.extents[0]:.1f} x {combined.extents[1]:.1f} x {combined.extents[2]:.1f} mm")


if __name__ == "__main__":
    main()
