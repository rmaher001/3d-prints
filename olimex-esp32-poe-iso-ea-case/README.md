# olimex-esp32-poe-iso-ea-case

3D-printed case for the **Olimex ESP32-POE-ISO-EA Rev M** board (external-antenna variant). Used as a Bluetooth proxy in a Home Assistant setup.

## Source

[Thingiverse 6227294](https://www.thingiverse.com/thing:6227294) — "Case for Olimex ESP32-POE-ISO-EA Rev J and newer" by fddvxzcv.

Single STL containing both halves (box + lid laid out side-by-side for one print job). Friction-fit lid. PCB retained by two through-hole spacer posts. Includes:
- Round SMA bulkhead cutout (one short end)
- RJ45 cutout (opposite short end)
- Micro-USB slot (long side)
- Top ventilation slots over DC-DC converter and ESP32 module

## Files

| File | Purpose |
|---|---|
| `olimex-esp32-poe-iso-ea-case.stl` | The print file (box + lid, one job) |
| `render-box-and-lid.png` | Render showing the two halves |
| `build-photo-finished.jpg` | Reference photo of a completed working unit |
| `SOURCE-README.txt` | Original README from the Thingiverse ZIP |
| `LICENSE.txt` | Original license from the Thingiverse ZIP |
| `reference/olimex-rev-J-and-newer-dimensions.pdf` | Authoritative Olimex mechanical drawing (Rev J+, covers M) |
| `reference/olimex-esp32-poe-iso-rev-M-schematic.pdf` | Rev M schematic from OLIMEX GitHub |
| `reference/olimex-official-ea-case-v12.stl` | Olimex's official `-EA` case STL (larger fallback) |
| `reference/olimex-official-ea-case-drawing.pdf` | Drawing for the official Olimex case |

## Dry-fit verification (2026-05-13)

Verified dimensionally against Olimex's authoritative Rev J+ drawing (`reference/olimex-rev-J-and-newer-dimensions.pdf`):

| | Board (Rev M) | Case cavity | Headroom |
|---|---|---|---|
| Length | 98.15 mm | ~110 mm | +11.85 mm |
| Width | 28 mm | ~49.5 mm | +21.5 mm |
| Height | ~9 mm | ~22 mm | ample |

- Olimex hardware changelog: **zero mechanical changes Rev J → Rev N.** Mounting holes, RJ45, USB, u.FL — identical positions across J/K/L/M/N. STL filename declares Rev K target; geometrically identical to M.
- Case uses through-hole spacer-post retention, not edge clamping — so component-near-edge concerns ("not enough lip") do not apply.
- Build photo (`build-photo-finished.jpg`) shows the same STL printed and working with a `-EA` board, SMA bulkhead, and ethernet.

## Print recommendation

- Material: **PETG** (better thermal headroom than PLA for the PoE chip)
- Orientation: as laid out in the STL (box hollow-up, lid flat alongside)
- Infill: 20–30%
- Print the base only first, dry-fit the bare board, then commit to the lid

## Open items requiring physical print to verify

1. SMA bulkhead diameter match (STL sized for standard ~6.5 mm threaded barrel)
2. FDM tolerance at the spacer posts (printer-specific, ~0.2–0.4 mm expected)
3. Lid friction-fit tightness

If any need an STL mod, the source remains `olimex-esp32-poe-iso-ea-case.stl`; modifications produce sibling versioned files (`*.v2.stl`, etc.) plus a `modify_*.py` script — same pattern as `../esp32-c6-c4001-enclosure/` in this repo.
