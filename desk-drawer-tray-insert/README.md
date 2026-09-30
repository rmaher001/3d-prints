# Desk drawer tray insert

A two-piece divider insert for the wooden tray in the credenza drawer. The tray is
365.5 × 179.5 × 30 mm inside. That's too long for the P2S bed, so the insert
prints as two halves that sit side by side: 183.25 × 180 × 22 mm on the left and
182.25 × 180 × 22 mm on the right (the right one is trimmed 1 mm, see Printing). The tray's
own walls hold them together, so they need no joint.

![layout](preview-layout.png)

Front is at the bottom of the picture: the side nearest you with the drawer open.

| Region | Size (mm) | For |
|---|---|---|
| pen shelf | 180 × 116, raised | six round grooves, all 18 wide and 12 deep (lowest point 10 mm off the bottom), one each for a pen, pencil, Sharpie, two screwdrivers and the Slice 10513 pen cutter (133.5 mm long, 17.5 mm at its thick end); items stand proud so they can be pinched, and each groove ends in a 22 mm finger cup, 6 mm deeper, at the seam end, so one item lifts out while its neighbours stay put |
| aa / aaa | 69 × 59 / 53 × 59, raised | 4 AA and 4 AAA, one slot each, lying front to back just under the top; a finger trough across the middle |
| coins | 55 × 59 | coins; the front and back floor edges curve up so coins slide out |
| cards | 107.5 × 62, 18 deep | about 16 cards lying flat, on a floor raised only 4 mm; sized for a card up to 89 × 58 mm, no scoops |
| tools | 107.5 × 71 | three round grooves (11 wide, 8 deep; the two screwdriver grooves have a 16 mm finger cup, 6 mm deeper, at the left end) for the small screwdrivers and the allen key (96 mm long arm; its 35 mm short arm lies in a round slot 10 wide and 40 long at the right end), and a pocket in front, about 90 × 30, for Command strips and Blu-Tack |
| keys | 56 × 41 | a physical key (50 mm) and a security key (45 mm), lying lengthwise |
| open bin | 50 × 41 | USB sticks up to about 48 mm (the SanDisk Dual Drive Go is ~44 mm) and odds and ends |
| fobs | 70 × 177 | both car key fobs (95 × 55 and 80 × 50) standing upright, end to end, no divider |

The halves are not interchangeable (different widths and contents). Either half
can be turned 180° only if its bins suit that end; a 90° turn won't fit, because
the half is about 3 mm longer than the tray is deep.

## Files

| File | Purpose |
|---|---|
| `create_insert.py` | Generator: every dimension is a named constant at the top |
| `test_create_insert.py` | Fit, printability and "does the item fit its bay" invariants |
| `desk-drawer-tray-insert-left.stl` / `-right.stl` | The two halves |
| `desk-drawer-tray-insert-fit-test-left.stl` / `-right.stl` | 3 mm tall floorless outlines for a fit check |
| `desk-drawer-tray-insert-groove-test.stl` | One 100 mm groove of the pen shelf, to try each pen and screwdriver |
| `desk-drawer-tray-insert-width-test-trim-1.0.stl` / `-1.5` / `-2.0` | The front 1 inch of the real right half at three widths (182.25, 181.75, 181.25 mm), full height, to find the width that drops into the tray; `desk-drawer-tray-insert-width-test.stl` is the current one |
| `preview-layout.png` | Top view sliced from the generated model |

```bash
../tools/venv/bin/python create_insert.py            # regenerate the STLs, test pieces + preview
../tools/venv/bin/python -m pytest test_create_insert.py -q
```

## Printing

1. **Groove strip and fit test first**, in any spare filament. Lay each pen,
   the pencil, the Sharpie and both screwdrivers in the groove strip: they should
   drop in without forcing and stand a few millimetres proud of it. If one is too
   fat, raise `MAX_PEN_DIA` (the grooves are sized for 16 mm). Then print both
   outlines, drop them into the tray side by side, and set both key fobs in
   the right-hand lane. The
   fit tests set the size, not the tape measure: the tray is a little bigger than
   the 365.5 × 179.5 it measured. The second pair of outlines (cooled on the
   plate) left 1 mm of play side to side and 0.5 mm front to back, so `CLEAR_W`
   and `CLEAR_D` take all of it up (pair 366.5 × 180). The full-height right half
   printed in textured PLA Wood then stuck, so `RIGHT_TRIM` takes 1 mm off it
   (pair 365.5 × 180). The width-test pieces check that at full height. If a print
   binds, raise the trim a little.

2. **The halves:** Bambu PLA Wood, White Oak, the closest match to the tray's
   pale wood. Dry it first (the wood powder takes on moisture), and use the
   0.4 mm nozzle; Bambu says PLA Wood is not compatible with the 0.2 mm one.
   Floor down, no supports, 0.20 mm layers, 4 walls (the 1.6 mm walls are four
   0.4 mm lines), 15% infill.

The longest pen or screwdriver (`LONGEST_TOOL`, 165 mm) is an estimate from a
photo. The pen grooves are 180 mm long and end in a 22 mm finger cup, so an item up to about
158 mm lies flat, and one up to about 169 mm still rests on the cup's edge.

The raised shelves are solid in the model; the slicer fills them with 15%
infill, so they cost print time more than filament.
