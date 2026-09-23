"""Invariants for the ZTH05 rework of the SPILLPROOF2 sensor box.

Two independent things have to hold. The DONOR tests pin what we measured out of
the shipped 3mf -- if AeonJoey's geometry ever differs from those numbers the
rework is being applied to something we did not survey, and it must fail loudly
rather than quietly cut the wrong hole. The REWORK tests pin that the result
actually takes a ZTH05: wide enough to enter, a stop with real overlap so it
cannot fall through, and a face that ends up flush.

    ../tools/venv/bin/python -m pytest test_modify_box.py -q
"""
import math
import os
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modify_box as mb


@pytest.fixture(scope="module")
def donor():
    if not os.path.exists(mb.donor_path()):
        pytest.skip(f"donor 3mf not present at {mb.donor_path()}")
    return mb.load_donor()


@pytest.fixture(scope="module")
def reworked(donor):
    return mb.rework(donor)


# --- finding the donor ------------------------------------------------------
# Opening the plate in Bambu Studio and saving it renumbers every object, so a
# re-saved 3mf no longer holds the box we surveyed. That happened once
# (2026-09-05) and left only a KeyError to explain it.

def _fake_3mf(path, with_box):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
        if with_box:
            z.writestr(mb.DONOR_MEMBER, "<model/>")
    return str(path)


def _truncated(path):
    """What an interrupted browser download leaves behind."""
    path.write_bytes(b"PK\x03\x04 truncated")
    return str(path)


def test_donor_is_found_under_the_makerworld_download_name(tmp_path):
    """MakerWorld names the download with '+' for spaces."""
    good = _fake_3mf(tmp_path / mb.DONOR_FILES[0], with_box=True)
    assert mb.donor_path(folder=str(tmp_path)) == good


def test_a_resaved_copy_is_passed_over_for_an_original(tmp_path):
    # the re-saved copy takes the FIRST name, so only the preference can skip it
    _fake_3mf(tmp_path / mb.DONOR_FILES[0], with_box=False)
    good = _fake_3mf(tmp_path / mb.DONOR_FILES[1], with_box=True)
    assert mb.donor_path(folder=str(tmp_path)) == good


def test_a_truncated_download_is_passed_over_for_an_original(tmp_path):
    _truncated(tmp_path / mb.DONOR_FILES[0])
    good = _fake_3mf(tmp_path / mb.DONOR_FILES[1], with_box=True)
    assert mb.donor_path(folder=str(tmp_path)) == good


def test_an_unreadable_entry_is_passed_over_for_an_original(tmp_path):
    (tmp_path / mb.DONOR_FILES[0]).mkdir()     # opening it raises OSError
    good = _fake_3mf(tmp_path / mb.DONOR_FILES[1], with_box=True)
    assert mb.donor_path(folder=str(tmp_path)) == good


def test_with_no_original_the_unusable_copy_is_returned_to_be_refused(tmp_path):
    resaved = _fake_3mf(tmp_path / mb.DONOR_FILES[1], with_box=False)
    assert mb.donor_path(folder=str(tmp_path)) == resaved


def test_with_no_copy_at_all_the_download_name_is_returned(tmp_path):
    assert mb.donor_path(folder=str(tmp_path)) == str(tmp_path / mb.DONOR_FILES[0])


def test_a_resaved_donor_is_refused_with_the_reason(tmp_path):
    resaved = _fake_3mf(tmp_path / mb.DONOR_FILES[1], with_box=False)
    with pytest.raises(ValueError, match="re-saved"):
        mb.load_donor(resaved)


def test_a_truncated_donor_is_refused_with_the_reason(tmp_path):
    with pytest.raises(ValueError, match="incomplete"):
        mb.load_donor(_truncated(tmp_path / mb.DONOR_FILES[0]))


@pytest.mark.parametrize("make, reason", [
    (lambda p: _fake_3mf(p, with_box=False), "re-saved"),
    (_truncated, "incomplete"),
    (lambda p: str(p), "not found"),
])
def test_the_command_exits_with_the_reason_not_a_traceback(tmp_path, monkeypatch,
                                                           make, reason):
    path = make(tmp_path / mb.DONOR_FILES[0])
    monkeypatch.setattr(sys, "argv", ["modify_box.py", path])
    with pytest.raises(SystemExit) as exit_:
        mb.main()
    assert reason in str(exit_.value.code)


# --- the donor is what we surveyed -----------------------------------------

def test_donor_outer_envelope(donor):
    w, d, h = donor.bounds[1] - donor.bounds[0]
    assert math.isclose(w, mb.BOX_W, abs_tol=0.02)
    assert math.isclose(d, mb.BOX_D, abs_tol=0.02)
    assert math.isclose(h, mb.BOX_H, abs_tol=0.02)


def test_donor_window_is_the_size_we_measured(donor):
    win = mb.measure_window(donor, depth=5.0)
    assert math.isclose(win.x_span, mb.DONOR_WINDOW, abs_tol=0.05)
    assert math.isclose(win.z_span, mb.DONOR_WINDOW, abs_tol=0.05)


def test_donor_stop_sits_at_the_depth_we_measured(donor):
    """12.75 mm in, the opening narrows in X only. That is the Xiaomi's stop."""
    before = mb.measure_window(donor, depth=mb.DONOR_SEAT_DEPTH - 0.4)
    after = mb.measure_window(donor, depth=mb.DONOR_SEAT_DEPTH + 0.4)
    assert math.isclose(before.x_span, mb.DONOR_WINDOW, abs_tol=0.05)
    assert math.isclose(after.x_span, mb.DONOR_SHOULDER, abs_tol=0.05)
    assert math.isclose(after.z_span, before.z_span, abs_tol=0.05)


