$fn = 48;

sw_w = 210.4;
fan = 80;
rail_depth = 8;
rail_offset = 59;
plat_w = sw_w + 16;
leg_w = 30;
leg_x = plat_w/2 - leg_w/2 - 4;
split_z = 75;
tenon_w = leg_w - 6;
tenon_d = rail_depth - 2;
tenon_h = 16;
bolt_d = 4.5;

module rr(w, d, h, r=2) {
    hull() for (dx=[-(w/2-r),(w/2-r)], dy=[-(d/2-r),(d/2-r)])
        translate([dx,dy,0]) cylinder(r=r, h=h);
}

difference() {
    union() {
        // Floor rails
        for (s=[-1, 1])
            translate([0, s*rail_offset, 0])
                rr(plat_w, rail_depth, 4);
        // Legs
        for (lx=[-leg_x, leg_x])
            for (s=[-1, 1])
                translate([lx, s*rail_offset, 0])
                    rr(leg_w, rail_depth, split_z);
        // Tenons
        for (lx=[-leg_x, leg_x])
            for (s=[-1, 1])
                translate([lx, s*rail_offset, split_z])
                    rr(tenon_w, tenon_d, tenon_h, 1.5);
    }
    // Bolt holes through tenons
    for (lx=[-leg_x, leg_x])
        for (s=[-1, 1])
            translate([lx, s*rail_offset, split_z - 8])
                cylinder(d=bolt_d, h=tenon_h + 12);
}
