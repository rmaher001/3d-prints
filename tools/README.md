# 3D Print Toolkit

Python primitives shared across the 3D-print generators in this repo.

## Environment

```bash
cd /Users/richard/3d-prints/tools
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Or use the venv directly without activating:
```bash
/Users/richard/3d-prints/tools/venv/bin/python <script.py>
/Users/richard/3d-prints/tools/venv/bin/pytest tools/tests
```

## Modules

| Module | Purpose |
|---|---|
| `mesh_primitives` | numpy-stl primitives: `make_box`, `make_cylinder`, `make_ring`, `combine`, `flip_z` |
| `step_primitives` | OCP/OpenCASCADE: `make_box`, `make_cylinder`, `translate`, `fuse`, `cut`, `load_step`, `save_step`, `save_stl`, `get_bbox` |
| `trimesh_helpers` | `to_manifold`, `from_manifold` — round-trip between trimesh and manifold3d for boolean ops on imported STLs |
| `bbox` | `print_dimensions(thing, label)` and `get_extents(thing)` — works on numpy-stl meshes, OCP shapes, and trimesh objects |
| `modify_step` | Legacy import surface + `example_apollo_dual_slots` CLI. New code should import from `step_primitives` directly. |

## Usage

Generators import from the toolkit with an explicit sys.path insert (since `tools/` is not pip-installed):

```python
import sys
sys.path.insert(0, "/Users/richard/3d-prints/tools")
from mesh_primitives import make_box, combine
from bbox import print_dimensions
```

## Tests

```bash
/Users/richard/3d-prints/tools/venv/bin/pytest tools/tests -v
```

All primitives have round-trip / bbox / dispatch tests.
