# ams2pro-desiccant-zth05

Fitting a **Tuya ZTH05** Zigbee hygrometer into the **SPILLPROOF2 AMS 2 Pro
Desiccant Boxes** instead of the Xiaomi Mijia 2 the model was cut for.

Donor model: [MakerWorld 1385353](https://makerworld.com/en/models/1385353-spillproof2-ams-2-pro-desiccant-boxes-xiaomi)
by AeonJoey, BY-NC-SA, profile *"Upper Position Xiaomi Hygrometer"*.
This directory holds only our own work — the donor 3mf is not redistributed here.

## Why the ZTH05

The AMS 2 Pro desiccant bay is the hard constraint. Measured off the donor
meshes, a box is **45.0 × 23.0 × 93.0 mm** outside — so nothing wider than
45 mm goes in the slot, whatever the box looks like.

| Sensor | Size | Verdict |
|---|---|---|
| SONOFF SNZB-02D | 63 × 65 × 22.5 mm | 18 mm too wide |
| SONOFF SNZB-02WD | 62.8 × 58.5 × 21.8 mm | 14 mm too wide |
| SONOFF SNZB-02P | 45 × 45 × 17.7 mm | 3 mm too wide (equals the *outer* box) |
| Third Reality 3RTHS0224Z | 55.6 × 55.9 × 12.3 mm | 11 mm too wide, and LCD-free |
| Xiaomi Mijia 2 (donor's target) | 43 × 43 × 12.5 mm | fits, seats flush |
| **Tuya ZTH05** | **43.3 × 43.3 × 10.5 mm** (measured) | **fits, after the rework below** |

The two SONOFF LCD models are big because of their 2.2–2.5″ screens. The ZTH05
gets a 1.5″ LCD into the same 43 × 43 face as the Mijia 2, is Zigbee2MQTT-native
(`ZTH05`, `ZTH05Z`, `ZTH05_1`), and runs a CR2032.

The display matters here: the desiccant boxes sit in the AMS 2 Pro's front bay
with the hygrometer window facing out, readable without opening the lid.

## The measurement this is all built on

Pulled from the donor 3mf, `3D/Objects/object_321.model` (the wide box whose
outer wall carries the hygrometer window). The window is a **through hole**, not
a blind pocket — the box's upper half is an open square frame:

| Feature | Value |
|---|---|
| Window opening | **43.16 × 43.16 mm** |
| Held full-size for | **12.75 mm** in from the outer face |
| Then a retaining shoulder (X only) | 41.80 mm, 0.68 mm per side |
| Shoulder run before the frame necks further | 5.30 mm |

**How the sensor is meant to sit.** It is pushed in from the *outer* face — the
one that shows out of the AMS — and stops against the shoulder. It cannot be
fitted from the lid side, where the opening is only 41.80 mm. A 12.5 mm-thick
Xiaomi in a 12.75 mm straight run therefore ends up **fully inserted, its face
flush with (a hair below) the outer surface**. Flush is the design intent; the
shoulder exists purely to stop the sensor being pushed on through into the AMS.

Anything on the sensor wider than the window — a bezel or lip — cannot enter the
hole at all; it would rest on the outer face and hold the sensor proud. That
turned out not to apply: the ZTH05's 43.30 mm is its widest point, bezel
included, so widening the window takes the whole sensor and no counterbore is
needed.

## Files

| File | Purpose |
|---|---|
| `modify_box.py` | **The rework.** Reads the donor 3mf, emits the ZTH05 sensor box |
| `test_modify_box.py` | Donor + rework invariants (pytest) |
| `create_gauge.py` | Fit-gauge generator (OCP, `../tools/step_primitives`) |
| `test_create_gauge.py` | Gauge invariants (pytest) |
| `ams2pro-zth05-fit-gauge.stl` | 2-tile fit gauge, rev 2 |
| `preview-sections.png` | Gauge top face and pocket section |

Regenerate: `../tools/venv/bin/python modify_box.py` → `ams2pro-sensor-box-zth05.stl`
Test: `../tools/venv/bin/python -m pytest -q`

`modify_box.py` and its tests read the donor 3mf from `~/Downloads` under
MakerWorld's download name (`SPILLPROOF+2+for+AMS+2+PRO_H2D_XIAOMI+UPPER.3mf`),
or pass the script a path; the gauge needs no donor. **Keep that file pristine —
print from a copy.** Saving it from Bambu Studio renumbers its objects, the box
stops being `object_321`, and the generator refuses it with that reason (as it
does an incomplete download).

The reworked box STL is **git-ignored on purpose**, as is
`preview-box-rework.png`, which plots the donor's own section beside the rework.
The donor is CC BY-NC-SA; `modify_box.py` is our work and is committed, but its
output is a derivative of AeonJoey's mesh, so it is generated locally rather than
redistributed here.

## The rework

Measured ZTH05: **43.30 × 43.30 × 10.50 mm**. Both numbers are wrong for the
donor box, in opposite directions:

| | Donor | ZTH05 | Problem |
|---|---|---|---|
| Window | 43.16 mm | 43.30 mm face | 0.14 mm too small — will not enter |
| Seat depth | 12.75 mm | 10.50 mm thick | would sink 2.25 mm below the surface |

So `modify_box.py` widens the window to **43.90 mm** and brings the stop forward
from 12.75 mm to **10.60 mm**, which puts the display 0.10 mm below flush — the
fit the donor gives a Xiaomi.

### Why 43.90 and not 43.60

Because nominal is not what comes off the plate. On the rev 1 tiles the 43.76 mm
window only *just* admitted the sensor and 43.56 mm would not, so this printer
and material lose **~0.45 mm** across a 43 mm opening — mostly first-layer
squish. 43.90 nominal lands at ~43.45 printed, leaving 0.15 mm on a 43.30 mm
sensor. A 43.60 window would have printed at ~43.15 and jammed, reproducing the
donor's original failure.

**That calibration transfers because the orientation matches.** The plate
transform for object id 4 maps model Y → plate Z: the box prints lying on its
back, outer face down on the bed, only 23 mm tall. Both window axes therefore
print in the XY plane — the same plane the flat gauge tiles cut theirs in.

Moving the stop is a *fuse*, not a cut. Cutting the wider window shallower would
leave the old 43.16 mm section as the stop, and a 43.30 mm sensor overlaps that
by 0.07 mm per side — nothing. Instead the donor's own 41.80 mm shoulder is
carried forward on rails, keeping **0.75 mm of overlap per side**. Like the
donor's shoulder they narrow X only, so the bay stays open front-to-back: air
reaches the sensor, and it pushes out from behind for a battery change or before
a dry cycle.

**This spends nearly the whole frame, and that is the design limit.** The donor
already runs thin — a 43.16 mm window in a 45.00 mm box leaves 0.92 mm of rim:

| Wall | Donor | Reworked |
|---|---|---|
| Side rim | 0.92 mm | **0.55 mm** — one extrusion |
| Divider under the window | 1.49 mm | 1.12 mm |
| Ceiling above the window | 2.32 mm | 1.95 mm |

A 0.55 mm rim is acceptable here because it is not a free-standing wall — it is
the box's own outer skin, continuous with the material above and below the
window and backed by the seat rails behind it. But 45.00 mm is the AMS bay and
cannot move, so **the window cannot grow much past this.** If a printed box
still will not take the sensor, the next lever is first-layer/elephant-foot
compensation in the slicer, not more width.

**Fitting it:** in Bambu Studio, on the *Front Row* plate, right-click the
45 × 23 × 93 mm `tinker.obj_2` — the thicker of the two objects sharing that
name — and replace it with the STL. Leave the `Desiccant_Boxes` print profile
alone.

## The gauge

### Rev 1 — printed 2026-08-31, width answered

Four 5 mm tiles at 43.16 / 43.36 / 43.56 / 43.76 mm. Result:

| Dots | Opening | Result |
|---|---|---|
| 1 | 43.16 mm (**unmodified donor**) | **would not admit the ZTH05** |
| 2 | 43.36 mm | body enters |
| 3 | 43.56 mm | body enters |
| 4 | 43.76 mm | body enters |

So **the donor boxes will not take a ZTH05 as they ship** — the window has to be
opened up by at least 0.20 mm. That is the one thing rev 1 could prove.

Rev 1 also had a defect: it modelled the full-size run as 3.69 mm when the donor
holds it for 12.75 mm. It tested width and nothing else. It could not show
whether the sensor seats to depth or finishes flush, and against a 3.69 mm tile
a bezel reads as "won't pass through" when in the real box the bezel would never
have gone in anyway.

### Rev 2 — depth-true, current

**Two separate 53.6 mm tiles** (113.1 × 53.6 mm of plate, **14.25 mm tall** =
12.75 mm pocket + 1.50 mm shoulder), reproducing the real insertion depth. Only
the widths still in play are reprinted; dot counts keep rev 1's meaning so the
two prints compare directly:

| Dots | Opening | vs donor |
|---|---|---|
| 2 | 43.36 mm | +0.20 |
| 3 | 43.56 mm | +0.40 |

Insert the sensor from the **top** face — it stands in for the box's outer face.

**Print the gauge in the same material as the boxes.** ASA shrinks roughly
twice as much as PLA on cooling, and holes shrink with the part — over 43 mm
that is ~0.1–0.15 mm, which is the entire clearance being measured. A PLA gauge
does not predict an ASA box.

It is separate tiles for the same reason: a single wide thin flat plate in ASA
warps, and a warped plate distorts the openings the gauge exists to measure.
Small tiles stay flat.

Flat as modelled, 0.2 mm layers, brim for ASA, no supports — the shoulder's
0.68 mm step bridges.

**Read it like this:** the tightest window that lets the ZTH05 slide down and
stop on the shoulder — with its face at or just below the tile's top surface —
is the pocket size to open the donor model up to.

What the gauge still does not answer:

- **It only steps larger.** FDM holes usually come out undersize, so the useful
  range is upward from the donor. If both windows are sloppy, the pocket wants
  *tightening* — regenerate with a negative `STEP` in `create_gauge.py`.
- **It has no counterbore.** Had the ZTH05's bezel been wider than the window,
  the sensor would have stood proud on every tile no matter how wide the window.
  Settled since: 43.30 mm is the bezel-inclusive width, so no recess is needed.

## How the box actually breathes

**Through the lid, not the front panel.** Checked against the mesh: the front
panel — the outward face, below the sensor window — has *no modelled holes
anywhere*, and it prints solid. That is correct and by design; it is the
"spillproof" outer face. Do not try to make it porous.

The lid (`tinker.obj_4`, a separate 44.96 × 5.40 × 100.80 mm part on the same
plate) carries two large features, and they do different jobs:

| Feature | Size | What it is |
|---|---|---|
| Over the sensor bay | ~35 × 41 mm | **a true through hole** — no material across the 5.4 mm |
| Over the desiccant | ~35 × 40 mm | a recess backed by a **1.79 mm wall** |

The sensor one must be open: the box's sensor bay is itself a through hole, so a
closed lid would seal the ZTH05 into a dead pocket reading its own box instead of
AMS air, with no way to push it out for a battery. The desiccant one is a thinned
panel, not a hole — thin enough to pass moisture, solid enough to hold the beads
in. That is the "spillproof" in the name.

A box without its lid printed is an open tray. Print the lids.

The `Desiccant_Boxes` profile still matters — `top_shell_layers = 0`,
`bottom_shell_layers = 0`, `wall_loops = 7`, `sparse_infill_density = 50%` grid —
but note `top_shell_thickness` is 1 mm, which re-solidifies any top-facing
surface regardless of the zero layer count. So the zero shells thin the box; they
are not what makes it breathe.

## What is on the plates

Nothing in this project is modelled as mesh — every part is a solid body, and the
only openings in the geometry are the lid windows. Sparse-vs-solid only exists
after slicing, so to see it: **Slice → Preview tab → drag the layer slider** to
the first few layers.

Tell the parts apart by **size**, not by look. Lids are 5.4 mm thin and 100.8 mm
long; boxes are 93 mm long and 18.2 or 23 mm thick.

| Plate | Object | Size (mm) | What it is |
|---|---|---|---|
| Front Row | `tinker.obj_2` | 45 × **23** × 93 | **the reworked sensor box** |
| Front Row | `tinker.obj_4` | 45 × 5.4 × 100.8 | **the vented lid that pairs with it** |
| Front Row | AMS2PRO Exporter-20 / -18 | 45 × 23 × 93 | plain wide boxes |
| Front Row | AMS2PRO Exporter-22 / -17 | 18 × 23 × 93 | narrow boxes |
| Front Row | AMS2PRO Exporter-24 ×2 | 45 × 5.4 × 100.8 | wide lids |
| Front Row | AMS2PRO Exporter-25 ×2 | 18 × 5.4 × 100.8 | narrow lids |
| Second Row | `tinker.obj_2` | 45 × **18.2** × 93 | *not* the sensor box — shallow variant |
| Second Row | everything else | — | same mix, 18.2 mm deep, no sensor |

Each plate is one complete row: **5 boxes + 5 lids**. The hygrometer window
exists on the Front Row `tinker.obj_2` only, so that is the plate to print for
the sensor — and note both plates contain an object called `tinker.obj_2`, so go
by the 23 mm thickness, not the name.

## Printing the actual boxes — the trap

**It ships sliced for an X1 Carbon**, 0.4 mm nozzle. The P2S shares the
256 × 256 bed so the plates fit, but switching printers in Bambu Studio can
silently reset the custom `Desiccant_Boxes` profile. Re-check its four values —
top and bottom shell layers 0, 7 wall loops, 50% grid infill — after the swap.
Replacing an object with an STL also drops its per-object `wall_loops = 4`
override, so re-apply that to the reworked box.

## Material and heat

Boxes print in **ASA**, so they survive the AMS 2 Pro dry cycle and can stay in
during drying.

The **sensor cannot**. Every candidate is rated to 50–60 °C and carries a
lithium coin cell; the dry cycle runs hotter. Pull the ZTH05 out of its box
before drying and leave the ASA boxes in place.

## Status

**2026-08-31.** Rev 1 gauge printed; the unmodified 43.16 mm window will not
admit a ZTH05. Sensor measured at 43.30 × 43.30 × 10.50 mm. Calibrated by
pushing the sensor face-first into the rev 1 tiles: only the 4-dot (43.76 mm)
admits it, the 3-dot (43.56 mm) does not, so the P2S loses ~0.45 mm across the
opening in ASA. Box reworked to **43.90 mm window / 10.60 mm seat** (see *Why
43.90 and not 43.60*). The next check is a printed box taking the sensor flush;
if it is still tight, go to first-layer compensation in the slicer, not a wider
window.

**2026-09-22.** The generator reads MakerWorld's download name, skips a re-saved
or incomplete copy when an original sits beside it, and otherwise refuses it with
the reason instead of failing with a `KeyError`. The seat and window cuts use
the shared `tools/mesh_shapes.centered_box`; output is unchanged.
