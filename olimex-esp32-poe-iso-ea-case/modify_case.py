#!/usr/bin/env python3
"""Olimex case lid friction-fit tightener.

The lid has 4 corner posts (triangular prisms ~3mm × 3mm × 3mm tall, from Z=2
to Z=5) that drop into 4 sockets in the case body. First print: case body fits
the Rev M PCB well, but the friction-fit lid is loose because the posts are
slightly undersized relative to the sockets.

This script grows each of the 4 posts outward from its own XY center by
POST_EXPAND_MM (per-vertex radial offset). The visible top plate (Z=0 to Z=2)
is UNCHANGED — exterior lid dimensions stay flush with the case opening, only
the hidden interlock posts get tighter.

Tune POST_EXPAND_MM empirically:
  0.2  = ~0.4mm total envelope growth (light interference vs a 0.32mm gap → firm fit)
  0.3  = tighter
  0.1  = looser
"""
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from bbox import print_dimensions

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_STL = os.path.join(SCRIPT_DIR, "olimex-esp32-poe-iso-ea-case.stl")
OUTPUT_STL = os.path.join(SCRIPT_DIR, "olimex-esp32-poe-iso-ea-case-v2.stl")

POST_EXPAND_MM = 0.2
POST_TOP_Z = 5.0   # 3 vertices per post face × 4 posts = 12 verts at this Z
POST_BASE_Z = 2.0  # post bases sit on top of the visible plate
Z_TOL = 0.01


def expand_vertices_radial(vertices: np.ndarray, idx_list: list[int], expand_mm: float) -> None:
    """Push each vertex in `idx_list` outward by `expand_mm` in XY from the group's centroid.

    Mutates `vertices` in place. Vertices exactly at the centroid are not moved
    (guards against div-by-zero).
    """
    pts = vertices[idx_list, :2]
    cx, cy = pts.mean(axis=0)
    for i in idx_list:
        dx = vertices[i, 0] - cx
        dy = vertices[i, 1] - cy
        dist = float(np.sqrt(dx * dx + dy * dy))
        if dist > 1e-6:
            vertices[i, 0] += dx / dist * expand_mm
            vertices[i, 1] += dy / dist * expand_mm


def group_vertices_by_quadrant(
    vertices: np.ndarray, idx_list: list[int], cx: float, cy: float
) -> dict[tuple[str, str], list[int]]:
    """Partition vertex indices into 4 groups by quadrant relative to (cx, cy)."""
    groups: dict[tuple[str, str], list[int]] = {
        ("R", "U"): [], ("R", "L"): [], ("L", "U"): [], ("L", "L"): []
    }
    for i in idx_list:
        qx = "R" if vertices[i, 0] > cx else "L"
        qy = "U" if vertices[i, 1] > cy else "L"
        groups[(qx, qy)].append(i)
    return groups


def main():
    m = trimesh.load(SOURCE_STL)
    print_dimensions(m, label="Source")

    parts = list(m.split(only_watertight=False))
    assert len(parts) == 2, f"Expected 2 disjoint parts, got {len(parts)}"
    # Lid sits at lower Y than the box in this STL's coordinate system; the box
    # also has a larger Z extent (it includes the case walls), so we use Y centroid.
    lid_idx = 0 if parts[0].centroid[1] < parts[1].centroid[1] else 1
    box = parts[1 - lid_idx]
    lid = parts[lid_idx]

    v = lid.vertices.copy()

    top_idx = np.where(np.isclose(v[:, 2], POST_TOP_Z, atol=Z_TOL))[0]
    assert len(top_idx) == 12, f"Expected 12 post-top verts, got {len(top_idx)}"

    # For each Z=5 vertex, find the closest Z=2 vertex by XY — that's its post base companion.
    base_global_idx = np.where(np.isclose(v[:, 2], POST_BASE_Z, atol=Z_TOL))[0]
    base_xy = v[base_global_idx, :2]
    base_idx_list: list[int] = []
    for ti in top_idx:
        dists = np.linalg.norm(base_xy - v[ti, :2], axis=1)
        base_idx_list.append(int(base_global_idx[np.argmin(dists)]))
    assert len(set(base_idx_list)) == 12, (
        f"Nearest-XY base matching produced duplicates: "
        f"{len(set(base_idx_list))} unique out of 12 expected. "
        f"Check POST_BASE_Z={POST_BASE_Z} against the source STL."
    )

    post_idx = list(top_idx) + base_idx_list
    assert len(set(post_idx)) == 24, "Post vertex indices not unique across top + base sets"

    lid_cx, lid_cy = lid.bounds.mean(axis=0)[:2]
    groups = group_vertices_by_quadrant(v, post_idx, lid_cx, lid_cy)
    for q, idx_list in groups.items():
        assert len(idx_list) == 6, f"Post {q} has {len(idx_list)} verts, expected 6"

    # Each post is enlarged by pushing its 6 verts outward from the post's own centroid.
    for q, idx_list in groups.items():
        post_cx, post_cy = v[idx_list, :2].mean(axis=0)
        expand_vertices_radial(v, idx_list, POST_EXPAND_MM)
        print(f"  Post {q[0]}{q[1]}: center=({post_cx:6.2f}, {post_cy:6.2f}), enlarged by {POST_EXPAND_MM}mm radial")

    print(f"\n4 corner posts grown by {POST_EXPAND_MM}mm radial outward; visible plate (Z<{POST_BASE_Z}) unchanged")

    lid_modified = trimesh.Trimesh(vertices=v, faces=lid.faces)
    combined = trimesh.util.concatenate([box, lid_modified])
    combined.export(OUTPUT_STL)
    print_dimensions(combined, label="Output")
    print(f"\nSaved: {OUTPUT_STL}")


if __name__ == "__main__":
    main()
