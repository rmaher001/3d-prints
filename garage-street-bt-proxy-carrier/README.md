# garage-street-bt-proxy-carrier

Internal carrier/sled + refillable desiccant basket that holds an **Olimex
ESP32-POE-ISO-EA (Rev M)** board vertically inside a length of **1.5″
Schedule-40 PVC *electrical* conduit**, for the outdoor street-facing BLE proxy
`garage-street-bt-proxy-poe`.

This is the *insides* only. The conduit, two end caps, and the cable grommet
are off-the-shelf (see Bill of materials).

## Why this shape

The enclosure is a vertical conduit stub, sealed cap **up**, cable grommet
**down**:

- **Board vertical**, RJ45/cable end **down** (meets the Ethernet coming up
  through the bottom grommet), U.FL antenna end **up**, facing the street.
- **3 perforated centering discs on a back spine** grip the 28 mm PCB through a
  slot, positioned on the clean PCB **above** the RJ45 so the whole
  RJ45 + plug + cable-bend region stays open below (not modeled — it's just air).
- **Axial flow holes** through every disc + the open bore keep drainage/airflow
  top→bottom, so the tube **breathes and sheds condensation** out the (snug but
  not potted) bottom grommet. No conformal coating is used, so this airflow is
  the moisture strategy, backed up by —
- **Desiccant basket** (perforated cup + friction lid) at the top. Holes are
  **smaller than the silica-gel beads** so loose beads stay put; the lid pulls
  off to re-bake/refill.

1.5″ conduit was chosen over 1.25″ specifically to leave ~6 mm of room around
the board for this carrier; at 1.25″ there's only ~3 mm and no room for a real
sled or basket.

## Board dimensions (verified)

98.15 × 28 × ~9 mm (taller only at the RJ45 end), confirmed against Olimex's
Rev J+ mechanical drawing — see `../olimex-esp32-poe-iso-ea-case/reference/`.
Hardware is mechanically identical Rev J→N.

## Files

| File | Purpose |
|---|---|
| `create_carrier.py` | Parametric generator (OCP/OpenCASCADE, `../tools/step_primitives`) |
| `test_create_carrier.py` | Fit/printability invariants (pytest) |
| `garage-street-bt-proxy-carrier.stl` | Sled + basket — **print 1** |
| `garage-street-bt-proxy-basket-lid.stl` | Friction lid — **print 2** |
| `preview-sections.png` | Cross-sections (verification) |

Regenerate: `../tools/venv/bin/python create_carrier.py`
Test: `../tools/venv/bin/python -m pytest test_create_carrier.py -q`

## Print

- **Material: PETG or ASA. Not PLA** — a capped conduit in direct sun gets hot
  enough to soften PLA and let the sled sag.
- **Orientation: vertical, as modeled (Z up).** Every feature (disc layers,
  axial holes, open-top cup) is support-free in this orientation.
- Tall, small footprint → **use a brim**. 20–30% infill, 3 walls.
- Print the **carrier first and dry-fit the bare board + a scrap of conduit**
  before printing the lid (same approach as the sibling case project).

## Bill of materials (off-the-shelf)

- ~180–190 mm of **1.5″ gray Sch-40 PVC electrical conduit** (UV-stabilized)
- 2× 1.5″ end caps — **top threaded/screw** (serviceable, not cemented), bottom
  drilled for the grommet
- 1× rubber cable **grommet** (reused from a UniFi Protect camera)
- Loose **silica-gel** beads (indicating type lets you see when spent)

## Assembly

1. Slide the PCB down into the carrier's disc slots (RJ45 end first / down).
2. Route the U.FL antenna up the wall via the basket's side notch (street side).
3. Fill the basket, press on the lid.
4. Drop the stack into the conduit; Ethernet up through the bottom grommet into
   the RJ45. Leave a **drip loop** in the cable below the entry.
5. Bottom grommet snug-but-not-potted (it's the drain/breather). **Seal the top
   cap; mount sealed-end-up, under cover.**

## Tunables (top of `create_carrier.py`)

| Param | Note |
|---|---|
| `FIT_CLEAR` | carrier OD = conduit ID − this; loosen/tighten the slip fit |
| `SLOT_CLEAR` | board ↔ slot, per side; tune to your printer's tolerance |
| `LID_CLEAR` | lid plug ↔ cup bore friction fit |
| `PERF_D` | **must be < your smallest silica bead** |
| `FLOW_D`, `FLOW_ANGLES` | open up if you want more drainage past the discs |
| `N_DISCS`, `BOTTOM_OVERHANG` | grip stations / how much board hangs below |

## Status

Design generated and dimensionally verified 2026-06-10; **not yet printed or
installed.**
