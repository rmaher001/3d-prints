"""OCP / OpenCASCADE geometry primitives for STEP and STL output.

All functions operate on OCP `TopoDS_Shape` objects. Outputs are in millimeters.
"""
from __future__ import annotations

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.Bnd import Bnd_Box
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
from OCP.StlAPI import StlAPI_Writer
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec


def load_step(filepath: str):
    """Load a STEP file and return the root shape."""
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != 1:
        raise RuntimeError(f"Error reading STEP file: {filepath}, status: {status}")
    reader.TransferRoots()
    return reader.OneShape()


def save_step(shape, filepath: str) -> None:
    """Write a shape to a STEP file."""
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    status = writer.Write(filepath)
    if status != 1:
        raise RuntimeError(f"Error writing STEP file: {filepath}, status: {status}")


def save_stl(shape, filepath: str, deflection: float = 0.05) -> None:
    """Mesh a shape and write it as binary STL. `deflection` controls chord error in mm."""
    BRepMesh_IncrementalMesh(shape, deflection).Perform()
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    if not writer.Write(shape, filepath):
        raise RuntimeError(f"Error writing STL: {filepath}")


def make_box(x: float, y: float, z: float, w: float, d: float, h: float):
    """Box with min-corner at (x, y, z) and extents (w, d, h)."""
    return BRepPrimAPI_MakeBox(gp_Pnt(x, y, z), w, d, h).Shape()


def make_cylinder(r: float, h: float, x: float = 0, y: float = 0, z: float = 0):
    """Cylinder axis along +Z, base centered at (x, y, z), radius r, height h."""
    cyl = BRepPrimAPI_MakeCylinder(r, h).Shape()
    if x or y or z:
        return translate(cyl, x, y, z)
    return cyl


def translate(shape, dx: float, dy: float, dz: float):
    """Return a copy of shape translated by (dx, dy, dz)."""
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(dx, dy, dz))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def fuse(a, b):
    """Boolean union of two shapes."""
    op = BRepAlgoAPI_Fuse(a, b)
    op.Build()
    if not op.IsDone():
        raise RuntimeError("Boolean fuse operation failed")
    return op.Shape()


def cut(a, b):
    """Boolean subtraction: a minus b."""
    op = BRepAlgoAPI_Cut(a, b)
    op.Build()
    if not op.IsDone():
        raise RuntimeError("Boolean cut operation failed")
    return op.Shape()


def get_bbox(shape) -> tuple[float, float, float, float, float, float]:
    """Return (xmin, ymin, zmin, xmax, ymax, zmax)."""
    bbox = Bnd_Box()
    BRepBndLib.AddClose_s(shape, bbox)
    return bbox.Get()
