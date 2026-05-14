#!/usr/bin/env python3
"""
ESP32-C6 + C4001 Enclosure Modifier

Takes the ESP32-S3 C4001 enclosure STL and:
1. Extends length by 2.54mm (1 extra pin row for C6)
2. Adds screw bosses at USB end (matching far-end originals)
3. Increases Z height for more wire room
4. Deepens ESP32 groove for better retention (USB-C stays aligned)

Usage:
    python modify_enclosure.py

Input:  ~/Downloads/esp32-s3-c4001-enclosure.stl
Output: esp32-c6-c4001-enclosure.stl
"""

import os
import sys

import numpy as np
import trimesh
import manifold3d as m3d

sys.path.insert(0, "/Users/richard/3d-prints/tools")
from trimesh_helpers import to_manifold as _to_manifold, from_manifold as _from_manifold

# --- Source ---
SOURCE_STL = os.path.expanduser("~/Downloads/esp32-s3-c4001-enclosure.stl")

# --- Length extension ---
# Original pieces: LOW-X X=93-127 (34mm), HIGH-X X=129-163 (34mm).
# HIGH-X contains the ESP32 groove (walls at X=131 and X=161, interior 30mm).
# We extend BOTH pieces by EXTENSION so assembled widths stay matched AND the
# groove actually lengthens (by splitting the HIGH-X stretch inside its groove).
EXTENSION = 3.0
LOW_X_CUT = 110.0    # between the two standoffs — X=99 stays, X=121 shifts to X=124 with the piece end
HIGH_X_SHIFT_BOUND = 128.0   # everything in HIGH-X piece shifts once
HIGH_X_GROOVE_CUT = 148.0    # inside the ESP32 groove, between walls

# --- Z-axis modifications ---
GROOVE_DEEPEN = 2.0
HEIGHT_ADD = 3.0
FLOOR_Z = 2.0
FLOOR_BLEND = 0.5
TOP_Z = 7.5
TOP_BLEND = 0.5

# --- Screw bosses (matching original style) ---
# Original: outer R≈2.9, inner R≈1.4, 2mm protrusion inward from Y=109
# Z=2.27-7.45 (center Z=4.86), at X=141.8 and X=150.2
BOSS_OUTER_RADIUS = 2.9    # match originals
BOSS_INNER_RADIUS = 1.4    # M3 clearance, matches originals
BOSS_PROTRUSION = 2.0      # inward protrusion into cavity (matches originals)
BOSS_Z_CENTER = 4.86       # match originals (unaffected by groove-deepen zone)

# Distances from each end to boss centers
BOSS_OFFSET_1 = 12.8       # closer to end
BOSS_OFFSET_2 = 21.2       # further from end


def stretch_mesh_x(mesh, extension):
    """Extend both halves by the same amount.

    LOW-X piece: shift verts with X > LOW_X_CUT by +ext (grows to the right,
    preserves the standoffs at X=99 and X=121).
    HIGH-X piece: shift the whole piece by +ext to maintain the gap between
    pieces, then shift verts with X > HIGH_X_GROOVE_CUT by another +ext so the
    ESP32 groove's far wall moves while the near wall stays — groove grows by ext.
    """
    v = mesh.vertices.copy()
    # Compute all masks from the ORIGINAL vertex positions so we don't double-shift
    orig_x = v[:, 0]
    low_mask = (orig_x <= HIGH_X_SHIFT_BOUND) & (orig_x > LOW_X_CUT)
    high_mask = orig_x >= HIGH_X_SHIFT_BOUND
    groove_mask = orig_x > HIGH_X_GROOVE_CUT  # inside HIGH-X, past near wall

    v[low_mask, 0] += extension
    v[high_mask, 0] += extension
    v[groove_mask, 0] += extension  # second shift for HIGH-X far wall

    return trimesh.Trimesh(vertices=v, faces=mesh.faces)


def lower_usbc_cutout_top(mesh, drop):
    """Lower the top edge of the USB-C cutout only — the 4 corner vertices
    at (X=93 and X=95) with Y∈(111,145) Z≈7. Avoid wall corners (Y=109/147)
    and the lip (X>=95.3) so we don't create a step in the outer wall.
    """
    v = mesh.vertices.copy()
    mask = ((v[:, 0] <= 95.25) & (v[:, 1] > 110.5) & (v[:, 1] < 145.5)
            & (v[:, 2] > 6.9) & (v[:, 2] < 7.1))
    v[mask, 2] -= drop
    return trimesh.Trimesh(vertices=v, faces=mesh.faces)


def modify_z(mesh, groove_deepen, height_add):
    vertices = mesh.vertices.copy()
    z = vertices[:, 2]
    offset = np.zeros_like(z)

    offset[z <= FLOOR_Z] = -groove_deepen

    bl = (z > FLOOR_Z) & (z < FLOOR_Z + FLOOR_BLEND)
    offset[bl] = -groove_deepen * (1.0 - (z[bl] - FLOOR_Z) / FLOOR_BLEND)

    offset[z >= TOP_Z + TOP_BLEND] = height_add

    bh = (z > TOP_Z) & (z < TOP_Z + TOP_BLEND)
    offset[bh] = height_add * ((z[bh] - TOP_Z) / TOP_BLEND)

    vertices[:, 2] += offset
    return trimesh.Trimesh(vertices=vertices, faces=mesh.faces)


