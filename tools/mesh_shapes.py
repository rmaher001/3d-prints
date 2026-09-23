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


def scooped_pocket(width: float, depth: float, height: float, radius: float,
                   floor_center=(0.0, 0.0, 0.0), sections: int = 64) -> trimesh.Trimesh:
    """A pocket cutter whose two bottom edges along X are rounded by `radius`.

    Subtract it from a block to get a cup you can sweep coins out of. `width`
    runs along X (ends stay square), `depth` along Y, `height` up Z from
    `floor_center`, which is the middle of the pocket's floor.
    """
    if not (0.0 < radius <= depth / 2.0 and radius < height):
        raise ValueError(f"radius {radius} must be > 0 and fit a {depth} x {height} section")
    upper = centered_box(width, depth, height - radius, (0.0, 0.0, radius + (height - radius) / 2.0))
    solid = to_manifold(upper)
    if depth > 2 * radius:
        solid = solid + to_manifold(centered_box(width, depth - 2 * radius, radius,
                                                 (0.0, 0.0, radius / 2.0)))
    for side in (-1, 1):
        edge = trimesh.creation.cylinder(radius=radius, height=width, sections=sections)
        edge.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        edge.apply_translation([0.0, side * (depth / 2.0 - radius), radius])
        solid = solid + to_manifold(edge)
    # the edge cylinders are 2r tall; trim anything past the pocket's own height
    solid = solid ^ to_manifold(centered_box(width, depth, height, (0.0, 0.0, height / 2.0)))
    pocket = from_manifold(solid)
    pocket.merge_vertices()
    pocket.apply_translation(floor_center)
    return pocket


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
