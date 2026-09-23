#!/usr/bin/env python3
"""Rework the SPILLPROOF2 sensor box to take a Tuya ZTH05.

The donor box (AeonJoey, MakerWorld 1385353, BY-NC-SA) cuts its hygrometer
window for a Xiaomi Mijia 2: 43.16 mm square, held for 12.75 mm of depth, then a
shoulder narrowing X to 41.80 mm that stops the sensor. The Xiaomi is 12.5 mm
thick, so it seats on that shoulder with its face flush to the outer surface.

A ZTH05 is 43.30 x 43.30 x 10.50 mm. Both numbers are wrong for this box:

  * 43.30 does not fit a 43.16 window. Confirmed on the printed fit gauge --
    the unmodified size would not admit the sensor at all.
  * 10.50 in a 12.75 mm pocket would sink the face 2.25 mm below the surface,
    with nothing gripping it.

So the rework does two things: widen the window to 43.90 mm, and bring the stop
forward from 12.75 mm to 10.60 mm so the face lands flush again.

43.90 is not 43.30-plus-a-guess. It is sized from what this printer actually
produces: on the fit tiles a nominal 43.76 mm window only just admitted the
sensor, so ~0.45 mm is lost across the opening and 43.90 lands at ~43.45 printed.

Bringing the stop forward is a FUSE, not a cut. Simply cutting the wider window
shallower would leave the old 43.16 mm section as the stop, and a 43.30 mm
sensor overlaps that by 0.07 mm per side -- nothing. The rails added here carry
the donor's own 41.80 mm shoulder forward instead, keeping 0.75 mm of overlap.
Like the donor's shoulder they narrow X only, so the bay stays open front to
back: air reaches the sensor and it can be pushed out from behind for a battery
or before an AMS dry cycle.

WHAT THIS COSTS. The donor already runs a thin frame -- a 43.16 mm window in a
45.00 mm box leaves 0.92 mm of rim per side. At 43.90 that rim becomes 0.55 mm,
one extrusion. That is acceptable here because the rim is not a free-standing
wall: it is the box's own outer skin, continuous with the material above and
below the window and backed by the seat rails behind. It is, however, the limit
-- 45.00 mm is the AMS bay and cannot move, so the window cannot grow much past
this. If a printed box still will not take the sensor, the answer is first-layer
compensation in the slicer, not more width.

LICENCE. The donor is CC BY-NC-SA. This script is our work; its OUTPUT is a
derivative of AeonJoey's mesh. It reads the 3mf from wherever you keep it and
writes the STL locally -- the derived geometry is deliberately NOT committed.

Usage:
    ../tools/venv/bin/python modify_box.py [path-to-donor.3mf]

Then in Bambu Studio, on the Front Row plate, right-click the 45 x 23 x 93 mm
"tinker.obj_2" (the thicker of the two objects sharing that name) and replace it
with the STL. Leave the Desiccant_Boxes print profile alone -- 0 top/bottom
shells, 7 walls, 50% grid infill is what makes the walls breathe.
"""
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass

import numpy as np
import trimesh

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
sys.path.insert(0, TOOLS)
from mesh_shapes import centered_box  # noqa: E402

# --- the donor, as measured -------------------------------------------------
# MakerWorld's download name first; the underscore spelling is how it was saved
# the first time round.
DONOR_FILES = ("SPILLPROOF+2+for+AMS+2+PRO_H2D_XIAOMI+UPPER.3mf",
               "SPILLPROOF_2_for_AMS_2_PRO_H2D_XIAOMI_UPPER.3mf")
DONOR_MEMBER = "3D/Objects/object_321.model"   # plate object id 4, "tinker.obj_2"

BOX_W, BOX_D, BOX_H = 45.00, 23.00, 93.00
DONOR_WINDOW = 43.16          # square opening at the outer face
DONOR_SEAT_DEPTH = 12.75      # outer face in to the shoulder
DONOR_SHOULDER = 41.80        # shoulder opening, X only
DONOR_DIVIDER = 1.49          # wall between sensor bay and desiccant chamber
DONOR_CEILING = 2.32          # wall between sensor bay and the top rail