def extract_standoffs(source_mesh, x_centers, x_half=3.2, y_range=(108.8, 111.3), z_range=(2.2, 7.5)):
    """Extract faces belonging to the original standoffs from the source mesh.

    Returns a trimesh whose vertices are the originals' geometry — we clone this
    and translate it to the opposite end rather than trying to rebuild by hand.
    """
    v = source_mesh.vertices
    in_any = np.zeros(len(v), dtype=bool)
    for xc in x_centers:
        in_any |= ((v[:, 0] > xc - x_half) & (v[:, 0] < xc + x_half) &
                   (v[:, 1] >= y_range[0]) & (v[:, 1] <= y_range[1]) &
                   (v[:, 2] >= z_range[0]) & (v[:, 2] <= z_range[1]))
    face_mask = in_any[source_mesh.faces].all(axis=1)
    sub_faces = source_mesh.faces[face_mask]
    used = np.unique(sub_faces.flatten())
    remap = {old: new for new, old in enumerate(used)}
    new_faces = np.vectorize(remap.get)(sub_faces)
    return trimesh.Trimesh(vertices=v[used].copy(), faces=new_faces)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("ESP32-C6 C4001 Enclosure Modifier")
    print("=" * 45)

    mesh = trimesh.load(SOURCE_STL)
    x_min = mesh.bounds[0][0]
    y_min = mesh.bounds[0][1]
    print(f"Source: {mesh.extents[0]:.1f} x {mesh.extents[1]:.1f} x {mesh.extents[2]:.1f} mm")

    # 1. Stretch X — extend both pieces equally, and lengthen the HIGH-X groove
    stretched = stretch_mesh_x(mesh, EXTENSION)
    # Report per-piece widths
    comps = stretched.split(only_watertight=False)
    for c in comps:
        print(f"  piece X:{c.bounds[0][0]:.1f}-{c.bounds[1][0]:.1f} ({c.extents[0]:.2f}mm)")

    # 2. Modify Z (groove deepen + top raise)
    modified = modify_z(stretched, GROOVE_DEEPEN, HEIGHT_ADD)
    print(f"Z modified: groove -{GROOVE_DEEPEN}mm, top +{HEIGHT_ADD}mm")

    # 2b. Lower USB-C cutout top by the groove-deepen amount so it aligns with
    # the USB-C connector (the connector dropped with the floor; the cutout top
    # was stuck at Z=7).
    modified = lower_usbc_cutout_top(modified, GROOVE_DEEPEN)
    print(f"USB-C cutout top lowered by {GROOVE_DEEPEN}mm")

    # 3. The LOW-X piece has 2 existing standoffs at (X=99, Y=114.5) and
    #    (X=121, Y=114.5) — "top right" and "bottom right" corners. Add matching
    #    standoffs at the empty LEFT corners: same X, mirrored Y (141.5).
    STAND_R_OUT = 3.85     # measured from source: X span 7.69mm / 2
    STAND_R_IN = 1.5       # M3 clearance
    STAND_Z_LOW = 0.0      # sits on the deepened floor (was Z=2 in source, now Z=0)
    STAND_HEIGHT = 7.0     # matches originals after Z-deepen: Z=0 to Z=7

    def make_standoff(x, y):
        outer = m3d.Manifold.cylinder(height=STAND_HEIGHT, radius_low=STAND_R_OUT,
                                      radius_high=STAND_R_OUT, circular_segments=32)
        inner = m3d.Manifold.cylinder(height=STAND_HEIGHT, radius_low=STAND_R_IN,
                                      radius_high=STAND_R_IN, circular_segments=32)
        return (outer - inner).translate([x, y, STAND_Z_LOW])

    # Match exact source centers (99.145, 114.9) and (120.855, 114.9) mirrored.
    # The X=121 source standoff got shifted to X=123.855 by the stretch.
    new_bodies = [make_standoff(99.145, 141.1), make_standoff(123.855, 141.1)]
    print(f"  New standoffs: (99.1,141.1) and (123.9,141.1), R={STAND_R_OUT}, Z={STAND_Z_LOW}-{STAND_Z_LOW+STAND_HEIGHT}")

    # Union into the LOW-X component (which contains the existing standoffs).
    parts = list(modified.split(only_watertight=False))
    low_idx = min(range(len(parts)), key=lambda i: parts[i].bounds[0][0])
    low_mani = _to_manifold(parts[low_idx], tolerance=0.01)
    for body in new_bodies:
        low_mani = low_mani + body
    parts[low_idx] = _from_manifold(low_mani)

    combined = trimesh.util.concatenate(parts)

    output_path = os.path.join(script_dir, "esp32-c6-c4001-enclosure.stl")
    combined.export(output_path)
    print(f"\nSaved: {output_path}")
    print(f"Final: {combined.extents[0]:.1f} x {combined.extents[1]:.1f} x {combined.extents[2]:.1f} mm")
    print(f"\n4 screw bosses total: 2 original (far end) + 2 new (USB end)")


if __name__ == "__main__":
    main()
