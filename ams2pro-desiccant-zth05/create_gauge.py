#!/usr/bin/env python3
"""Fit gauge for seating a Tuya ZTH05 in the SPILLPROOF2 AMS 2 Pro box.

The donor model (AeonJoey, MakerWorld 1385353) cuts its hygrometer window for a
Xiaomi Mijia 2. Measured out of the shipped 3mf, the window is a THROUGH hole in
the box's outer wall: 43.16 x 43.16 mm held for 12.75 mm of depth, then a
shoulder narrowing X to 41.80 mm that stops the sensor from being pushed on
through into the AMS. A 12.2 mm-thick Xiaomi in a 12.75 mm run therefore seats
fully, face flush with (a hair below) the outer surface. That is the target fit.

REV 2. Rev 1 printed four widths on 5 mm tiles and answered the width question:
1 dot (the unmodified donor size) would not admit the ZTH05; 2-4 dots did. But
rev 1 modelled the full-size run as 3.69 mm, not 12.75 mm, so it could only ever
test width -- never whether the sensor seats to depth and finishes flush. This
revision is depth-true and reprints only the widths still in play.

Windows keep rev 1's labelling so the two prints compare directly: dot count n
means donor + (n-1) x 0.20 mm. This gauge prints 2 and 3 dots.

Output (next to this script):
  ams2pro-zth05-fit-gauge.stl

Print in the SAME MATERIAL as the finished boxes. ASA shrinks about twice as
much as PLA on cooling and holes shrink with the part -- over 43 mm that gap is
~0.1-0.15 mm, which is the whole clearance being measured. A PLA gauge does not
predict an ASA box.

Emitted as SEPARATE tiles rather than one plate: a wide thin flat plate in ASA
warps, and a warped plate distorts the openings and invalidates the test.
Insert the sensor from the TOP face (+Z), which stands in for the box's outer
face. 0.2 mm layers, as modelled (Z up), brim recommended for ASA. No supports
-- the shoulder's 0.68 mm step bridges.

Usage:  ../tools/venv/bin/python create_gauge.py
"""
import os
import sys

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")
sys.path.insert(0, TOOLS)
from step_primitives import cut, fuse, make_box, make_cylinder, save_stl  # noqa: E402
from bbox import print_dimensions  # noqa: E402

# ---------------------------------------------------------------------------
# Measured from the donor 3mf (3D/Objects/object_321.model, the wide box whose
# front carries the hygrometer window). Do not "clean up" these numbers -- they
# are what the shipped geometry actually is.
# ---------------------------------------------------------------------------
SOURCE_POCKET = 43.16        # window opening, X and Z on the box
SOURCE_POCKET_DEPTH = 12.75  # outer face (y=-11.50) in to the shoulder (y=+1.25)
SOURCE_SHOULDER = 41.80      # retaining shoulder, X only
SOURCE_SHOULDER_RUN = 5.30   # shoulder length before the pocket necks further
LIP_INSET = (SOURCE_POCKET - SOURCE_SHOULDER) / 2.0   # 0.68 per side

# Sensor under test: Tuya ZTH05, CR2032, Zigbee2MQTT-native.
SENSOR_NOMINAL = 43.0

# Gauge variants. Dot count n decodes to donor + (n-1) x STEP, same as rev 1.
# 1 dot is omitted: the rev 1 print proved the donor size will not admit a ZTH05.
STEP = 0.20
DOT_COUNTS = (2, 3)
WINDOW_SIZES = [SOURCE_POCKET + (n - 1) * STEP for n in DOT_COUNTS]

# Tiles. Separate coupons, not one plate -- see module docstring. The tile is as
# deep as the real pocket so the gauge tests seating, not just width; a shorter
# tile cannot tell a sensor that seats from one that bottoms out early.
LIP_T = 1.50                 # gauge shoulder; the donor runs 5.30, 1.50 is enough to stop
PLATE_T = SOURCE_POCKET_DEPTH + LIP_T
MARGIN = 5.0                 # material between a window edge and its tile edge
TILE = max(WINDOW_SIZES) + 2 * MARGIN     # uniform, so all tiles look alike
GAP = 6.0                    # clear space between tiles on the plate
COLS, ROWS = 2, 1

# Dot labels (recessed into the top face)
DOT_D = 2.5
DOT_DEPTH = 1.0
DOT_PITCH = 4.0
DOT_OFFSET = 2.5             # below the window edge, into the margin

BED = 256.0                  # Bambu Lab P2S build plate


def window_centers():
    """Centers of the four cells, in the same order as WINDOW_SIZES."""
    return [
        (col * (TILE + GAP) + TILE / 2.0, row * (TILE + GAP) + TILE / 2.0)
        for row in range(ROWS)
        for col in range(COLS)
    ]


def dot_centers(idx, cx, cy):
    """Dot positions in the margin below window `idx`; count encodes the size."""
    n = DOT_COUNTS[idx]
    size = WINDOW_SIZES[idx]
    y = cy - size / 2.0 - DOT_OFFSET
    x0 = cx - (n - 1) * DOT_PITCH / 2.0
    return [(x0 + i * DOT_PITCH, y) for i in range(n)]


def build_gauge():
    plate = None

    for idx, ((cx, cy), size) in enumerate(zip(window_centers(), WINDOW_SIZES)):
        tile = make_box(cx - TILE / 2.0, cy - TILE / 2.0, 0, TILE, TILE, PLATE_T)
        plate = tile if plate is None else fuse(plate, tile)
        # Full-size opening above the shoulder: the sensor's 12.75 mm of travel.
        plate = cut(plate, make_box(
            cx - size / 2.0, cy - size / 2.0, LIP_T,
            size, size, PLATE_T - LIP_T + 1.0,
        ))
        # Shoulder: narrows X only, matching the donor.
        lip_w = size - 2 * LIP_INSET
        plate = cut(plate, make_box(
            cx - lip_w / 2.0, cy - size / 2.0, -1.0,
            lip_w, size, LIP_T + 1.0,
        ))
        # Label.
        for dx, dy in dot_centers(idx, cx, cy):
            plate = cut(plate, make_cylinder(
                DOT_D / 2.0, DOT_DEPTH + 1.0,
                dx, dy, PLATE_T - DOT_DEPTH,
            ))

    return plate


def main():
    gauge = build_gauge()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "ams2pro-zth05-fit-gauge.stl")
    save_stl(gauge, out)
    print_dimensions(gauge, "ZTH05 fit gauge")
    print(f"  pocket depth {SOURCE_POCKET_DEPTH:.2f} mm + {LIP_T:.2f} mm shoulder")
    for idx, size in enumerate(WINDOW_SIZES):
        n = DOT_COUNTS[idx]
        print(f"  {n} dots: {size:.2f} mm "
              f"({size - SOURCE_POCKET:+.2f} vs donor, "
              f"{size - SENSOR_NOMINAL:+.2f} vs ZTH05 nominal)")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
