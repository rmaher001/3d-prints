# 3D Print Modification Tools

Python tools for modifying STEP files programmatically using OpenCASCADE.

## Environment Setup
```bash
cd /Users/richard/3d-prints/tools
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Verify Installation
```bash
python -c "from OCP.STEPControl import STEPControl_Reader; print('OCP installed successfully')"
```

## Usage
```python
from modify_step import load_step, save_step, cut, create_box, print_dimensions

shape = load_step("my_case.step")
xmin, ymin, zmin, xmax, ymax, zmax = print_dimensions(shape)

slot = create_box(x=-20, y=20, z=zmin - 5, width=40, depth=10, height=15)
result = cut(shape, slot)
save_step(result, "my_case_modified.step")
```

## Apollo Example
```bash
python modify_step.py --apollo input.step output.step
```
