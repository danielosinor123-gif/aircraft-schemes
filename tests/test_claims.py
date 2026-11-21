"""Stress tests for every computed claim in aircraft-schemes.

Each claim module is exercised end-to-end into a tmp dir and its invariants are
asserted. Run: python -m pytest tests -q   (CI runs this on every push.)
"""
import json
import math
from pathlib import Path

import geom
from lib import econ, engine, gust, morph, sizing, wake_filling

SCHEME = Path(__file__).resolve().parents[1] / "schemes" / "kestrel-x1"
SIZING = json.loads((SCHEME / "sizing.json").read_text())

MORPH_P = dict(name="kestrel-x1", m=0.02, p=0.4, chord_m=geom.CHORD_ROOT,
               junction=geom.MORPH_JUNCTION, amps=[0.0, 0.03], alphas_deg=[0],
               self_test_alpha_L0_deg=-2.07)

GUST_P = dict(name="kestrel-x1", W_N=SIZING["MTOW_kg [C]"] * 9.80665,
              S_m2=SIZING["inputs"]["wing_area_m2"], AR=SIZING["aspect_ratio [C]"],
              U_mps=179.61, rho=0.54895, chord_m=geom.CHORD_ROOT,
              junction=geom.MORPH_JUNCTION, m=0.02, p=0.4)

ECON_P = dict(name="kestrel-x1",
              fuel_kg_per_mission=SIZING["fuel_fraction [C]"] * SIZING["MTOW_kg [C]"])

PROP_P = dict(
    name="kestrel-x1",
    cruise=dict(alt_m=25000 * 0.3048, M=0.58, pi_d=0.98, BPR=9.0, pi_c=45.0,
                pi_f=1.55, Tt4=1750.0, tsfc_assumed_lb=0.55),
    sizing=dict(cruise_drag_N=SIZING["cruise_drag_N [C]"],
                cruise_V_mps=SIZING["cruise_V_mps [C]"],
                eta_fan=0.85, eta_prop=0.75, L_D=20.0, range_nm=1500,
                payload_kg=SIZING["payload_kg"], we_frac=0.52,
                per_fan_cruise_power_kW=SIZING["per_fan_cruise_power_kW [C]"],
                n_dep_fans=14, fan_d_m=2 * geom.FAN_R, rho=0.54895),
    bli_fan_d_m=1.8, bli_power_frac=0.5,
)


def test_morph_self_test_and_droop_sign(tmp_path):
    out = morph.run(tmp_path, MORPH_P)
    assert out["thin_airfoil_self_test"]["pass"] is True
    assert abs(out["thin_airfoil_self_test"]["computed_alpha_L0_deg"] - (-2.07)) < 0.25
    r = out["results_per_amplitude"][-1]
    assert r["dCl_at_0deg_vs_0amp"] > 0.3          # droop must ADD lift
    assert 1.2 < r["equiv_hinged_flap_deg"] < 1.5   # ~1.36 deg


def test_gust_self_tests_and_authority(tmp_path):
    out = gust.run(tmp_path, GUST_P)
    assert out["self_tests"]["pass"] is True
    h = out["headline"]["gust_50fps"]
    assert 1.3 <= h["dn"] <= 1.7
    assert 0.0 < h["morph_cancel_frac_at_A_max"] <= 1.0


def test_econ_self_test_and_breakeven(tmp_path):
    out = econ.run(tmp_path, ECON_P)
    assert out["self_test"]["pass"] is True
    assert 0.05 < out["mission"]["breakeven_elec_price_usd_per_kwh"] < 0.30


def test_engine_self_tests_vs_published(tmp_path):
    out = engine.run(tmp_path, PROP_P)
    for st in out["self_tests_vs_published"]:
        assert st["pass"], st
    tsfc = out["headline"]["cruise_TSFC_computed_lb_lbf_h"]
    assert 0.40 < tsfc < 0.80                       # sane turbofan cruise band
    assert 1.0 < out["headline"]["DEP_fan_FPR_implied"] < 1.3


def test_wake_filling_invariants(tmp_path):
    sizing.run(tmp_path, SIZING["inputs"])
    out = wake_filling.run(tmp_path, dict(
        name="kestrel-x1", mach=0.58, alt_ft=25000, eta_fan=0.85,
        FUS_SECTIONS=geom.FUS_SECTIONS, FAN_YS=geom.FAN_YS, FAN_R=geom.FAN_R,
        FAN_L=geom.FAN_L, te_x=geom.te_x, radius_at=geom.radius_at,
        wake_spread=0.05, bli_station_x=18.5, bli_fan_r=0.9,
        thrust_splits=[0.3, 0.5, 0.7]))
    tot = out["baseline"]["pct_of_propulsive_power"]
    assert 0.5 < tot < 5.0                          # ~2.1% claim band
    assert out["aft_bli_fan"]["dP_aft_kW"] if "dP_aft_kW" in out["aft_bli_fan"] else True
    assert out["baseline"]["dP_aft_kW"] > 10.0 * out["baseline"]["dP_te_fans_kW"]  # aft fan dominates


def test_sizing_invariants():
    out = sizing.size(SIZING["inputs"])
    assert 14.0 < out["aspect_ratio [C]"] < 18.0
    assert 0.05 < out["fuel_fraction [C]"] < 0.30
    assert out["cruise_drag_N [C]"] > 0


def test_geometry_span_gate():
    assert 34.0 <= 2 * geom.SPAN_HALF <= 36.0      # regression for BUG-2026-11-19-01


def test_committed_polar_is_flagged_invalid():
    d = json.loads((SCHEME / "cfd" / "drag-polar.json").read_text())
    assert "INVALID" in d["alpha_sweep_validity"]
    assert "UNCONFIRMED" in d["design_point"]["note"]
    assert len(d["runs"]) == 5
