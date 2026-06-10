"""Dimensional/printability invariants for the street-proxy carrier.

These guard the fit-critical numbers: the carrier must slip inside the 1.5"
conduit, the lid must seat in the basket bore, both must be watertight single
bodies, and the board slot must actually be open. Run:

    ../tools/venv/bin/python -m pytest test_create_carrier.py -q
"""
import math
import os
import sys

import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import create_carrier as cc

CARRIER = cc.build_carrier()
LID = cc.build_lid()


def _mesh(shape, name):
    path = os.path.join("/tmp", f"_test_{name}.stl")
    cc.save_stl(shape, path)
    return trimesh.load(path)


def test_carrier_fits_conduit():
    m = _mesh(CARRIER, "carrier")
    w, d, h = (m.bounds[1] - m.bounds[0])
    assert max(w, d) < cc.CONDUIT_ID, "carrier OD must be strictly less than conduit ID (else it jams)"
    assert math.isclose(max(w, d), cc.CONDUIT_ID - cc.FIT_CLEAR, abs_tol=0.1)


def test_carrier_height():
    m = _mesh(CARRIER, "carrier")
    h = (m.bounds[1] - m.bounds[0])[2]
    assert math.isclose(h, cc.GRIP_LEN + cc.BASKET_H, abs_tol=0.1)


def test_carrier_is_printable_single_body():
    m = _mesh(CARRIER, "carrier")
    assert m.is_watertight, "carrier must be watertight to slice"
    assert m.body_count == 1, "carrier must be one connected piece (spine ties discs+basket)"


def test_carrier_is_hollow():
    """Not a solid slug: discs + spine + cup should be a small fraction of the envelope."""
    m = _mesh(CARRIER, "carrier")
    envelope = math.pi * (cc.CARRIER_R ** 2) * (cc.GRIP_LEN + cc.BASKET_H)
    assert 0.10 < m.volume / envelope < 0.45


def test_board_slot_is_open():
    """The axis at mid-grip must be empty (the PCB slot), but disc rim must be solid."""
    m = _mesh(CARRIER, "carrier")
    inside_slot = m.contains([[0, 0, cc.GRIP_LEN / 2]])[0]
    # (16,0) is past the slot edge (|x|>14.4) and off the flow-hole ring (r=15.5) -> disc body
    in_disc_body = m.contains([[16.0, 0, cc.DISC_T / 2]])[0]
    assert not inside_slot, "board slot should be open along the axis"
    assert in_disc_body, "disc body should be solid off the slot/flow-holes"


def test_lid_seats_in_basket():
    lm = _mesh(LID, "lid")
    w, d, _ = (lm.bounds[1] - lm.bounds[0])
    cup_bore_d = 2 * (cc.CARRIER_R - cc.BASKET_WALL)
    # flange must be WIDER than the cup bore (so it catches on the rim) but not
    # exceed the conduit ID
    assert cup_bore_d < max(w, d) < cc.CONDUIT_ID, "lid flange must catch the rim and clear the conduit"
    # and the plug must be narrower than the bore so it actually drops in
    assert (cc.CARRIER_R - cc.BASKET_WALL) - cc.LID_CLEAR < cc.CARRIER_R - cc.BASKET_WALL
    assert lm.is_watertight and lm.body_count == 1


def test_perf_smaller_than_typical_bead():
    """Perforations must retain beads; warn-level guard at the small end of silica gel (~2mm)."""
    assert cc.PERF_D <= 2.0
