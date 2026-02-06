// USW-Pro-XG-8-PoE Cooling Stand v8 - KEEP IT SIMPLE
//
// From top to bottom:
//   Switch upside down on edge in a simple 2-wall cradle
//   ↓ cables hang down from ports
//   2" open gap - cables route out the sides
//   Fan shelf - 2x Noctua NF-A8 blow air up
//   4 bare legs on 2 thin floor rails
//
// Two-piece for P2S | PETG | 4 walls | 25% infill

$fn = 40;

/* [Switch] */
sw_w = 210.4;
sw_t = 43.7;

/* [Fans - Noctua NF-A8] */
fan = 80;
fan_holes = 71.5;
fan_screw = 4.3;
fan_cut = 76;
fan_gap = 10;

/* [Floor] */
rail_depth = 8;
rail_offset = 59;

/* [Key Heights] */
floor_clear = 155;
fan_shelf_z = 165;
cable_gap_h = 50;
shelf_t = 5;
cradle_z = fan_shelf_z + shelf_t + cable_gap_h;

/* [Cradle] */
clr = 1.5;
wall = 4;
slot_w = sw_t + clr * 2;
cradle_wall_h = 70;
slot_lip = 8;

/* [Platform] */
plat_w = sw_w + 16;
plat_d = fan + 20;

/* [Legs] */
leg_w = 30;
leg_d = rail_depth;
leg_x = plat_w/2 - leg_w/2 - 4;

/* [Split] */
split_z = 75;        // lower split = real legs on Part B
tenon_w = leg_w - 6;
tenon_d = rail_depth - 2;
tenon_h = 16;
tenon_clr = 0.3;
bolt_d = 4.5;

f1x = -(fan/2 + fan_gap/2);
f2x = (fan/2 + fan_gap/2);

module rr(w, d, h, r=2) {
    hull() for (dx=[-(w/2-r),(w/2-r)], dy=[-(d/2-r),(d/2-r)])
        translate([dx,dy,0]) cylinder(r=r,h=h);
}

module fan_cut() {
    translate([0,0,-1]) cylinder(d=fan_cut, h=shelf_t+2);
    for (dx=[-1,1], dy=[-1,1])
        translate([dx*fan_holes/2, dy*fan_holes/2, -1])
            cylinder(d=fan_screw, h=shelf_t+2);
}

module fan_boss() {
    for (dx=[-1,1], dy=[-1,1])
        translate([dx*fan_holes/2, dy*fan_holes/2, 0])
            cylinder(d=fan_screw+6, h=shelf_t);
}

// ============================================================
// PART A: Floor rails + 4 bare legs + tenons
// ============================================================
module part_a() {
    difference() {
        union() {
            for (s=[-1,1])
                translate([0, s*rail_offset, 0])
                    rr(plat_w, rail_depth, 4);
            for (lx=[-leg_x, leg_x], s=[-1,1])
                translate([lx, s*rail_offset, 0])
                    rr(leg_w, leg_d, split_z);
            for (lx=[-leg_x, leg_x], s=[-1,1])
                translate([lx, s*rail_offset, split_z])
                    rr(tenon_w, tenon_d, tenon_h, 1.5);
        }
        for (lx=[-leg_x, leg_x], s=[-1,1])
            translate([lx, s*rail_offset, split_z-8])
                cylinder(d=bolt_d, h=tenon_h+12);
    }
}

// ============================================================
// PART B: Upper legs + fan shelf + gap posts + simple cradle
// ============================================================
module part_b() {
    upper_h = fan_shelf_z - shelf_t - split_z;
    sz = upper_h;
    post = 8;
    post_z = sz + shelf_t;
    cz = post_z + cable_gap_h;
    
    sk_w = tenon_w + tenon_clr*2;
    sk_d = tenon_d + tenon_clr*2;
    sk_h = tenon_h + 1;
    
    difference() {
        union() {
            // Upper legs
            for (lx=[-leg_x, leg_x], s=[-1,1])
                translate([lx, s*rail_offset, 0])
                    rr(leg_w, leg_d, upper_h);
            
            // One brace (just below shelf, above 6" clearance)
            brace_local_z = upper_h - 4;
            for (lx=[-leg_x, leg_x])
                translate([lx-2, -rail_offset, brace_local_z])
                    cube([4, rail_offset*2, 10]);
            
            // Fan shelf
            translate([0, 0, sz])
                rr(plat_w, plat_d, shelf_t, 3);
            translate([f1x, 0, sz]) fan_boss();
            translate([f2x, 0, sz]) fan_boss();
            
            // 4 corner posts
            for (dx=[-1,1], dy=[-1,1])
                translate([dx*(sw_w/2), dy*(slot_w/2 + wall/2), post_z])
                    rr(post, post, cable_gap_h);
            
            // Cradle: two L-shaped walls + end stops
            // Each wall has a small inward lip the switch edge rests on
            // Center is wide open for cables to pass through
            lip = 10;  // how far lip extends inward from wall
            
            // Front wall
            translate([0, -(slot_w/2 + wall/2), cz])
                rr(sw_w + 10, wall, cradle_wall_h);
            // Front lip (extends inward)
            translate([0, -(slot_w/2 - lip/2), cz])
                rr(sw_w + 10, lip, wall);
            
            // Back wall
            translate([0, (slot_w/2 + wall/2), cz])
                rr(sw_w + 10, wall, cradle_wall_h);
            // Back lip (extends inward)
            translate([0, (slot_w/2 - lip/2), cz])
                rr(sw_w + 10, lip, wall);
            
            // End stops
            for (dx=[-1,1])
                translate([dx*(sw_w/2 + clr + wall/2), 0, cz])
                    rr(wall, slot_w + wall*2, slot_lip);
        }
        
        // Sockets
        for (lx=[-leg_x, leg_x], s=[-1,1])
            translate([lx, s*rail_offset, -1])
                rr(sk_w, sk_d, sk_h+1, 1.5);
        // Bolts
        for (lx=[-leg_x, leg_x], s=[-1,1])
            translate([lx, s*rail_offset, -1])
                cylinder(d=bolt_d, h=upper_h+shelf_t+5);
        // Fan cuts
        translate([f1x, 0, sz]) fan_cut();
        translate([f2x, 0, sz]) fan_cut();
    }
}

// ============================================================
color("SteelBlue") part_a();
color("DarkOrange") translate([0,0,split_z]) part_b();

// STL export - uncomment one:
// part_a();
// part_b();
