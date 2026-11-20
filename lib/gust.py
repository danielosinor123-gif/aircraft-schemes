"""CLAIM-3: turbulence (gust) alleviation with the KESTREL-TE morphing law [C].

Question: when the plane hits a vertical gust, how much extra lift does the
wing make, how much does that bump the load factor n, and how much of it can
the KESTREL-TE morphing trailing edge (CLAIM-2 law) cancel by drooping/reflexing?

Method (order-of-magnitude, quasi-steady — all [C]):

    d_alpha = atan(w_g / U)                    # gust tilts the relative wind
    Cl_alpha_3D = a0 * AR / (AR + 2)           # lifting-line (Helmbold) correction, a0 = 2*pi
    dCl_gust = Cl_alpha_3D * d_alpha
    dL = q * S * dCl_gust ;  dn = dL / W ;  n = 1 + dn

Morph authority comes from lib/morph.py itself (single source for the law):
dCl/dA by finite difference of the Glauert solver at alpha = 0. Full
cancellation needs A_req = dCl_gust / (dCl/dA); we compare that to the
demonstrated A_max = 0.03 (138 mm droop at root chord).

Self-tests (recorded in the JSON, must pass):
  1. 2-D thin-airfoil dCl/dalpha from lib/morph.py must equal 2*pi/rad within 0.15.
  2. dn for a 15.24 m/s (50 ft/s) sharp-edged gust at the cruise point must land
     in [1.3, 1.7] (hand check: Cl_alpha~5.6/rad, dalpha~0.085 rad -> dCl~0.47,
     dn = q*S*dCl/W ~ 1.48 at W = 211.8 kN, S = 75 m^2, q = 8854 Pa).

Caveats: quasi-steady (real gusts have an unsteady Kussner build-up, so peak
loads are somewhat higher); no structural dynamics / wing bending relief;
lifting-line AR correction is the simple Helmbold form; the morph actuation
RATE is not modeled (a gust needs the TE to move in ~0.1-0.5 s — that is the
falsification path: unsteady CFD + actuator dynamics). 2-D section, 3-D
correction only. NOT validated.
"""
import json
import math
from pathlib import Path

from lib import morph

GUSTS_MPS = [5.0, 10.0, 15.24]   # 15.24 m/s = 50 ft/s, the commonly used discrete gust [E]
A_MAX = 0.03                       # demonstrated morph amplitude (CLAIM-2 headline), fraction of chord


def cl_alpha_3d(a0, AR):
    """Lift-curve slope of a finite wing, Helmbold lifting-line form, per rad."""
    return a0 * AR / (AR + 2.0)