# --- the rework takes a ZTH05 ----------------------------------------------

def test_sensor_clears_the_opening_all_the_way_to_the_seat(reworked):
    """43.30 mm of sensor must pass every section from the face to the seat, or
    it jams part way in and never reaches flush."""
    for depth in (0.3, 2.0, 5.0, 8.0, mb.SEAT_DEPTH - 0.3):
        win = mb.measure_window(reworked, depth=depth)
        assert win.x_span >= mb.ZTH05_FACE, f"X pinches to {win.x_span:.3f} at {depth} mm"
        assert win.z_span >= mb.ZTH05_FACE, f"Z pinches to {win.z_span:.3f} at {depth} mm"


def test_widening_never_reaches_the_outer_wall(reworked):
    """45.00 mm is the AMS bay limit and cannot move, so the window can only grow
    until the rim runs out. This is the wall the design is now pinned against."""
    assert mb.WINDOW + 2 * 0.50 <= mb.BOX_W, "window has eaten the whole rim"


def test_the_seat_actually_stops_the_sensor(reworked):
    """Past the seat the opening must narrow enough to catch a 43.30 mm face with
    real overlap -- a couple of tenths would just let it push through."""
    win = mb.measure_window(reworked, depth=mb.SEAT_DEPTH + 0.5)
    overlap = (mb.ZTH05_FACE - win.x_span) / 2.0
    assert overlap >= 0.5, f"only {overlap:.3f} mm of stop per side"


def test_sensor_finishes_flush_with_the_outer_face(reworked):
    """Measured on the mesh: the whole 10.50 mm of sensor goes in, and the stop
    catches it within 0.25 mm of that -- so the face ends at or just below the
    surface. The donor's 12.75 mm seat would have left it 2.25 mm sunk."""
    inside = mb.measure_window(reworked, depth=mb.ZTH05_THICK - 0.05)
    assert inside.x_span >= mb.ZTH05_FACE, "sensor stops short of full depth"
    caught = mb.measure_window(reworked, depth=mb.ZTH05_THICK + 0.25)
    assert caught.x_span < mb.ZTH05_FACE, "nothing stops the sensor within 0.25 mm"


def test_rework_does_not_touch_the_outer_envelope(reworked):
    """The AMS 2 Pro bay is the hard constraint; 45 mm is not negotiable."""
    w, d, h = reworked.bounds[1] - reworked.bounds[0]
    assert math.isclose(w, mb.BOX_W, abs_tol=0.02)
    assert math.isclose(d, mb.BOX_D, abs_tol=0.02)
    assert math.isclose(h, mb.BOX_H, abs_tol=0.02)


def test_nothing_is_thinned_past_printing(reworked):
    """Widening the window eats the frame around it. None of the three walls it
    eats into may drop below one 0.42 mm extrusion. The side rim is not a
    free-standing wall -- it is the box's own outer skin, continuous above and
    below the window -- so a single-line rim is acceptable here."""
    assert mb.side_wall() >= 0.50, f"side rim {mb.side_wall():.3f} mm"
    assert mb.divider_wall() >= 1.10, f"divider {mb.divider_wall():.3f} mm"
    assert mb.ceiling_wall() >= 1.90, f"ceiling {mb.ceiling_wall():.3f} mm"


def test_result_is_printable_solid(reworked):
    assert reworked.is_watertight, "rework must stay watertight"
    assert reworked.body_count == 1, "rework must stay a single body"


def test_window_is_sized_from_the_printed_calibration(reworked):
    """The number that matters is the PRINTED opening, not the nominal one. On the
    rev 1 ASA tiles a nominal 43.76 mm window only just admitted the 43.30 mm
    sensor, so this printer loses ~0.45 mm across a 43 mm hole."""
    wanted = mb.ZTH05_FACE + mb.PRINTED_LOSS + mb.FIT_CLEARANCE
    win = mb.measure_window(reworked, depth=5.0)
    assert math.isclose(win.x_span, wanted, abs_tol=0.05), f"cut {win.x_span:.3f}"
    assert math.isclose(win.z_span, wanted, abs_tol=0.05), f"cut {win.z_span:.3f}"
    assert wanted > mb.DONOR_WINDOW, "the donor window is too small; it must grow"


def test_predicted_printed_opening_actually_admits_the_sensor(reworked):
    """Nominal 43.60 would have printed at ~43.15 and jammed -- the same failure
    the donor already has. Size for what comes off the plate."""
    printed = mb.WINDOW - mb.PRINTED_LOSS
    assert printed >= mb.ZTH05_FACE + 0.10, (
        f"predicted printed opening {printed:.2f} leaves "
        f"{printed - mb.ZTH05_FACE:.2f} mm on a {mb.ZTH05_FACE} mm sensor")


def test_calibration_matches_what_the_tiles_showed(reworked):
    """The 4-dot tile (43.76 nominal) admitted the sensor but was tight; the 3-dot
    (43.56) did not. PRINTED_LOSS must sit in the band that explains both."""
    assert 43.56 - mb.PRINTED_LOSS < mb.ZTH05_FACE, "3-dot should have been too small"
    assert 43.76 - mb.PRINTED_LOSS >= mb.ZTH05_FACE - 0.02, "4-dot did admit it"
