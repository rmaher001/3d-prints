#!/usr/bin/env python3
"""Apollo R-PRO-1 standing case: the case and its stand as one printed part.

The case stands on the end that carries the cable openings, light slots up. This
grows that end downward by LIFT_MM: the side walls and the front wall carry on
down as plain walls, the back of the skirt is left open so the vents in the
bottom of the case exhaust into it and out the back, and a solid base plate
runs HEEL_REACH past the case's back so the tall part does not tip.

Everything above the skirt is the dual-slot case untouched, scaled SCALE_XY in
X and Y — the fit Richard verified on 2026-09-17.

Case frame: Z=0 is the face with the light slots, the open back is at the case's
own Z depth; -Y is the end this stands on. It prints face down, no supports.
"""
import os
import sys
import tempfile

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bbox import print_dimensions
from mesh_shapes import centered_box
from step_primitives import load_step, save_stl
from trimesh_helpers import from_manifold, to_manifold

SOURCE_STEP = os.path.join(HERE, "r_pro-1_case-v2_DUAL_slots.step")
OUTPUT_STL = os.path.join(HERE, "r_pro-1_standing_case.stl")

SCALE_XY = 1.005     # the case scale that fits the board
LIFT_MM = 20.0       # clear height added under the case
WALL = 1.75          # matches the case's own wall
FRONT_T = 2.0        # front wall thickness down the skirt
BASE_T = 3.0         # base plate thickness, solid
HEEL_REACH = 30.0    # how far the base runs back BEHIND the case
HEEL_R = 8.0         # corner radius on the back of the heel
BLEND = 2.5          # skirt runs this far up the case, filling its rounded end
OVERCUT = 2.0        # oversize on cutting tools, so they break clean through
DEFLECTION = 0.02


def scaled_case():
    """The dual-slot case at the printed scale, as a mesh."""
    shape = load_step(SOURCE_STEP)
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as fh:
        tmp = fh.name
    try:
        save_stl(shape, tmp, deflection=DEFLECTION)
        mesh = trimesh.load(tmp)
    finally:
        os.unlink(tmp)
    mesh.apply_transform(np.diag([SCALE_XY, SCALE_XY, 1.0, 1.0]))
    return mesh


def foot(case):
    """Skirt walls plus the solid base plate, built against the case bounds."""
    x_half = case.extents[0] / 2.0
    y_top = case.bounds[0, 1]            # the case's bottom end
    y_bot = y_top - LIFT_MM
    z_back = case.bounds[1, 2]           # the case's open back
    heel_z = z_back + HEEL_REACH
    # the case's end is rounded off over ~2 mm, so the skirt runs BLEND past the
    # joint to fill that curve; the lowest vent slot is 4.9 mm up, well clear
    wall_h = LIFT_MM + BLEND
    y_mid = (y_top + BLEND + y_bot) / 2.0

    solid = None
    for side in (-1, 1):                 # side walls, continuing the case's own
        wall = centered_box(WALL, wall_h, z_back,
                            (side * (x_half - WALL / 2.0), y_mid, z_back / 2.0))
        solid = to_manifold(wall) if solid is None else solid + to_manifold(wall)
    solid = solid + to_manifold(
        centered_box(2 * x_half, wall_h, FRONT_T, (0, y_mid, FRONT_T / 2.0)))

    base = to_manifold(centered_box(2 * x_half, BASE_T, heel_z,
                                    (0, y_bot + BASE_T / 2.0, heel_z / 2.0)))
    for side in (-1, 1):                 # round the two back corners of the heel
        square = centered_box(HEEL_R, BASE_T + OVERCUT, HEEL_R,
                              (side * (x_half - HEEL_R / 2.0), y_bot + BASE_T / 2.0,
                               heel_z - HEEL_R / 2.0))
        quarter = trimesh.creation.cylinder(radius=HEEL_R, height=BASE_T + OVERCUT,
                                            sections=48)
        quarter.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        quarter.apply_translation([side * (x_half - HEEL_R), y_bot + BASE_T / 2.0,
                                   heel_z - HEEL_R])
        base = base - (to_manifold(square) - to_manifold(quarter))
    return solid + base


def build():
    case = scaled_case()
    out = from_manifold(to_manifold(case) + foot(case))
    out.merge_vertices()
    out.update_faces(out.nondegenerate_faces())
    out.remove_unreferenced_vertices()
    return out


if __name__ == "__main__":
    part = build()
    part.export(OUTPUT_STL)
    print(f"Saved: {OUTPUT_STL}")
    print_dimensions(part, "standing case")
    print(f"  watertight: {part.is_watertight}, volume: {part.volume / 1000.0:.1f} cm3")
