"""Conversion helpers between trimesh.Trimesh and manifold3d.Manifold.

Use these to apply manifold3d's robust boolean ops to imported STL meshes
without writing the conversion boilerplate per project.

Source: lifted from esp32-c6-c4001-enclosure/modify_enclosure.py.
"""
from __future__ import annotations

import manifold3d as m3d
import numpy as np
import trimesh


def to_manifold(mesh: trimesh.Trimesh, tolerance: float = 0.01) -> m3d.Manifold:
    """Convert a trimesh.Trimesh to a manifold3d.Manifold, tolerating small gaps."""
    verts = np.ascontiguousarray(mesh.vertices.astype(np.float32))
    faces = np.ascontiguousarray(mesh.faces.astype(np.uint32))
    return m3d.Manifold(m3d.Mesh(vert_properties=verts, tri_verts=faces, tolerance=tolerance))


def from_manifold(mani: m3d.Manifold) -> trimesh.Trimesh:
    """Convert a manifold3d.Manifold back to a trimesh.Trimesh."""
    mm = mani.to_mesh()
    return trimesh.Trimesh(
        vertices=np.asarray(mm.vert_properties[:, :3]),
        faces=np.asarray(mm.tri_verts),
    )
