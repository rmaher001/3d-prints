# Apollo R-PRO-1 Case Modifications

Custom 3D printed case modifications for the Apollo Automation R-PRO-1 mmWave sensor.

## Light Sensor Modification

The stock FDM case blocks the **LTR390** illuminance sensor (U12). These modified cases add light slots to allow proper light measurement.

### Files

| File | Description |
|------|-------------|
| `r_pro-1_case-v2_DUAL_slots.step` | **Recommended** - Dual 40mm × 10mm slots (front + top) |
| `r_pro-1_lens_cover.step` | Press-fit translucent lens cover for light slots (print 2) |
| `r_pro-1_case-v2_FRONT_slot.step` | Single slot on front face only |
| `r_pro-1_case-v2_with_light_slot.step` | Original smaller slot (36.5mm × 4mm) |

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