# --- the sensor -------------------------------------------------------------
ZTH05_FACE = 43.30            # widest point, bezel included
ZTH05_THICK = 10.50

# --- printer calibration ----------------------------------------------------
# Measured on the rev 1 ASA fit tiles, 2026-08-31: a nominal 43.76 mm window only
# just admitted the 43.30 mm sensor, and 43.56 would not. So this printer and
# material lose ~0.45 mm across a 43 mm opening -- most of it first-layer squish,
# since the window's outer face prints face-down on the plate.
#
# The calibration transfers because the ORIENTATION matches. The plate transform
# for object id 4 maps model Y -> plate Z, so the box prints lying on its back,
# outer face on the bed, 23 mm tall. Both window axes therefore lie in the XY
# build plane -- the same plane the flat gauge tiles cut theirs in.
PRINTED_LOSS = 0.45
FIT_CLEARANCE = 0.15          # wanted at the PRINTED size, not the nominal one

# --- the change -------------------------------------------------------------
WINDOW = ZTH05_FACE + PRINTED_LOSS + FIT_CLEARANCE   # 43.90 nominal, ~43.45 printed
SEAT_DEPTH = ZTH05_THICK + 0.10          # 10.60, face 0.1 mm below flush
SHOULDER = DONOR_SHOULDER                # carried forward unchanged

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def _holds_the_box(path):
    try:
        with zipfile.ZipFile(path) as z:
            return DONOR_MEMBER in z.namelist()
    except (zipfile.BadZipFile, OSError):
        return False


def donor_path(argv_path=None, folder="~/Downloads"):
    """The donor to read: an explicit path, else the first original in `folder`.

    Saving the plate from Bambu Studio renumbers its objects, so a copy that has
    been printed from can sit next to a fresh download under the other name.
    Prefer the one that still holds the box; failing that, return whatever exists
    so load_donor can say why it is unusable.
    """
    if argv_path:
        return os.path.expanduser(argv_path)
    found = [p for p in (os.path.join(os.path.expanduser(folder), f) for f in DONOR_FILES)
             if os.path.exists(p)]
    for p in found:
        if _holds_the_box(p):
            return p
    return found[0] if found else os.path.join(os.path.expanduser(folder), DONOR_FILES[0])


def side_wall():
    """Rim left on each X side of the widened window."""
    return (BOX_W - WINDOW) / 2.0


def divider_wall():
    return DONOR_DIVIDER - (WINDOW - DONOR_WINDOW) / 2.0


def ceiling_wall():
    return DONOR_CEILING - (WINDOW - DONOR_WINDOW) / 2.0


def load_donor(path=None):
    """Pull the sensor box mesh straight out of the 3mf."""
    path = donor_path(path)
    if not zipfile.is_zipfile(path):
        raise ValueError(
            f"{path} is not a 3mf archive -- the download is probably incomplete. "
            f"Download it again from MakerWorld 1385353.")
    with zipfile.ZipFile(path) as z:
        if DONOR_MEMBER not in z.namelist():
            raise ValueError(
                f"{path} has no {DONOR_MEMBER}: it has been re-saved by a slicer, "
                f"which renumbers its objects. Download the original again from "
                f"MakerWorld 1385353 and do not save over it.")
        root = ET.fromstring(z.read(DONOR_MEMBER))
    mesh_el = root.find(".//m:mesh", NS)
    verts = np.array([[float(v.get(a)) for a in ("x", "y", "z")]
                      for v in mesh_el.find("m:vertices", NS)])
    faces = np.array([[int(t.get(k)) for k in ("v1", "v2", "v3")]
                      for t in mesh_el.find("m:triangles", NS)])
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


@dataclass
class Window:
    x_span: float
    z_span: float
    z_lo: float
    z_hi: float


