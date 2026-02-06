import numpy as np
from stl import mesh
import copy

def make_box(w, d, h, cx=0, cy=0, cz=0):
    x0, x1 = cx - w/2, cx + w/2
    y0, y1 = cy - d/2, cy + d/2
    z0, z1 = cz, cz + h
    verts = np.array([
        [x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
        [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],
    ])
    faces = np.array([
        [0,2,1],[0,3,2],[4,5,6],[4,6,7],
        [0,1,5],[0,5,4],[2,3,7],[2,7,6],
        [0,4,7],[0,7,3],[1,2,6],[1,6,5],
    ])
    m = mesh.Mesh(np.zeros(12, dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[f[j]]
    return m

def make_cylinder(r, h, cx=0, cy=0, cz=0, n=32):
    faces_list = []
    angles = np.linspace(0, 2*np.pi, n+1)[:-1]
    for i in range(n):
        a1, a2 = angles[i], angles[(i+1)%n]
        x1, y1 = cx + r*np.cos(a1), cy + r*np.sin(a1)
        x2, y2 = cx + r*np.cos(a2), cy + r*np.sin(a2)
        faces_list.append([[cx,cy,cz],[x2,y2,cz],[x1,y1,cz]])
        faces_list.append([[cx,cy,cz+h],[x1,y1,cz+h],[x2,y2,cz+h]])
        faces_list.append([[x1,y1,cz],[x2,y2,cz],[x2,y2,cz+h]])
        faces_list.append([[x1,y1,cz],[x2,y2,cz+h],[x1,y1,cz+h]])
    m = mesh.Mesh(np.zeros(len(faces_list), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces_list):
        for j in range(3):
            m.vectors[i][j] = f[j]
    return m

def make_ring(r_outer, r_inner, h, cx=0, cy=0, cz=0, n=48):
    """Cylinder with a hole - for fan shelf around fan cutouts"""
    faces_list = []
    angles = np.linspace(0, 2*np.pi, n+1)[:-1]
    for i in range(n):
        a1, a2 = angles[i], angles[(i+1)%n]
        ox1, oy1 = cx + r_outer*np.cos(a1), cy + r_outer*np.sin(a1)
        ox2, oy2 = cx + r_outer*np.cos(a2), cy + r_outer*np.sin(a2)
        ix1, iy1 = cx + r_inner*np.cos(a1), cy + r_inner*np.sin(a1)
        ix2, iy2 = cx + r_inner*np.cos(a2), cy + r_inner*np.sin(a2)
        # Top face (annular segment)
        faces_list.append([[ox1,oy1,cz+h],[ox2,oy2,cz+h],[ix2,iy2,cz+h]])
        faces_list.append([[ox1,oy1,cz+h],[ix2,iy2,cz+h],[ix1,iy1,cz+h]])
        # Bottom face
        faces_list.append([[ox2,oy2,cz],[ox1,oy1,cz],[ix1,iy1,cz]])
        faces_list.append([[ox2,oy2,cz],[ix1,iy1,cz],[ix2,iy2,cz]])
        # Outer wall
        faces_list.append([[ox1,oy1,cz],[ox2,oy2,cz],[ox2,oy2,cz+h]])
        faces_list.append([[ox1,oy1,cz],[ox2,oy2,cz+h],[ox1,oy1,cz+h]])
        # Inner wall
        faces_list.append([[ix2,iy2,cz],[ix1,iy1,cz],[ix1,iy1,cz+h]])
        faces_list.append([[ix2,iy2,cz],[ix1,iy1,cz+h],[ix2,iy2,cz+h]])
    m = mesh.Mesh(np.zeros(len(faces_list), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces_list):
        for j in range(3):
            m.vectors[i][j] = f[j]
    return m

def combine(meshes):
    return mesh.Mesh(np.concatenate([m.data for m in meshes]))

def flip_z(m, max_z):
    """Flip a mesh upside down around max_z/2"""
    flipped = mesh.Mesh(m.data.copy())
    flipped.vectors[:,:,2] = max_z - flipped.vectors[:,:,2]
    # Fix normals by swapping vertex order
    for i in range(len(flipped.vectors)):
        flipped.vectors[i] = flipped.vectors[i][::-1]
    return flipped

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
