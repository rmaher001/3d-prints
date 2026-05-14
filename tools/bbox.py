"""Cross-stack bounding-box helpers.

Dispatches over the three mesh representations used in this toolkit:
- numpy-stl `stl.Mesh`
- OCP `TopoDS_Shape`
- trimesh `Trimesh`
"""
from __future__ import annotations

import numpy as np
import trimesh
from OCP.TopoDS import TopoDS_Shape
from stl import mesh as _stl_mesh

from step_primitives import get_bbox as _ocp_get_bbox


def get_extents(thing) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (mins, maxs, dims) as length-3 numpy arrays in mm."""
    if isinstance(thing, _stl_mesh.Mesh):
        v = thing.vectors.reshape(-1, 3)
        mins = v.min(axis=0)
        maxs = v.max(axis=0)
    elif isinstance(thing, trimesh.Trimesh):
        mins = np.asarray(thing.bounds[0])
        maxs = np.asarray(thing.bounds[1])
    elif isinstance(thing, TopoDS_Shape):
        xmin, ymin, zmin, xmax, ymax, zmax = _ocp_get_bbox(thing)
        mins = np.array([xmin, ymin, zmin])
        maxs = np.array([xmax, ymax, zmax])
    else:
        raise TypeError(f"Unsupported shape type: {type(thing).__name__}")
    return mins, maxs, maxs - mins


def print_dimensions(thing, label: str = "Bounding box") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Print a 3-line bounding-box report and return (mins, maxs, dims)."""
    mins, maxs, dims = get_extents(thing)
    print(f"{label}:")
    print(f"  X: {mins[0]:.2f} to {maxs[0]:.2f} (width:  {dims[0]:.2f}mm)")
    print(f"  Y: {mins[1]:.2f} to {maxs[1]:.2f} (depth:  {dims[1]:.2f}mm)")
    print(f"  Z: {mins[2]:.2f} to {maxs[2]:.2f} (height: {dims[2]:.2f}mm)")
    return mins, maxs, dims
