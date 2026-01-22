# Apollo R-PRO-1 Case Modifications

Custom 3D printed case modifications for the Apollo Automation R-PRO-1 mmWave sensor.

## Light Sensor Modification

The stock FDM case blocks the **LTR390** illuminance sensor (U12). These modified cases add light slots to allow proper light measurement.

### Files

| File | Description |
|------|-------------|
| `r_pro-1_case-v2_DUAL_slots.step` | **Recommended** - Dual 40mm × 10mm slots (front + top) |
| `r_pro-1_case-v2_FRONT_slot.step` | Single slot on front face only |
| `r_pro-1_case-v2_with_light_slot.step` | Original smaller slot (36.5mm × 4mm) |

### Dual Slot Specifications (Recommended)

- **Slot 1 (Front face)**: 40mm wide × 10mm tall, positioned near top edge
- **Slot 2 (Top face)**: 40mm wide × 10mm tall, positioned near front edge
- Both slots centered horizontally

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
