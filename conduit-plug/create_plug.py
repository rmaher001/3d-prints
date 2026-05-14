#!/usr/bin/env python3
"""Conduit Plug Generator — circular plugs for 22.5mm conduit.

Generates STL files for simple cylindrical plugs with a flange at multiple heights.

Usage:
    python create_plug.py

Output: conduit_plug_{height}mm.stl
"""
import os
import sys

sys.path.insert(0, "/Users/richard/3d-prints/tools")
from step_primitives import make_cylinder, translate, fuse, save_stl
from bbox import print_dimensions

CONDUIT_DIAMETER = 22.5
PLUG_DIAMETER = CONDUIT_DIAMETER
LIP_OVERHANG = 2.0
LIP_THICKNESS = 2.0
HEIGHTS = [2, 3, 4]


def create_plug(diameter: float, height: float):
    plug_radius = diameter / 2.0
    lip_radius = plug_radius + LIP_OVERHANG
    lip = make_cylinder(lip_radius, LIP_THICKNESS)
    plug = translate(make_cylinder(plug_radius, height), 0, 0, LIP_THICKNESS)
    return fuse(lip, plug)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print("Conduit Plug Generator")
    print(f"Conduit diameter: {CONDUIT_DIAMETER} mm")
    print(f"Plug diameter:    {PLUG_DIAMETER} mm")
    print(f"Lip diameter:     {PLUG_DIAMETER + 2 * LIP_OVERHANG} mm")
    print(f"Lip thickness:    {LIP_THICKNESS} mm")
    print("=" * 40)

    for h in HEIGHTS:
        print(f"\n--- {h}mm height ---")
        shape = create_plug(PLUG_DIAMETER, h)
        print_dimensions(shape)
        output_path = os.path.join(script_dir, f"conduit_plug_{h}mm.stl")
        save_stl(shape, output_path)
        print(f"  Saved: {output_path}")

    print("\nDone. Print flat side down, no supports needed.")


if __name__ == "__main__":
    main()
