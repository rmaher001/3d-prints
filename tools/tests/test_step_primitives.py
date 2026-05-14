"""Tests for OCP/OpenCASCADE primitives."""
import pytest

from step_primitives import (
    load_step,
    save_step,
    save_stl,
    make_box,
    make_cylinder,
    translate,
    fuse,
    cut,
    get_bbox,
)


def _dims(shape):
    xmin, ymin, zmin, xmax, ymax, zmax = get_bbox(shape)
    return (xmax - xmin, ymax - ymin, zmax - zmin)


def test_make_box_dimensions():
    box = make_box(0, 0, 0, 10, 20, 30)
    w, d, h = _dims(box)
    assert (round(w, 4), round(d, 4), round(h, 4)) == (10.0, 20.0, 30.0)


def test_make_cylinder_dimensions():
    cyl = make_cylinder(r=5, h=10)
    w, d, h = _dims(cyl)
    assert round(h, 4) == 10.0
    # bbox of cylinder is 2r × 2r
    assert round(w, 4) == 10.0
    assert round(d, 4) == 10.0


def test_translate_shifts_bbox():
    box = make_box(0, 0, 0, 10, 10, 10)
    moved = translate(box, 100, 200, 300)
    xmin, ymin, zmin, xmax, ymax, zmax = get_bbox(moved)
    assert round(xmin, 4) == 100
    assert round(ymin, 4) == 200
    assert round(zmin, 4) == 300


def test_fuse_combines_two_disjoint_boxes():
    a = make_box(0, 0, 0, 10, 10, 10)
    b = make_box(20, 0, 0, 10, 10, 10)
    combined = fuse(a, b)
    xmin, ymin, zmin, xmax, ymax, zmax = get_bbox(combined)
    assert round(xmin, 4) == 0
    assert round(xmax, 4) == 30  # spans both


def test_cut_subtracts():
    outer = make_box(0, 0, 0, 10, 10, 10)
    inner = make_box(2, 2, 2, 6, 6, 6)
    result = cut(outer, inner)
    # bbox is unchanged by cut (the outer shell remains)
    xmin, ymin, zmin, xmax, ymax, zmax = get_bbox(result)
    assert round(xmax - xmin, 4) == 10


def test_save_step_roundtrip(tmp_path):
    box = make_box(0, 0, 0, 7, 8, 9)
    fp = tmp_path / "box.step"
    save_step(box, str(fp))
    assert fp.exists()
    loaded = load_step(str(fp))
    w, d, h = _dims(loaded)
    assert (round(w, 2), round(d, 2), round(h, 2)) == (7.0, 8.0, 9.0)


def test_save_stl_writes_valid_binary_stl(tmp_path):
    from stl import mesh as stl_mesh
    box = make_box(0, 0, 0, 7, 8, 9)
    fp = tmp_path / "box.stl"
    save_stl(box, str(fp))
    assert fp.exists()
    loaded = stl_mesh.Mesh.from_file(str(fp))
    v = loaded.vectors.reshape(-1, 3)
    assert round(v[:, 0].max() - v[:, 0].min(), 2) == 7.0
    assert round(v[:, 1].max() - v[:, 1].min(), 2) == 8.0
    assert round(v[:, 2].max() - v[:, 2].min(), 2) == 9.0
