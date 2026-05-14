#!/usr/bin/env python3
"""
Conduit Plug Generator - Creates circular plugs for 22.5mm conduit.

Generates STL files for simple cylindrical plugs at multiple heights.

Usage:
    python create_plug.py

Output: conduit_plug_{height}mm.stl
"""

import os
import math

from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.StlAPI import StlAPI_Writer
from OCP.BRepMesh import BRepMesh_IncrementalMesh

# --- Configurable Dimensions ---
CONDUIT_DIAMETER = 22.5  # mm
PLUG_DIAMETER = CONDUIT_DIAMETER  # exact match; printer shrinkage gives slight clearance
LIP_OVERHANG = 2.0  # mm per side
LIP_THICKNESS = 2.0  # mm
HEIGHTS = [2, 3, 4]  # mm


def create_plug(diameter, height):
    plug_radius = diameter / 2.0
    lip_radius = plug_radius + LIP_OVERHANG

    # Lip sits at Z=0 (flat on print bed), plug body extends upward
    lip = BRepPrimAPI_MakeCylinder(lip_radius, LIP_THICKNESS)
    lip.Build()

    plug = BRepPrimAPI_MakeCylinder(plug_radius, height)
    plug.Build()

    # Move plug body on top of lip using gp_Trsf
    from OCP.gp import gp_Trsf, gp_Vec
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(0, 0, LIP_THICKNESS))
    moved_plug = BRepBuilderAPI_Transform(plug.Shape(), trsf, True).Shape()

    fuse = BRepAlgoAPI_Fuse(lip.Shape(), moved_plug)
    fuse.Build()
    if not fuse.IsDone():
        raise RuntimeError("Fuse operation failed")
    return fuse.Shape()


def print_dimensions(shape):
    bbox = Bnd_Box()
    BRepBndLib.AddClose_s(shape, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    print(f"  Bounding box: {xmax - xmin:.2f} x {ymax - ymin:.2f} x {zmax - zmin:.2f} mm")


def save_stl(shape, filepath):
    mesh = BRepMesh_IncrementalMesh(shape, 0.05)  # 0.05mm linear deflection
    mesh.Perform()
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    success = writer.Write(shape, filepath)
    if not success:
        raise RuntimeError(f"Error writing STL: {filepath}")
    print(f"  Saved: {filepath}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Conduit Plug Generator")
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

    print("\nDone. Print flat side down, no supports needed.")


if __name__ == "__main__":
    main()
