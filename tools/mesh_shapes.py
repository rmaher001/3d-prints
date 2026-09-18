"""Shared trimesh shape helpers for the generators.

`centered_box` and `rounded_slot` are the two shapes every generator here keeps
needing: a box placed by its center, and a stadium-shaped slot — the rounded-end
vent slot the Apollo and Olimex cases are covered in — oriented on any axis.

Slots are built with their length along X and drilled through Z, then rotated:
`along` names the axis the length runs on, `through` the axis it drills. Make
`depth` larger than the wall you are cutting so the slot breaks through both
faces.
"""
from __future__ import annotations

import numpy as np
import trimesh

from trimesh_helpers import from_manifold, to_manifold

_ORIENTATIONS = {
    ("x", "z"): np.eye(4),
    ("x", "y"): trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]),
    ("z", "x"): trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]),
}


def centered_box(width: float, depth: float, height: float,
                 center=(0.0, 0.0, 0.0)) -> trimesh.Trimesh:
    """A box of the given extents, centered on `center`."""
    box = trimesh.creation.box(extents=(width, depth, height))
    box.apply_translation(center)
    return box


def rounded_slot(length: float, width: float, depth: float,
                 center=(0.0, 0.0, 0.0), along: str = "x",
                 through: str = "z", sections: int = 40) -> trimesh.Trimesh:
    """A stadium-shaped slot: `length` along `along`, drilled through `through`."""
    if (along, through) not in _ORIENTATIONS:
        raise ValueError(f"unsupported slot orientation: along={along}, through={through}")
    body = centered_box(length - width, width, depth)
    solid = to_manifold(body)
    for end in (-1, 1):
        cap = trimesh.creation.cylinder(radius=width / 2.0, height=depth, sections=sections)
        cap.apply_translation([end * (length - width) / 2.0, 0, 0])
        solid = solid + to_manifold(cap)
    slot = from_manifold(solid)
    slot.merge_vertices()
    slot.apply_transform(_ORIENTATIONS[(along, through)])
    slot.apply_translation(center)
    return slot
