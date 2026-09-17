# Apollo R-PRO-1 Case Modifications

Custom 3D printed case modifications for the Apollo Automation R-PRO-1 mmWave sensor.

## Light Sensor Modification

The stock FDM case blocks the **LTR390** illuminance sensor (U12). These modified cases add light slots to allow proper light measurement.

### Files

| File | Description |
|------|-------------|
| `r_pro-1_case-v2_DUAL_slots.step` | **Recommended** - Dual 40mm × 10mm slots (front + top) |
| `r_pro-1_lens_cover_loose.step` | Translucent lens cover, 0.1mm clearance per side (print 2) |
| `r_pro-1_lens_cover_press.step` | Translucent lens cover, -0.04mm interference fit, for 100.7% XY scale (print 2) |
| `r_pro-1_case-v2_FRONT_slot.step` | Single slot on front face only |
| `r_pro-1_case-v2_with_light_slot.step` | Original smaller slot (36.5mm × 4mm) |
| `r_pro-1_standing_case.stl` | **One-piece standing case** — the case with a 20 mm vented foot built in, already at 100.5% |
| `create_standing_case.py` | Generator for the standing case (covered by `test_standing_case.py`) |

### Fit

The PCB is 57.2 x 44.8 mm. It goes in through the open back past the rim snap lip and rests on the ledges on the long walls (tips 54.8 mm apart). The rim lip opening along the length is 56.63 mm at 100%, 0.29 mm per side narrower than the board. That print is too tight, and the board is hard to get out. At 101% XY the opening is 57.20 mm, the same as the board, so it doesn't catch the board at all. Print the case **and** the lid at **100.5% X/Y, 100% Z**: the opening is 56.91 mm (about 0.15 mm per side of snap), and the lid scales with the lip so its snap is unchanged. Width is not the issue, since the lip opening across the width is 45.65 mm at 100% against a 44.8 mm board. The lid STL will not print as downloaded. It stands on two small board-hold tabs (about 20 mm² of bed contact), and its outer face is covered in 0.5 mm dimples, so flipped over only about 880 mm² of webbing touches the plate. Both ways end in spaghetti, and the dimples also make it a 1.1M-triangle mesh. Fill the dimples solid (a 0.7 mm slab under the 1 mm plate, taken from the plate's own outline) and print it outer face down. That gives 2,230 mm² of contact and about 1,200 triangles; everything above the plate is unchanged.

### Dual Slot Specifications (Recommended)

- **Slot 1 (Front face)**: 40mm wide × 10mm tall, positioned near top edge
- **Slot 2 (Top face)**: 40mm wide × 10mm tall, positioned near front edge
- Both slots centered horizontally

### Lens Cover Specifications

Press-fit translucent covers for the dual light slots. Print 2 (one per slot).

```
        ┌────────────────────────────┐
        │     Outer Flange (lip)     │  42mm x 12mm x 0.8mm
        │  ┌──────────────────────┐  │
        │  │   Insert Body        │  │  39.8mm x 9.8mm x 2.0mm
        │  │   (press-fits into   │  │
        │  │    slot opening)     │  │
        │  └──────────────────────┘  │
        └────────────────────────────┘
```

- **Flange**: 42mm × 12mm × 0.8mm (1mm lip per side, sits flush on case exterior)
- **Insert body**: 39.8mm × 9.8mm × 2.0mm (0.1mm clearance per side)
- **Total depth**: 2.8mm

**Print settings:**
- **Filament**: Translucent PLA or PETG
- **Orientation**: Flange face down on build plate
- **Infill**: 100% (solid for even light transmission)
- **Layer height**: 0.12–0.16mm for smooth finish
- **Quantity**: 2 (one for each slot)

**Tolerance tuning:** Edit the variables at the top of `tools/create_lens.py` and regenerate the STEP file. Increase `CLEARANCE` if the fit is too tight, decrease if too loose.

## Standing Case

`r_pro-1_standing_case.stl` is the case and its stand as one part, for a sensor sitting upright on a surface with the light slots at the top.

- The bottom end grows 20 mm: side walls (1.75 mm) and front wall (2 mm) carry on down, each with the case's own rounded vent slots.
- The back of that skirt is open, so the eight vent slots in the bottom of the case exhaust into it and out the back.
- The base plate is solid, 3 mm, rounded back corners, running 30 mm behind the case so an 82 mm tall part does not tip.
- Whole part: 51.2 wide x 82.2 tall x 54 deep, 22.3 cm3. Prints face down, no supports. Lens covers and the lid are unchanged.

Regenerate with `../tools/venv/bin/python create_standing_case.py`.

### Sensor Info

- **Sensor**: LTR390 (U12 on PCB)
- **Location**: Top right corner of PCB, 0.5mm from edge
- **Function**: Measures ambient light in lux

### Base Model

Modified from: [Apollo Automation R-PRO-1 FDM Case](https://www.printables.com/model/1349076-apollo-automation-r-pro-1-fdm-case) by chuyskywalker

Original case by Apollo Automation (no dimples version for FDM printing).

## Testing Results

| Configuration | Lux Range |
|--------------|-----------|
| Naked PCB (no case) | 0-170 lux |
| Single small slot | 0-20 lux |
| Dual large slots | Comparable to commercial sensors |

## License

Based on original Apollo Automation design (CC BY-NC-SA).
