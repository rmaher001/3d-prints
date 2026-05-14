#!/usr/bin/env python3
"""STEP file modifier — Apollo R-PRO-1 light-slot example + CLI.

Primitives moved to `step_primitives`. This file is kept for the documented
`from modify_step import ...` import path (see tools/README.md) and the
`--apollo` CLI example.

Usage:
    python modify_step.py <input.step> <output.step>
    python modify_step.py --apollo <input.step> <output.step>
"""
from step_primitives import (
    load_step,
    save_step,
    cut,
    make_box as create_box,  # legacy name preserved for tools/README.md compatibility
    get_bbox as get_bounding_box,
)


def print_dimensions(shape):
    """Print bounding box dimensions and return them.

    Kept here for backward compatibility with the documented API. New code
    should import from `bbox` instead.
    """
    xmin, ymin, zmin, xmax, ymax, zmax = get_bounding_box(shape)
    print("Bounding box:")
    print(f"  X: {xmin:.2f} to {xmax:.2f} (width: {xmax - xmin:.2f}mm)")
    print(f"  Y: {ymin:.2f} to {ymax:.2f} (depth: {ymax - ymin:.2f}mm)")
    print(f"  Z: {zmin:.2f} to {zmax:.2f} (height: {zmax - zmin:.2f}mm)")
    return xmin, ymin, zmin, xmax, ymax, zmax


def example_apollo_dual_slots(input_file, output_file):
    """Add two light slots to the Apollo R-PRO-1 case for the LTR390 sensor."""
    print(f"Loading: {input_file}")
    shape = load_step(input_file)
    xmin, ymin, zmin, xmax, ymax, zmax = print_dimensions(shape)

    slot_width = 40.0
    slot_height = 10.0
    wall_thickness = 2.5
    cut_depth = 15.0

    print(f"\nCreating front slot: {slot_width}mm x {slot_height}mm")
    slot1 = create_box(
        -slot_width / 2,
        ymax - wall_thickness - slot_height,
        zmin - 5,
        slot_width,
        slot_height,
        cut_depth,
    )
    shape = cut(shape, slot1)

    print(f"Creating top slot: {slot_width}mm x {slot_height}mm")
    slot2 = create_box(
        -slot_width / 2,
        ymax - 5,
        zmin + wall_thickness,
        slot_width,
        cut_depth,
        slot_height,
    )
    shape = cut(shape, slot2)

    save_step(shape, output_file)
    print(f"Saved: {output_file}")
    print("Done!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        shape = load_step(sys.argv[1])
        print_dimensions(shape)
        save_step(shape, sys.argv[2])
        print(f"Saved: {sys.argv[2]}")
    elif len(sys.argv) == 4 and sys.argv[1] == "--apollo":
        example_apollo_dual_slots(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