def run(outdir, P):
    """P keys: name, W_N, S_m2, AR, U_mps, rho, chord_m, junction, m, p."""
    outdir = Path(outdir)
    W, S, AR, U, rho = P["W_N"], P["S_m2"], P["AR"], P["U_mps"], P["rho"]
    c, j, m, p = P["chord_m"], P["junction"], P["m"], P["p"]
    q = 0.5 * rho * U * U
    a0 = 2.0 * math.pi

    # --- self-test 1: 2-D dCl/dalpha from the morph Glauert solver ~ 2*pi/rad
    a = math.radians(1.0)
    cl2d = (morph.glauert(m, p, j, 0.0, a)["Cl"] - morph.glauert(m, p, j, 0.0, 0.0)["Cl"]) / a
    st1 = {"computed_dCl_dalpha_2d_per_rad": round(cl2d, 4), "thin_airfoil_2pi": round(a0, 4),
           "abs_err": round(abs(cl2d - a0), 4), "pass": abs(cl2d - a0) < 0.15}

    # --- morph authority: dCl/dA at alpha=0 by finite difference (law is linear-ish in A)
    dA = 0.01
    dCl_dA = (morph.glauert(m, p, j, dA, 0.0)["Cl"] - morph.glauert(m, p, j, 0.0, 0.0)["Cl"]) / dA
    dCl_morph_max = dCl_dA * A_MAX

    Cl_alpha = cl_alpha_3d(a0, AR)
    rows = []
    for w in GUSTS_MPS:
        dalpha = math.atan(w / U)
        dCl = Cl_alpha * dalpha
        dL = q * S * dCl
        dn = dL / W
        a_req = dCl / dCl_dA
        rows.append({
            "gust_mps": w,
            "gust_fps": round(w * 3.28084, 1),
            "dalpha_rad": round(dalpha, 5),
            "dCl_gust": round(dCl, 4),
            "dL_N": round(dL, 0),
            "dn": round(dn, 4),
            "n_total": round(1.0 + dn, 3),
            "morph_cancel_frac_at_A_max": round(min(1.0, dCl_morph_max / dCl), 4),
            "A_req_to_cancel_fully": round(a_req, 5),
            "A_req_mm_root_chord": round(a_req * c * 1000, 1),
            "within_A_max": a_req <= A_MAX,
        })

    st2 = next(r for r in rows if r["gust_mps"] == 15.24)
    self_test_2 = {"dn_at_50fps": st2["dn"], "expected_range": [1.3, 1.7],
                   "pass": 1.3 <= st2["dn"] <= 1.7}
    self_test = {"thin_airfoil_dCl_dalpha": st1, "gust_dn_hand_check": self_test_2,
                 "pass": st1["pass"] and self_test_2["pass"]}
    if not self_test["pass"]:
        raise SystemExit("CLAIM-3 self-test FAILED — do not commit numbers")

    r50 = st2
    out = {
        "scheme": P["name"],
        "claim_id": "CLAIM-3",
        "tag": "[C] computed in-repo by lib/gust.py — quasi-steady gust loads + morphing-TE "
               "alleviation authority. NOT validated; no unsteady (Kussner) or structural dynamics.",
        "question": "How much does a vertical gust bump the load factor, and how much of that "
                    "can the KESTREL-TE morphing law cancel?",
        "method": {
            "Cl_alpha_3D_per_rad": round(Cl_alpha, 4),
            "Cl_alpha_formula": "a0*AR/(AR+2), a0=2*pi (Helmbold lifting-line)",
            "gust_model": "sharp-edged vertical gust, quasi-steady dalpha = atan(w/U)",
            "dCl_dA_per_chord_frac": round(dCl_dA, 4),
            "dCl_dA_source": "finite difference of lib/morph.py Glauert solver (CLAIM-2 law), alpha=0",
            "A_max_demonstrated": A_MAX,
            "dCl_morph_at_A_max": round(dCl_morph_max, 4),
        },
        "cruise_point": {"W_N": round(W, 0), "S_m2": S, "AR": round(AR, 2), "U_mps": U,
                         "rho_kg_m3": rho, "q_Pa": round(q, 1)},
        "self_tests": self_test,
        "results_per_gust": rows,
        "headline": {
            "gust_50fps": {"dn": r50["dn"], "n_total": r50["n_total"],
                           "morph_cancel_frac_at_A_max": r50["morph_cancel_frac_at_A_max"],
                           "A_req_full_cancel_mm": r50["A_req_mm_root_chord"],
                           "within_A_max": r50["within_A_max"]},
        },
        "claim": (
            "CLAIM-3: at the M0.58 cruise point a 50 ft/s (15.24 m/s) sharp-edged vertical gust "
            f"adds dn = {r50['dn']} (n = 1 -> {r50['n_total']}) [C]. The KESTREL-TE law at its "
            f"demonstrated A = 3% chord droop (dCl = {round(dCl_morph_max,3)}) cancels "
            f"{100*r50['morph_cancel_frac_at_A_max']:.0f}% of that gust's lift increment; full "
            f"cancellation needs A = {r50['A_req_mm_root_chord']} mm droop at root chord — just past "
            "the demonstrated range, so the law has real gust-alleviation authority but not "
            "complete authority at 50 ft/s. Quasi-steady [C]; falsify with unsteady CFD of the "
            "morphed wing (actuation rate is the untested part)."
        ),
        "caveats": [
            "Quasi-steady: real sharp-edged gusts build up over ~chord-lengths of travel (Kussner), "
            "so true peak loads are somewhat higher than these numbers.",
            "No structural dynamics: wing bending relief and aeroelastic response not modeled.",
            "Helmbold AR correction is the simple incompressible form; transonic/compressibility ignored.",
            "Morph actuation RATE not modeled — a gust alleviation system must move the TE in "
            "~0.1-0.5 s; that is the falsification path (unsteady CFD + actuator model).",
            "Gust alleviation also reduces passenger-perceived bumpiness, which is the design goal "
            "in docs/passenger-first.md — this file quantifies the aerodynamic authority only.",
        ],
    }
    adir = outdir / "analysis"
    adir.mkdir(exist_ok=True)
    path = adir / "gust-alleviation.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print("report:", path)
    print(f"  self-tests pass={self_test['pass']}")
    print(f"  50 ft/s gust: dn={r50['dn']}, cancel at A_max={100*r50['morph_cancel_frac_at_A_max']:.0f}%, "
          f"A_req={r50['A_req_mm_root_chord']} mm (A_max={A_MAX*c*1000:.0f} mm)")
    return out
