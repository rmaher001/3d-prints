import numpy as np
from stl import mesh

def make_box(w, d, h, cx=0, cy=0, cz=0):
    """Create a box mesh centered at cx,cy with bottom at cz.
    w=X width, d=Y depth, h=Z height"""
    x0, x1 = cx - w/2, cx + w/2
    y0, y1 = cy - d/2, cy + d/2
    z0, z1 = cz, cz + h
    
    verts = np.array([
        [x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],  # bottom
        [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],  # top
    ])
    
    # 12 triangles (2 per face)
    faces = np.array([
        [0,2,1],[0,3,2],  # bottom
        [4,5,6],[4,6,7],  # top
        [0,1,5],[0,5,4],  # front
        [2,3,7],[2,7,6],  # back
        [0,4,7],[0,7,3],  # left
        [1,2,6],[1,6,5],  # right
    ])
    
    m = mesh.Mesh(np.zeros(12, dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[f[j]]
    return m

def make_cylinder(r, h, cx=0, cy=0, cz=0, n=32):
    """Cylinder centered at cx,cy with bottom at cz"""
    angles = np.linspace(0, 2*np.pi, n+1)[:-1]
    faces_list = []
    
    for i in range(n):
        a1, a2 = angles[i], angles[(i+1)%n]
        x1b, y1b = cx + r*np.cos(a1), cy + r*np.sin(a1)
        x2b, y2b = cx + r*np.cos(a2), cy + r*np.sin(a2)
        x1t, y1t = x1b, y1b
        x2t, y2t = x2b, y2b
        
        # Bottom triangle
        faces_list.append([[cx,cy,cz],[x2b,y2b,cz],[x1b,y1b,cz]])
        # Top triangle
        faces_list.append([[cx,cy,cz+h],[x1t,y1t,cz+h],[x2t,y2t,cz+h]])
        # Side quad (2 triangles)
        faces_list.append([[x1b,y1b,cz],[x2b,y2b,cz],[x2t,y2t,cz+h]])
        faces_list.append([[x1b,y1b,cz],[x2t,y2t,cz+h],[x1t,y1t,cz+h]])
    
    m = mesh.Mesh(np.zeros(len(faces_list), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces_list):
        for j in range(3):
            m.vectors[i][j] = f[j]
    return m

def combine(meshes):
    return mesh.Mesh(np.concatenate([m.data for m in meshes]))

# ============================================================
# DIMENSIONS - exactly matching the React viewer
# ============================================================
SW_W = 210.4
SW_T = 43.7
FAN = 80
RAIL_DEPTH = 8
RAIL_OFFSET = 59
PLAT_W = SW_W + 16       # 226.4
PLAT_D = FAN + 20        # 100
FLOOR_CLEAR = 155
SHELF_Z = 165
SHELF_T = 5
WALL = 4
CLR = 1.5
SLOT_W = SW_T + CLR * 2  # 46.7
LEG_W = 30
LEG_X = PLAT_W/2 - LEG_W/2 - 4  # 109.2
CABLE_GAP = 50
LIP = 10
WALL_H = 70
CRADLE_Z = SHELF_Z + SHELF_T + CABLE_GAP  # 220

FAN_GAP = 10
F1X = -(FAN/2 + FAN_GAP/2)  # -45
F2X = FAN/2 + FAN_GAP/2     # 45

POST = 8
SLOT_LIP = 8

# ============================================================
# BUILD FULL MODEL (matching React viewer exactly)
# ============================================================
parts = []

# --- FLOOR RAILS ---
for s in [-1, 1]:
    parts.append(make_box(PLAT_W, RAIL_DEPTH, 4, 0, s*RAIL_OFFSET, 0))

# --- 4 LEGS ---
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        parts.append(make_box(LEG_W, RAIL_DEPTH, FLOOR_CLEAR, lx, s*RAIL_OFFSET, 0))

# --- BRACE ---
brace_z = FLOOR_CLEAR + (SHELF_Z - SHELF_T - FLOOR_CLEAR) / 2
for lx in [-LEG_X, LEG_X]:
    parts.append(make_box(4, RAIL_OFFSET*2, 10, lx, 0, brace_z))

# --- FAN SHELF ---
parts.append(make_box(PLAT_W, PLAT_D, SHELF_T, 0, 0, SHELF_Z - SHELF_T))

# --- FAN HOLES (cut as recessed cylinders - skip for now, holes in shelf) ---
# We'll represent fan mounting bosses instead
for fx in [F1X, F2X]:
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            # Screw boss
            parts.append(make_cylinder(5, SHELF_T, fx + dx*71.5/2, dy*71.5/2, SHELF_Z - SHELF_T, 16))

# --- CORNER POSTS ---
for dx in [-1, 1]:
    for dy in [-1, 1]:
        parts.append(make_box(POST, POST, CABLE_GAP, 
                              dx*(SW_W/2), dy*(SLOT_W/2 + WALL/2), SHELF_Z))

# --- CRADLE FRONT WALL ---
parts.append(make_box(SW_W + 10, WALL, WALL_H, 0, -(SLOT_W/2 + WALL/2), CRADLE_Z))

# --- CRADLE BACK WALL ---
parts.append(make_box(SW_W + 10, WALL, WALL_H, 0, (SLOT_W/2 + WALL/2), CRADLE_Z))

# --- FRONT LIP ---
parts.append(make_box(SW_W + 10, LIP, WALL, 0, -(SLOT_W/2 - LIP/2), CRADLE_Z))

# --- BACK LIP ---
parts.append(make_box(SW_W + 10, LIP, WALL, 0, (SLOT_W/2 - LIP/2), CRADLE_Z))

# --- END STOPS ---
for dx in [-1, 1]:
    parts.append(make_box(WALL, SLOT_W + WALL*2, SLOT_LIP,
                          dx*(SW_W/2 + CLR + WALL/2), 0, CRADLE_Z))

# ============================================================
# COMBINE AND SAVE FULL MODEL
# ============================================================
full = combine(parts)
full.save('/home/claude/v8_full.stl')
print(f"Full model saved: {len(full.data)} triangles")

# ============================================================
# SPLIT INTO TWO PARTS
# ============================================================
SPLIT_Z = 75  # split at 75mm

# Part A: everything below split_z (trimmed)
part_a_meshes = []
# Rails
for s in [-1, 1]:
    part_a_meshes.append(make_box(PLAT_W, RAIL_DEPTH, 4, 0, s*RAIL_OFFSET, 0))
# Lower legs (0 to split_z)
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        part_a_meshes.append(make_box(LEG_W, RAIL_DEPTH, SPLIT_Z, lx, s*RAIL_OFFSET, 0))
# Tenons
TENON_W = LEG_W - 6
TENON_D = RAIL_DEPTH - 2
TENON_H = 16
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        part_a_meshes.append(make_box(TENON_W, TENON_D, TENON_H, lx, s*RAIL_OFFSET, SPLIT_Z))

part_a = combine(part_a_meshes)
part_a.save('/home/claude/v8_part_a.stl')
print(f"Part A saved: {len(part_a.data)} triangles, height={SPLIT_Z+TENON_H}mm")

# Part B: everything above split_z, shifted down so bottom is at z=0
part_b_meshes = []
upper_leg_h = FLOOR_CLEAR - SPLIT_Z  # 80mm of leg above split

# Sockets (negative space conceptual - we just start legs from 0)
# Upper legs
for lx in [-LEG_X, LEG_X]:
    for s in [-1, 1]:
        part_b_meshes.append(make_box(LEG_W, RAIL_DEPTH, upper_leg_h, lx, s*RAIL_OFFSET, 0))

# Brace (shifted down by SPLIT_Z)
local_brace_z = brace_z - SPLIT_Z
for lx in [-LEG_X, LEG_X]:
    part_b_meshes.append(make_box(4, RAIL_OFFSET*2, 10, lx, 0, local_brace_z))

# Fan shelf
local_shelf_z = SHELF_Z - SHELF_T - SPLIT_Z
part_b_meshes.append(make_box(PLAT_W, PLAT_D, SHELF_T, 0, 0, local_shelf_z))

# Fan screw bosses
for fx in [F1X, F2X]:
    for dx in [-1, 1]:
        for dy in [-1, 1]:
            part_b_meshes.append(make_cylinder(5, SHELF_T, fx + dx*71.5/2, dy*71.5/2, local_shelf_z, 16))

# Corner posts
local_shelf_top = SHELF_Z - SPLIT_Z
for dx in [-1, 1]:
    for dy in [-1, 1]:
        part_b_meshes.append(make_box(POST, POST, CABLE_GAP,
                                      dx*(SW_W/2), dy*(SLOT_W/2 + WALL/2), local_shelf_top))

# Cradle
local_cradle_z = CRADLE_Z - SPLIT_Z
# Front wall
part_b_meshes.append(make_box(SW_W + 10, WALL, WALL_H, 0, -(SLOT_W/2 + WALL/2), local_cradle_z))
# Back wall
part_b_meshes.append(make_box(SW_W + 10, WALL, WALL_H, 0, (SLOT_W/2 + WALL/2), local_cradle_z))
# Front lip
part_b_meshes.append(make_box(SW_W + 10, LIP, WALL, 0, -(SLOT_W/2 - LIP/2), local_cradle_z))
# Back lip
part_b_meshes.append(make_box(SW_W + 10, LIP, WALL, 0, (SLOT_W/2 - LIP/2), local_cradle_z))
# End stops
for dx in [-1, 1]:
    part_b_meshes.append(make_box(WALL, SLOT_W + WALL*2, SLOT_LIP,
                                  dx*(SW_W/2 + CLR + WALL/2), 0, local_cradle_z))

part_b = combine(part_b_meshes)
part_b.save('/home/claude/v8_part_b.stl')
print(f"Part B saved: {len(part_b.data)} triangles, height={CRADLE_Z - SPLIT_Z + WALL_H}mm")
print(f"\nAssembled: Part A on floor, Part B placed at z={SPLIT_Z}")
print(f"Total height to top of cradle walls: {CRADLE_Z + WALL_H}mm ({(CRADLE_Z+WALL_H)/25.4:.1f}\")")
