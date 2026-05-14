# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a 3D printing toolkit for Claude Code. The user describes a physical object they need, and Claude Code writes a parametric Python generator that produces print-ready STL files. Each subdirectory is one project/object.

The `tools/` directory contains a shared library of primitives and utilities that generators import. When building a new object, **reuse and extend** the shared library rather than copy-pasting helpers into each generator.

## Environment

Shared venv: `/Users/richard/3d-prints/tools/venv`

```bash
# Run any generator
/Users/richard/3d-prints/tools/venv/bin/python <script.py>

# Install new packages
/Users/richard/3d-prints/tools/venv/bin/pip install <package>
```

Key packages:
- `numpy-stl` — STL mesh generation (`from stl import mesh`)
- `cadquery-ocp` — OpenCASCADE / STEP file operations (`from OCP...`)
- `numpy` — vertex/face array math

## Shared Primitives (`tools/`)

Reusable geometry helpers — import these instead of redefining per-project:

| Module | Functions |
|---|---|
| `mesh_primitives` | `make_box(w, d, h, cx, cy, cz)`, `make_cylinder(r, h, cx, cy, cz, n)`, `make_ring(r_outer, r_inner, h, ...)`, `combine(meshes)`, `flip_z(mesh, max_z)` — numpy-stl mesh output |
| `step_primitives` | `make_box(x, y, z, w, d, h)`, `make_cylinder(r, h, x, y, z)`, `translate(s, dx, dy, dz)`, `fuse(a, b)`, `cut(a, b)`, `load_step`, `save_step`, `save_stl`, `get_bbox` — OCP/OpenCASCADE BREP |
| `trimesh_helpers` | `to_manifold(mesh, tolerance)`, `from_manifold(mani)` — for STL boolean surgery via manifold3d |
| `bbox` | `print_dimensions(thing, label)`, `get_extents(thing)` — works on numpy-stl, OCP, and trimesh objects |

Legacy import surface preserved in `tools/modify_step.py` (re-exports from `step_primitives`).

**When you add a new primitive** (e.g., fillet, chamfer, wedge, slot, screw hole), add it to the matching module so future projects can use it. Add tests in `tools/tests/`.

## Writing a New Generator

1. **Create a subdirectory** for the project
2. **Import shared primitives** from `tools/`
3. **Define dimensions** as module-level constants in mm — wall thickness, clearances, channel widths, etc. Derived positions computed from constants.
4. **Build geometry** as a list of primitives, `combine()`, `.save()`
5. **Print verification** — bounding box dims to stdout so the user can sanity-check before slicing
6. **Print guidance** — orientation advice, support notes, material suggestions

### Generator structure
```python
"""Docstring: what this object is, ASCII side-view profile, coordinate system."""

import sys
sys.path.insert(0, "/Users/richard/3d-prints/tools")
from mesh_primitives import make_box, make_cylinder, combine
from bbox import print_dimensions

# ── Dimensions (mm) ─────────────────────────
WIDTH = 50.0
WALL = 4.0
CLEARANCE = 1.5      # always explicit
# ... derived positions ...

# ── Build ────────────────────────────────────
parts = []
parts.append(make_box(...))
parts.append(make_cylinder(...))

result = combine(parts)
result.save("output.stl")

# ── Verify ───────────────────────────────────
# print bounding box, print orientation advice
```

## Design Knowledge

### Tolerances
- **Sliding fit**: ~1.5mm clearance (e.g., cradle holding a device)
- **Snug fit**: ~0.3mm clearance (e.g., tenon into socket)
- **Press fit**: 0.0 to -0.05mm (interference fit, may need XY compensation in slicer)
- Always expose tolerance as a named constant so the user can tune after test prints

### Print Orientation
- Orient to minimize overhangs and supports
- Large flat surfaces on the build plate for adhesion
- For multi-part assemblies, `flip_z()` can generate print-orientation STL separate from assembly-orientation
- Note: the user's printer is a **Bambu Lab P2S** (256x256x256mm build volume)

### Multi-Part Assemblies
- Generate separate STL per part (e.g., `part_a.stl`, `part_b.stl`)
- Also generate a full-assembly reference STL for visualization
- Use tenon/socket joints for connecting parts (see `usw-cooling-stand` for example)
- Expose tenon clearance as a tunable constant (0.1mm is a good starting point)

### Structural
- Default wall thickness: 4mm (good strength/weight balance for PLA/PETG)
- Cross braces for tall/narrow structures
- Corner posts for open sections that need rigidity

## Evolving the Toolkit

This library is meant to grow. When working on a new project:
- If you write a geometry helper that would be useful beyond this one project, add it to `tools/`
- If you learn a print-specific lesson (e.g., minimum feature size, bridge distance), add it to the Design Knowledge section above
- If a pattern recurs across generators (e.g., screw bosses, fan cutouts), extract it into a parameterized function in the shared library
