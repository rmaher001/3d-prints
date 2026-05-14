import sys
sys.path.insert(0, "/Users/richard/3d-prints/tools")
from mesh_primitives import make_box, make_cylinder, make_ring, combine, flip_z

# ============================================================
# DIMENSIONS
# ============================================================
SW_W = 210.4
SW_T = 43.7
FAN = 80
RAIL_DEPTH = 8
RAIL_OFFSET = 59
PLAT_W = SW_W + 16
PLAT_D = FAN + 20
FLOOR_CLEAR = 155
SHELF_Z = 165
SHELF_T = 5
WALL = 4
CLR = 1.5
SLOT_W = SW_T + CLR * 2
LEG_W = 30
LEG_X = PLAT_W/2 - LEG_W/2 - 4
CABLE_GAP = 50
LIP = 10
WALL_H = 70
CRADLE_Z = SHELF_Z + SHELF_T + CABLE_GAP
FAN_GAP = 10
F1X = -(FAN/2 + FAN_GAP/2)
F2X = FAN/2 + FAN_GAP/2
POST = 8
SLOT_LIP = 8
SPLIT_Z = 75
TENON_W = LEG_W - 6
TENON_D = RAIL_DEPTH - 2
TENON_H = 16
FAN_CUT_R = 76/2  # fan cutout radius
FAN_SCREW_SPACING = 71.5
FAN_SCREW_R = 4.3/2

# ============================================================
# PART A (unchanged - legs + rails + tenons)
# ============================================================
part_a_meshes = []
for s in [-1, 1]:
    part_a_meshes.append(make_box(PLAT_W, RAIL_DEPTH, 4, 0, s*RAIL_OFFSET, 0))
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        part_a_meshes.append(make_box(LEG_W, RAIL_DEPTH, SPLIT_Z, lx, s*RAIL_OFFSET, 0))
        part_a_meshes.append(make_box(TENON_W, TENON_D, TENON_H, lx, s*RAIL_OFFSET, SPLIT_Z))

part_a = combine(part_a_meshes)
part_a.save('/home/claude/v8_part_a.stl')
print(f"Part A: {SPLIT_Z + TENON_H}mm tall")

# ============================================================
# PART B - built in ASSEMBLY orientation then flipped for printing
# (z=0 at split point, everything goes UP)
# ============================================================
pb = []

# Upper legs: from split point up to shelf
upper_leg_h = SHELF_Z - SHELF_T - SPLIT_Z  # 85mm
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        pb.append(make_box(LEG_W, RAIL_DEPTH, upper_leg_h, lx, s*RAIL_OFFSET, 0))

# Brace at midpoint of upper legs
brace_z = upper_leg_h / 2
for lx in [-LEG_X, LEG_X]:
    pb.append(make_box(4, RAIL_OFFSET*2, 10, lx, 0, brace_z))

# Fan shelf - built as a plate with fan holes
# Instead of a solid plate, build it as strips around the fan holes
shelf_z = upper_leg_h  # local z of shelf bottom

# Build shelf as the solid plate
pb.append(make_box(PLAT_W, PLAT_D, SHELF_T, 0, 0, shelf_z))

# Fan hole rings (these sit ON the shelf to form the screw bosses
# and visually indicate where fans mount)
for fx in [F1X, F2X]:
    # Ring around each fan hole
    pb.append(make_ring(FAN_CUT_R + 4, FAN_CUT_R, SHELF_T, fx, 0, shelf_z, 48))
    # Screw bosses
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            pb.append(make_cylinder(FAN_SCREW_R + 3, SHELF_T,
                                   fx + dx*FAN_SCREW_SPACING/2,
                                   dy*FAN_SCREW_SPACING/2,
                                   shelf_z, 16))

# Corner posts (cable gap)
shelf_top = shelf_z + SHELF_T
for dx in [-1, 1]:
    for dy in [-1, 1]:
        pb.append(make_box(POST, POST, CABLE_GAP,
                          dx*(SW_W/2), dy*(SLOT_W/2 + WALL/2), shelf_top))

