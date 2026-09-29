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


def drop_slivers(mesh: trimesh.Trimesh, min_volume: float = 1e-3) -> trimesh.Trimesh:
    """Return the one real body of `mesh`, dropping zero-volume sheets.

    Where a boolean cutter's curve meets a flat face tangentially, manifold can
    leave a flat sheet of triangles behind: no volume, nothing to print, but it
    counts as a second body. Raises ValueError if more than one body has volume,
    so a genuinely detached part is never thrown away silently.
    """
    mesh.merge_vertices()
    bodies = mesh.split(only_watertight=False)
    if len(bodies) <= 1:
        return mesh
    kept = [b for b in bodies if abs(b.volume) > min_volume]
    if len(kept) != 1:
        raise ValueError(f"{len(kept)} bodies with volume, expected 1")
    return kept[0]
