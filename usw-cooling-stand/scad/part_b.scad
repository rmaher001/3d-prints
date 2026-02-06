$fn = 48;

// Dimensions matching the React viewer
sw_w = 210.4;
sw_t = 43.7;
fan = 80;
rail_depth = 8;
rail_offset = 59;
plat_w = sw_w + 16;
plat_d = rail_offset*2 + rail_depth + 4;  // 130mm - reaches the legs
shelf_t = 5;
wall = 4;
clr = 1.5;
slot_w = sw_t + clr * 2;
leg_w = 30;
leg_x = plat_w/2 - leg_w/2 - 4;
cable_gap = 50;
lip = 10;
wall_h = 70;
fan_gap = 10;
f1x = -(fan/2 + fan_gap/2);
f2x = fan/2 + fan_gap/2;
slot_lip = 8;
fan_cut_r = 76/2;
fan_hole_spacing = 71.5;
fan_screw_d = 4.3;

// Split / connection
split_z = 75;
shelf_z_local = 165 - 5 - split_z;    // 85mm - shelf bottom
shelf_top_local = shelf_z_local + shelf_t;  // 90mm
cradle_z_local = shelf_top_local + cable_gap;  // 140mm

// Legs now extend all the way to the shelf
leg_h = shelf_z_local;  // 85mm - legs meet shelf directly

// Corner posts beefed up
post_w = 15;   // wider posts
post_d = 10;

// Tenon socket
tenon_w = leg_w - 6;
tenon_d = rail_depth - 2;
tenon_h = 16;
tenon_clr = 0.3;
socket_w = tenon_w + tenon_clr * 2;
socket_d = tenon_d + tenon_clr * 2;
socket_h = tenon_h + 1;

module rr(w, d, h, r=2) {
    hull() for (dx=[-(w/2-r),(w/2-r)], dy=[-(d/2-r),(d/2-r)])
        translate([dx,dy,0]) cylinder(r=r, h=h);
}

difference() {
    union() {
        // === LEGS (extend up to meet shelf) ===
        for (lx=[-leg_x, leg_x])
            for (s=[-1, 1])
                translate([lx, s*rail_offset, 0])
                    rr(leg_w, rail_depth, leg_h);

        // === BRACE (midway up legs) ===
        for (lx=[-leg_x, leg_x])
            translate([lx-2, -rail_offset, leg_h/2])
                cube([4, rail_offset*2, 10]);

        // === FAN SHELF (sits on top of legs) ===
        translate([0, 0, shelf_z_local])
            rr(plat_w, plat_d, shelf_t, 3);

        // === 6 POSTS: corners + center (reduce bridging to ~105mm spans) ===
        for (dx=[-sw_w/2, 0, sw_w/2])
            for (dy=[-1, 1])
                translate([dx, dy*(slot_w/2 + wall/2), shelf_top_local])
                    rr(post_w, post_d, cable_gap);

        // === CRADLE WALLS ===
        translate([0, -(slot_w/2 + wall/2), cradle_z_local])
            rr(sw_w + 10, wall, wall_h);
        translate([0, (slot_w/2 + wall/2), cradle_z_local])
            rr(sw_w + 10, wall, wall_h);

        // === LIPS ===
        translate([0, -(slot_w/2 - lip/2), cradle_z_local])
            rr(sw_w + 10, lip, wall);
        translate([0, (slot_w/2 - lip/2), cradle_z_local])
            rr(sw_w + 10, lip, wall);

        // === END STOPS ===
        for (dx=[-1, 1])
            translate([dx*(sw_w/2 + clr + wall/2), 0, cradle_z_local])
                rr(wall, slot_w + wall*2, slot_lip);
    }

    // === FAN HOLES ===
    translate([f1x, 0, shelf_z_local - 1])
        cylinder(r=fan_cut_r, h=shelf_t + 2);
    translate([f2x, 0, shelf_z_local - 1])
        cylinder(r=fan_cut_r, h=shelf_t + 2);

    // === FAN SCREW HOLES ===
    for (fx=[f1x, f2x])
        for (dx=[-1, 1])
            for (dy=[-1, 1])
                translate([fx + dx*fan_hole_spacing/2, dy*fan_hole_spacing/2, shelf_z_local - 1])
                    cylinder(d=fan_screw_d, h=shelf_t + 2);

    // === TENON SOCKETS ===
    for (lx=[-leg_x, leg_x])
        for (s=[-1, 1])
            translate([lx, s*rail_offset, -0.5])
                rr(socket_w, socket_d, socket_h, 1.5);
}