# Cradle
cz = shelf_top + CABLE_GAP
# Front wall
pb.append(make_box(SW_W + 10, WALL, WALL_H, 0, -(SLOT_W/2 + WALL/2), cz))
# Back wall
pb.append(make_box(SW_W + 10, WALL, WALL_H, 0, (SLOT_W/2 + WALL/2), cz))
# Front lip
pb.append(make_box(SW_W + 10, LIP, WALL, 0, -(SLOT_W/2 - LIP/2), cz))
# Back lip
pb.append(make_box(SW_W + 10, LIP, WALL, 0, (SLOT_W/2 - LIP/2), cz))
# End stops
for dx in [-1, 1]:
    pb.append(make_box(WALL, SLOT_W + WALL*2, SLOT_LIP,
                      dx*(SW_W/2 + CLR + WALL/2), 0, cz))

# Combine in assembly orientation
part_b_assembly = combine(pb)

# Total height of part B
total_b_h = cz + WALL_H
print(f"Part B assembly orientation: {total_b_h:.0f}mm tall")

# Now flip for printing: cradle goes on build plate, legs point UP
# This way when you flip it over for assembly, legs point DOWN
part_b_print = flip_z(part_b_assembly, total_b_h)
part_b_print.save('/home/claude/v8_part_b.stl')
print(f"Part B flipped for printing: cradle at bottom, legs pointing up")
print(f"  -> When assembled, flip over so legs go into Part A")

# ============================================================
# FULL MODEL (for reference)
# ============================================================
full_parts = []
# Part A at z=0
for s in [-1, 1]:
    full_parts.append(make_box(PLAT_W, RAIL_DEPTH, 4, 0, s*RAIL_OFFSET, 0))
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        full_parts.append(make_box(LEG_W, RAIL_DEPTH, FLOOR_CLEAR, lx, s*RAIL_OFFSET, 0))

brace_z_full = FLOOR_CLEAR + (SHELF_Z - SHELF_T - FLOOR_CLEAR) / 2
for lx in [-LEG_X, LEG_X]:
    full_parts.append(make_box(4, RAIL_OFFSET*2, 10, lx, 0, brace_z_full))

full_parts.append(make_box(PLAT_W, PLAT_D, SHELF_T, 0, 0, SHELF_Z - SHELF_T))
for fx in [F1X, F2X]:
    full_parts.append(make_ring(FAN_CUT_R + 4, FAN_CUT_R, SHELF_T, fx, 0, SHELF_Z - SHELF_T, 48))
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            full_parts.append(make_cylinder(FAN_SCREW_R + 3, SHELF_T,
                                           fx + dx*FAN_SCREW_SPACING/2,
                                           dy*FAN_SCREW_SPACING/2,
                                           SHELF_Z - SHELF_T, 16))

for dx in [-1, 1]:
    for dy in [-1, 1]:
        full_parts.append(make_box(POST, POST, CABLE_GAP,
                                  dx*(SW_W/2), dy*(SLOT_W/2 + WALL/2), SHELF_Z))

full_parts.append(make_box(SW_W + 10, WALL, WALL_H, 0, -(SLOT_W/2 + WALL/2), CRADLE_Z))
full_parts.append(make_box(SW_W + 10, WALL, WALL_H, 0, (SLOT_W/2 + WALL/2), CRADLE_Z))
full_parts.append(make_box(SW_W + 10, LIP, WALL, 0, -(SLOT_W/2 - LIP/2), CRADLE_Z))
full_parts.append(make_box(SW_W + 10, LIP, WALL, 0, (SLOT_W/2 - LIP/2), CRADLE_Z))
for dx in [-1, 1]:
    full_parts.append(make_box(WALL, SLOT_W + WALL*2, SLOT_LIP,
                              dx*(SW_W/2 + CLR + WALL/2), 0, CRADLE_Z))

full = combine(full_parts)
full.save('/home/claude/v8_full.stl')
print(f"\nFull model: {CRADLE_Z + WALL_H}mm tall ({(CRADLE_Z+WALL_H)/25.4:.1f}\")")