def measure_window(mesh, depth, samples=3000):
    """Free span across the sensor bay `depth` mm in from the outer face.

    Probed rather than assumed: the numbers this returns are what the tests pin
    the donor against, so a different donor file fails instead of miscutting.
    """
    lo, hi = mesh.bounds
    y = lo[1] + depth
    zc = (1.03 + 44.16) / 2.0

    xs = np.linspace(-BOX_W / 2 + 0.1, BOX_W / 2 - 0.1, samples)
    pts = np.zeros((samples, 3))
    pts[:, 0], pts[:, 1], pts[:, 2] = xs, y, zc
    free_x = xs[~mesh.contains(pts)]

    zs = np.linspace(-6.0, 50.0, samples)
    pts = np.zeros((samples, 3))
    pts[:, 1], pts[:, 2] = y, zs
    free = ~mesh.contains(pts)
    # contiguous run through the window centre, so the desiccant chamber below
    # never gets counted as part of the opening
    k = int(np.argmin(abs(zs - zc)))
    a = b = k
    step = zs[1] - zs[0]
    while a > 0 and free[a - 1] and zs[a] - zs[a - 1] <= step * 1.5:
        a -= 1
    while b < samples - 1 and free[b + 1] and zs[b + 1] - zs[b] <= step * 1.5:
        b += 1
    return Window(x_span=free_x.max() - free_x.min(), z_span=zs[b] - zs[a],
                  z_lo=zs[a], z_hi=zs[b])


def rework(mesh):
    """Widen the window to WINDOW and carry the stop forward to SEAT_DEPTH."""
    lo, hi = mesh.bounds
    outer = lo[1]
    win = measure_window(mesh, depth=5.0)
    zc = (win.z_lo + win.z_hi) / 2.0

    # 1. widen: open the bay to WINDOW square, from the outer face to the seat
    y0, y1 = outer - 1.0, outer + SEAT_DEPTH
    cut = centered_box(WINDOW, y1 - y0, WINDOW, center=(0.0, (y0 + y1) / 2.0, zc))
    out = trimesh.boolean.difference([mesh, cut], engine="manifold")

    # 2. seat: carry the 41.80 mm shoulder forward, X sides only, so the widened
    #    window still has something to stop against
    rail_w = (WINDOW - SHOULDER) / 2.0
    y0, y1 = outer + SEAT_DEPTH, outer + DONOR_SEAT_DEPTH
    for sign in (-1.0, +1.0):
        rail = centered_box(rail_w, y1 - y0, WINDOW,
                            center=(sign * (SHOULDER + rail_w) / 2.0, (y0 + y1) / 2.0, zc))
        out = trimesh.boolean.union([out, rail], engine="manifold")

    out.process(validate=True)
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    path = donor_path(src)
    if not os.path.exists(path):
        sys.exit(f"donor 3mf not found: {path}\n"
                 f"pass its path: ../tools/venv/bin/python modify_box.py <file.3mf>")

    try:
        donor = load_donor(path)
    except ValueError as e:
        sys.exit(str(e))
    out = rework(donor)

    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "ams2pro-sensor-box-zth05.stl")
    out.export(dest)

    w, d, h = out.bounds[1] - out.bounds[0]
    print(f"donor : {DONOR_MEMBER}  window {DONOR_WINDOW} mm, seat {DONOR_SEAT_DEPTH} mm")
    print(f"sensor: ZTH05 {ZTH05_FACE} x {ZTH05_FACE} x {ZTH05_THICK} mm")
    print(f"rework: window {WINDOW:.2f} mm nominal -> ~{WINDOW - PRINTED_LOSS:.2f} mm "
          f"printed ({WINDOW - PRINTED_LOSS - ZTH05_FACE:+.2f} on the sensor), "
          f"seat {SEAT_DEPTH} mm (face {SEAT_DEPTH - ZTH05_THICK:.2f} mm below flush)")
    print(f"        stop overlap {(ZTH05_FACE - SHOULDER) / 2:.2f} mm per side")
    print(f"walls : rim {side_wall():.2f}  divider {divider_wall():.2f}  "
          f"ceiling {ceiling_wall():.2f}")
    print(f"result: {w:.2f} x {d:.2f} x {h:.2f} mm, watertight={out.is_watertight}, "
          f"bodies={out.body_count}")
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
