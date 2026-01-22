#!/usr/bin/env python3
"""
STEP File Modifier - Cut slots/holes in STEP files using boolean operations

Uses OCP (OpenCASCADE Python bindings) for CAD operations.

Usage:
    python modify_step.py <input.step> <output.step>

Or import and use programmatically - see examples below.
"""

from OCP.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.gp import gp_Pnt
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box


def load_step(filepath):
    """Load a STEP file and return the shape."""
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != 1:
        raise Exception(f"Error reading STEP file: {filepath}, status: {status}")
    reader.TransferRoots()
    return reader.OneShape()


def save_step(shape, filepath):
    """Save a shape to a STEP file."""
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    status = writer.Write(filepath)
    if status != 1:
        raise Exception(f"Error writing STEP file: {filepath}, status: {status}")
    print(f"Saved: {filepath}")


def get_bounding_box(shape):
    """Get the bounding box of a shape. Returns (xmin, ymin, zmin, xmax, ymax, zmax)."""
    bbox = Bnd_Box()
    BRepBndLib.AddClose_s(shape, bbox)
    return bbox.Get()


def print_dimensions(shape):
    """Print the dimensions of a shape."""
    xmin, ymin, zmin, xmax, ymax, zmax = get_bounding_box(shape)
    print(f"Bounding box:")
    print(f"  X: {xmin:.2f} to {xmax:.2f} (width: {xmax - xmin:.2f}mm)")
    print(f"  Y: {ymin:.2f} to {ymax:.2f} (depth: {ymax - ymin:.2f}mm)")
    print(f"  Z: {zmin:.2f} to {zmax:.2f} (height: {zmax - zmin:.2f}mm)")
    return xmin, ymin, zmin, xmax, ymax, zmax


def create_box(x, y, z, width, depth, height):
    """Create a box shape at the given position with given dimensions."""
    return BRepPrimAPI_MakeBox(
        gp_Pnt(x, y, z),
        width,
        depth,
        height
    ).Shape()


def cut(shape, cutter):
    """Subtract cutter from shape (boolean cut)."""
    cut_op = BRepAlgoAPI_Cut(shape, cutter)
    cut_op.Build()
    if not cut_op.IsDone():
        raise Exception("Boolean cut operation failed")
    return cut_op.Shape()


def example_apollo_dual_slots(input_file, output_file):
    """
    Add two light slots to the Apollo R-PRO-1 case for the LTR390 sensor.
    """
    print(f"Loading: {input_file}")
    shape = load_step(input_file)

    xmin, ymin, zmin, xmax, ymax, zmax = print_dimensions(shape)

    slot_width = 40.0
    slot_height = 10.0
    wall_thickness = 2.5
    cut_depth = 15.0

    print(f"\nCreating front slot: {slot_width}mm x {slot_height}mm")
    slot1 = create_box(
        x=-slot_width / 2,
        y=ymax - wall_thickness - slot_height,
        z=zmin - 5,
        width=slot_width,
        depth=slot_height,
        height=cut_depth
    )
    shape = cut(shape, slot1)

    print(f"Creating top slot: {slot_width}mm x {slot_height}mm")
    slot2 = create_box(
        x=-slot_width / 2,
        y=ymax - 5,
        z=zmin + wall_thickness,
        width=slot_width,
        depth=cut_depth,
        height=slot_height
    )
    shape = cut(shape, slot2)

    save_step(shape, output_file)
    print("Done!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        shape = load_step(sys.argv[1])
        print_dimensions(shape)
        save_step(shape, sys.argv[2])
    elif len(sys.argv) == 4 and sys.argv[1] == "--apollo":
        example_apollo_dual_slots(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
