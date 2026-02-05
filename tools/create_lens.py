#!/usr/bin/env python3
"""
Lens Cover Generator - Creates press-fit translucent lens covers for light slots.

Generates a STEP file for a lens cover with an outer flange (lip) and insert body
that press-fits into the light slots cut in the Apollo R-PRO-1 case.

Usage:
    python create_lens.py [output.step]

Default output: ../apollo-r-pro-1-case/r_pro-1_lens_cover.step
"""

import os
import sys

from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.gp import gp_Pnt
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

# --- Configurable Dimensions ---

# Slot opening dimensions (must match modify_step.py cuts)
SLOT_WIDTH = 40.0   # mm
SLOT_HEIGHT = 10.0   # mm

# Clearance per side for the insert (adjust if fit is too tight/loose)
CLEARANCE = 0.1     # mm per side

# Flange (outer lip) overhang per side
FLANGE_LIP = 1.0    # mm per side

# Thicknesses
FLANGE_THICKNESS = 0.8   # mm - thin for light transmission
INSERT_DEPTH = 2.0       # mm - how far insert goes into slot


def create_lens_cover():
    """
    Create a lens cover shape with flange + insert body.

    The cover is oriented with:
    - Flange on the XY plane at Z=0 (face-down for printing)
    - Insert body extending in +Z direction

    Returns the fused shape.
    """
    # Insert body dimensions (with clearance)
    insert_w = SLOT_WIDTH - 2 * CLEARANCE
    insert_h = SLOT_HEIGHT - 2 * CLEARANCE

    # Flange dimensions
    flange_w = SLOT_WIDTH + 2 * FLANGE_LIP
    flange_h = SLOT_HEIGHT + 2 * FLANGE_LIP

    # Create flange (centered at origin in XY)
    flange = BRepPrimAPI_MakeBox(
        gp_Pnt(-flange_w / 2, -flange_h / 2, 0),
        flange_w,
        flange_h,
        FLANGE_THICKNESS,
    ).Shape()

    # Create insert body (centered at origin in XY, starts at top of flange)
    insert = BRepPrimAPI_MakeBox(
        gp_Pnt(-insert_w / 2, -insert_h / 2, FLANGE_THICKNESS),
        insert_w,
        insert_h,
        INSERT_DEPTH,
    ).Shape()

    # Fuse the two shapes together
    fuse = BRepAlgoAPI_Fuse(flange, insert)
    fuse.Build()
    if not fuse.IsDone():
        raise RuntimeError("Boolean fuse operation failed")

    return fuse.Shape()


def print_dimensions(shape):
    """Print the bounding box dimensions of a shape."""
    bbox = Bnd_Box()
    BRepBndLib.AddClose_s(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    print(f"Bounding box:")
    print(f"  X: {xmin:.2f} to {xmax:.2f} (width: {xmax - xmin:.2f}mm)")
    print(f"  Y: {ymin:.2f} to {ymax:.2f} (height: {ymax - ymin:.2f}mm)")
    print(f"  Z: {zmin:.2f} to {zmax:.2f} (depth: {zmax - zmin:.2f}mm)")


def save_step(shape, filepath):
    """Save a shape to a STEP file."""
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    status = writer.Write(filepath)
    if status != 1:
        raise RuntimeError(f"Error writing STEP file: {filepath}, status: {status}")
    print(f"Saved: {filepath}")


def main():
    # Default output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_output = os.path.join(
        script_dir, "..", "apollo-r-pro-1-case", "r_pro-1_lens_cover.step"
    )
    output_path = sys.argv[1] if len(sys.argv) > 1 else default_output

    print("Lens Cover Generator")
    print("=" * 40)
    print(f"Slot opening:      {SLOT_WIDTH} x {SLOT_HEIGHT} mm")
    print(f"Clearance/side:    {CLEARANCE} mm")
    print(f"Insert body:       {SLOT_WIDTH - 2*CLEARANCE} x {SLOT_HEIGHT - 2*CLEARANCE} x {INSERT_DEPTH} mm")
    print(f"Flange:            {SLOT_WIDTH + 2*FLANGE_LIP} x {SLOT_HEIGHT + 2*FLANGE_LIP} x {FLANGE_THICKNESS} mm")
    print(f"Total depth:       {FLANGE_THICKNESS + INSERT_DEPTH} mm")
    print()

    cover = create_lens_cover()
    print_dimensions(cover)
    print()

    save_step(cover, output_path)
    print(f"\nPrint 2 copies (one for each slot).")


if __name__ == "__main__":
    main()
