#!/usr/bin/env python3
"""Lens Cover Generator — press-fit translucent lens covers for light slots.

Generates STEP files for lens covers with an outer flange (lip) and insert body
that press-fits into the light slots cut in the Apollo R-PRO-1 case.

Two variants: loose (0.1mm clearance) and press (-0.04mm interference fit for 100.7% XY scale).

Output: ../apollo-r-pro-1-case/r_pro-1_lens_cover_{loose,press}.step
"""
import os

from step_primitives import fuse, make_box, save_step
from bbox import print_dimensions

SLOT_WIDTH = 40.0
SLOT_HEIGHT = 10.0

VARIANTS = [
    ("loose", 0.1),
    ("press", -0.04),
]

FLANGE_LIP = 1.0
FLANGE_THICKNESS = 0.8
INSERT_DEPTH = 2.0


def create_lens_cover(clearance: float):
    insert_w = SLOT_WIDTH - 2 * clearance
    insert_h = SLOT_HEIGHT - 2 * clearance
    flange_w = SLOT_WIDTH + 2 * FLANGE_LIP
    flange_h = SLOT_HEIGHT + 2 * FLANGE_LIP

    flange = make_box(-flange_w / 2, -flange_h / 2, 0, flange_w, flange_h, FLANGE_THICKNESS)
    insert = make_box(-insert_w / 2, -insert_h / 2, FLANGE_THICKNESS, insert_w, insert_h, INSERT_DEPTH)
    return fuse(flange, insert)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "apollo-r-pro-1-case")

    print("Lens Cover Generator")
    print("=" * 40)

    for suffix, clearance in VARIANTS:
        print(f"\n--- Variant: {suffix} (clearance {clearance:+.2f} mm/side) ---")
        print(f"Slot opening:      {SLOT_WIDTH} x {SLOT_HEIGHT} mm")
        print(f"Insert body:       {SLOT_WIDTH - 2*clearance} x {SLOT_HEIGHT - 2*clearance} x {INSERT_DEPTH} mm")
        print(f"Flange:            {SLOT_WIDTH + 2*FLANGE_LIP} x {SLOT_HEIGHT + 2*FLANGE_LIP} x {FLANGE_THICKNESS} mm")
        print(f"Total depth:       {FLANGE_THICKNESS + INSERT_DEPTH} mm")
        print()

        cover = create_lens_cover(clearance)
        print_dimensions(cover)
        print()

        output_path = os.path.join(output_dir, f"r_pro-1_lens_cover_{suffix}.step")
        save_step(cover, output_path)
        print(f"Saved: {output_path}")

    print("\nPrint 2 copies of each variant (one per slot).")


if __name__ == "__main__":
    main()
