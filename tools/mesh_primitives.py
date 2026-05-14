"""numpy-stl geometry primitives shared across 3D-print generators.

All functions return `stl.Mesh` objects in millimeters, with:
- Box/cylinder/ring centered in XY around (cx, cy); bottom face at z=cz.
- Triangle winding consistent with numpy-stl conventions (outward normals).

Source: lifted from usw-cooling-stand/scad/gen_stl_v2.py.
"""
from __future__ import annotations

import numpy as np
from stl import mesh


def make_box(w: float, d: float, h: float,
             cx: float = 0, cy: float = 0, cz: float = 0) -> mesh.Mesh:
    """Axis-aligned box. w=X width, d=Y depth, h=Z height. Centered in XY at (cx,cy), bottom at cz."""
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - d / 2, cy + d / 2
    z0, z1 = cz, cz + h
    verts = np.array([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ])
    faces = np.array([
        [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5],
    ])
    m = mesh.Mesh(np.zeros(12, dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[f[j]]
    return m


def make_cylinder(r: float, h: float,
                  cx: float = 0, cy: float = 0, cz: float = 0,
                  n: int = 32) -> mesh.Mesh:
    """Solid cylinder, axis along Z. n = circumferential segments."""
    faces_list = []
    angles = np.linspace(0, 2 * np.pi, n + 1)[:-1]
    for i in range(n):
        a1, a2 = angles[i], angles[(i + 1) % n]
        x1, y1 = cx + r * np.cos(a1), cy + r * np.sin(a1)
        x2, y2 = cx + r * np.cos(a2), cy + r * np.sin(a2)
        faces_list.append([[cx, cy, cz], [x2, y2, cz], [x1, y1, cz]])
        faces_list.append([[cx, cy, cz + h], [x1, y1, cz + h], [x2, y2, cz + h]])
        faces_list.append([[x1, y1, cz], [x2, y2, cz], [x2, y2, cz + h]])
        faces_list.append([[x1, y1, cz], [x2, y2, cz + h], [x1, y1, cz + h]])
    m = mesh.Mesh(np.zeros(len(faces_list), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces_list):
        for j in range(3):
            m.vectors[i][j] = f[j]
    return m


def make_ring(r_outer: float, r_inner: float, h: float,
              cx: float = 0, cy: float = 0, cz: float = 0,
              n: int = 48) -> mesh.Mesh:
    """Annular cylinder (cylinder with cylindrical hole through it)."""
    faces_list = []
    angles = np.linspace(0, 2 * np.pi, n + 1)[:-1]
    for i in range(n):
        a1, a2 = angles[i], angles[(i + 1) % n]
        ox1, oy1 = cx + r_outer * np.cos(a1), cy + r_outer * np.sin(a1)
        ox2, oy2 = cx + r_outer * np.cos(a2), cy + r_outer * np.sin(a2)
        ix1, iy1 = cx + r_inner * np.cos(a1), cy + r_inner * np.sin(a1)
        ix2, iy2 = cx + r_inner * np.cos(a2), cy + r_inner * np.sin(a2)
        faces_list.append([[ox1, oy1, cz + h], [ox2, oy2, cz + h], [ix2, iy2, cz + h]])
        faces_list.append([[ox1, oy1, cz + h], [ix2, iy2, cz + h], [ix1, iy1, cz + h]])
        faces_list.append([[ox2, oy2, cz], [ox1, oy1, cz], [ix1, iy1, cz]])
        faces_list.append([[ox2, oy2, cz], [ix1, iy1, cz], [ix2, iy2, cz]])
        faces_list.append([[ox1, oy1, cz], [ox2, oy2, cz], [ox2, oy2, cz + h]])
        faces_list.append([[ox1, oy1, cz], [ox2, oy2, cz + h], [ox1, oy1, cz + h]])
        faces_list.append([[ix2, iy2, cz], [ix1, iy1, cz], [ix1, iy1, cz + h]])
        faces_list.append([[ix2, iy2, cz], [ix1, iy1, cz + h], [ix2, iy2, cz + h]])
    m = mesh.Mesh(np.zeros(len(faces_list), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces_list):
        for j in range(3):
            m.vectors[i][j] = f[j]
    return m


def combine(meshes: list[mesh.Mesh]) -> mesh.Mesh:
    """Concatenate a list of meshes into a single mesh."""
    return mesh.Mesh(np.concatenate([m.data for m in meshes]))


def flip_z(m: mesh.Mesh, max_z: float) -> mesh.Mesh:
    """Mirror mesh in Z around max_z/2. Used to swap print vs assembly orientation."""
    flipped = mesh.Mesh(m.data.copy())
    flipped.vectors[:, :, 2] = max_z - flipped.vectors[:, :, 2]
    for i in range(len(flipped.vectors)):
        flipped.vectors[i] = flipped.vectors[i][::-1]
    return flipped
