"""KESTREL morphing trailing-edge law + thin-airfoil analysis — CLAIM-2 [C].

The KESTREL-TE law (authored in this repo; first published here, commit of
2026-11-19): the aft fraction (1 - j) of the chord morphs smoothly. Camber
perturbation (in chord units):

    dz(xi) = -A * s^2 * (3 - 2s),   s = (xi - j) / (1 - j),   xi = x/c

i.e. a smoothstep: ZERO slope at the junction (no hinge line, no gap, no
discontinuity) and a rounded tip. A = amplitude as a fraction of chord,
A > 0 = DROOP (trailing edge down, more camber/lift), A < 0 = reflex.
Thickness is unchanged (scheme model).

Aerodynamic effect is computed with classical thin-airfoil theory (Glauert
integrals on a theta grid, trapezoid rule) implemented here from first
principles — no empirical flap tables copied from anywhere:

    xi = (1 - cos(theta)) / 2
    A0 = alpha - (1/pi) * int(dzeta/dxi dtheta)
    An = (2/pi) * int(dzeta/dxi * cos(n theta) dtheta)
    Cl = 2 pi (A0 + A1/2)
    Cm_le = -(pi/2)(A0 + A1 - A2/2),  Cm_ac = Cm_le + Cl/4
    alpha_L0 = (1/pi) int(dzeta/dxi dtheta) - A1/2

Self-test: plain NACA 2412 must reproduce alpha_L0 ~ -2.07 deg (published
[E] value) — checked in run() and recorded in the JSON.

Comparison: equivalent hinged flap at the same junction (dzeta/dxi -= delta
for xi >= j; thin-airfoil is exactly linear in delta) gives the flap angle
delta_eq that produces the same dCl as the morphing law — quantifying what
the morphing law buys (same lift change, no hinge gap / actuator step).

Every number here is a [C] estimate: 2-D, inviscid, thin airfoil. NOT validated.
"""
import json
import math
from pathlib import Path

N_THETA = 1440


def dz_over_c(xi, j, amp_frac):
    """KESTREL-TE morphing camber perturbation, chord units (z positive UP).
    amp_frac > 0 = droop (TE down -> dz negative at the rear). xi = x/c."""
    if xi < j:
        return 0.0
    s = (xi - j) / (1.0 - j)
    return -amp_frac * s * s * (3.0 - 2.0 * s)


def naca_camber(xi, m, p):
    """NACA 4-digit camber line, chord units."""
    if xi < p:
        return m / p**2 * (2 * p * xi - xi * xi)
    return m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * xi - xi * xi)


def slope_fn(m, p, j, amp_frac):
    """(theta, d(zeta)/dxi) samples. Uniform xi grid -> theta = acos(1-2xi) is
    NON-uniform; integrators must use the actual per-interval dtheta."""
    n = 2000
    xs = [i / n for i in range(n + 1)]
    zs = [naca_camber(x, m, p) + dz_over_c(x, j, amp_frac) for x in xs]
    out = []
    for i in range(n + 1):
        xi = xs[i]
        theta = math.acos(1.0 - 2.0 * xi)
        h = xs[1] - xs[0]
        if i == 0:
            s = (zs[1] - zs[0]) / h
        elif i == n:
            s = (zs[n] - zs[n - 1]) / h
        else:
            s = (zs[i + 1] - zs[i - 1]) / (2 * h)
        out.append((theta, s))
    return out


def _integ(pts, f):
    """Trapezoid over the actual (possibly non-uniform) theta grid."""
    tot = 0.0
    for (t0, s0), (t1, s1) in zip(pts, pts[1:]):
        tot += 0.5 * (f(t0, s0) + f(t1, s1)) * (t1 - t0)
    return tot


def glauert(m, p, j, amp_frac, alpha):
    """Thin-airfoil coefficients for NACA(m,p) + KESTREL morph at angle alpha (rad)."""
    pts = slope_fn(m, p, j, amp_frac)
    I0 = _integ(pts, lambda t, s: s)
    A0 = alpha - I0 / math.pi
    A1 = (2.0 / math.pi) * _integ(pts, lambda t, s: s * math.cos(t))
    A2 = (2.0 / math.pi) * _integ(pts, lambda t, s: s * math.cos(2 * t))
    Cl = 2 * math.pi * (A0 + A1 / 2.0)
    Cm_le = -(math.pi / 2.0) * (A0 + A1 - A2 / 2.0)
    Cm_ac = Cm_le + Cl / 4.0
    alpha_L0 = I0 / math.pi - A1 / 2.0
    return {"Cl": Cl, "Cm_ac": Cm_ac, "alpha_L0": alpha_L0, "A0": A0, "A1": A1, "A2": A2}


def _flap_slope_fn(m, p, j, delta):
    """Hinged flap at junction j deflected delta (rad, down +): slope -= delta
    for xi >= j, on top of the base camber."""
    n = 2000
    pts = []
    for i in range(n + 1):
        xi = i / n
        theta = math.acos(1 - 2 * xi)
        zc = naca_camber(xi, m, p) - delta * max(0.0, (xi - j) / (1 - j))
        pts.append((theta, xi, zc))
    out = []
    for i, (t, xi, z) in enumerate(pts):
        if i == 0:
            s = (pts[1][2] - pts[0][2]) * n
        elif i == len(pts) - 1:
            s = (pts[-1][2] - pts[-2][2]) * n
        else:
            s = (pts[i + 1][2] - pts[i - 1][2]) * n / 2
        out.append((t, s))
    return out


def flap_dCl_per_rad(m, p, j):
    """dCl per radian of a hinged flap at junction j (thin airfoil is exactly
    linear in delta, so one finite difference is exact)."""
    d = 0.01
    base_pts = slope_fn(m, p, 0.0, 0.0)
    flap_pts = _flap_slope_fn(m, p, j, d)

    def Cl_of(pts, alpha=0.0):
        I0 = _integ(pts, lambda t, s: s)
        A0 = alpha - I0 / math.pi
        A1 = (2.0 / math.pi) * _integ(pts, lambda t, s: s * math.cos(t))
        return 2 * math.pi * (A0 + A1 / 2)

    return (Cl_of(flap_pts) - Cl_of(base_pts)) / d


def run(outdir, P):
    """P keys: name, m, p (airfoil), chord_m, junction, amps (fractions of chord),
    alphas_deg (list), self_test_alpha_L0_deg (published value for the plain airfoil)."""
    outdir = Path(outdir)
    m, p, c, j = P["m"], P["p"], P["chord_m"], P["junction"]

    # self-test: plain airfoil alpha_L0 vs published [E]
    st = glauert(m, p, j, 0.0, 0.0)
    aL0_deg = math.degrees(st["alpha_L0"])
    self_test = {"airfoil": f"NACA {int(m*100)}412-ish m={m} p={p}",
                 "computed_alpha_L0_deg": round(aL0_deg, 3),
                 "published_alpha_L0_deg [E]": P["self_test_alpha_L0_deg"],
                 "abs_err_deg": round(abs(aL0_deg - P["self_test_alpha_L0_deg"]), 3),
                 "pass": abs(aL0_deg - P["self_test_alpha_L0_deg"]) < 0.25}

    K = flap_dCl_per_rad(m, p, j)   # dCl per radian of hinged flap at junction j

    rows = []
    base = glauert(m, p, j, 0.0, 0.0)
    for a in P["amps"]:
        r = {"amp_frac_chord": a, "amp_mm": round(a * c * 1000, 1)}
        for al_deg in P["alphas_deg"]:
            g = glauert(m, p, j, a, math.radians(al_deg))
            r[f"Cl_at_{al_deg}deg"] = round(g["Cl"], 5)
        g0 = glauert(m, p, j, a, 0.0)
        r["alpha_L0_deg"] = round(math.degrees(g0["alpha_L0"]), 3)
        r["dCl_at_0deg_vs_0amp"] = round(g0["Cl"] - base["Cl"], 5)
        r["dCm_ac_vs_0amp"] = round(g0["Cm_ac"] - base["Cm_ac"], 5)
        r["equiv_hinged_flap_deg"] = round(math.degrees((g0["Cl"] - base["Cl"]) / K), 2) if K else None
        rows.append(r)

    amax = max(P["amps"])
    rmax = next(r for r in rows if r["amp_frac_chord"] == amax)
    out = {
        "scheme": P["name"],
        "claim_id": "CLAIM-2",
        "tag": "[C] computed in-repo by lib/morph.py — 2-D inviscid thin-airfoil theory, NOT validated",
        "law": {
            "name": "KESTREL-TE smoothstep morphing camber law (authored in this repo)",
            "formula": "dz(xi) = A * s^2 * (3 - 2s),  s = (xi - j)/(1 - j),  xi = x/c,  xi >= j",
            "properties": ["zero slope at junction (no hinge line / no gap)",
                           "rounded tip (C1 continuous everywhere)",
                           "thickness unchanged; camber-only morph (scheme model)",
                           "A > 0 droop (lift), A < 0 reflex (cruise drag reduction)"],
            "formula_sign": "dz = -A*s^2*(3-2s), z positive UP, so A>0 = TE down = droop",
            "junction_j": j, "chord_m": c,
        },
        "airfoil": {"m": m, "p": p, "note": "NACA 2412-class scheme profile (same as model.py)"},
        "thin_airfoil_self_test": self_test,
        "flap_equivalence": {"junction": j,
                             "dCl_per_rad_hinged_flap": round(K, 4),
                             "note": "thin-airfoil theory is exactly linear in flap angle; "
                                     "equiv_hinged_flap_deg = dCl_morph / K"},
        "results_per_amplitude": rows,
        "headline": {
            "max_amp_frac_chord": amax,
            "dCl_at_0deg": rmax["dCl_at_0deg_vs_0amp"],
            "equiv_hinged_flap_deg": rmax["equiv_hinged_flap_deg"],
            "dCm_ac": rmax["dCm_ac_vs_0amp"],
        },
        "claim": ("CLAIM-2: the KESTREL-TE smoothstep morphing law (authored in this repo, "
                  f"first published in commit history 2026-11-19) produces dCl = "
                  f"{rmax['dCl_at_0deg_vs_0amp']} at A = {amax} of chord — equivalent to a hinged "
                  f"flap of {rmax['equiv_hinged_flap_deg']} deg at the same junction — but with no "
                  "hinge line or gap. [C] 2-D inviscid estimate; falsifiable by CFD on the morphed "
                  "geometry (see docs/morphing-te.md)."),
        "method_notes": [
            "Glauert thin-airfoil integrals on a theta grid (N=1440), trapezoid rule; slopes by central differences.",
            "Self-test: plain NACA 2412 alpha_L0 must match the published ~-2.07 deg within 0.25 deg.",
            "2-D inviscid: no viscous hinge-moment or gap-drag penalty modeled; those favor the morphing law in reality, so treat dCl as a lower-confidence estimate and the comparison as qualitative.",
        ],
    }
    adir = outdir / "analysis"
    adir.mkdir(exist_ok=True)
    path = adir / "morphing-te.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print("report:", path)
    print(f"  self-test alpha_L0: {aL0_deg:.3f} deg (published {P['self_test_alpha_L0_deg']}) "
          f"pass={self_test['pass']}")
    print(f"  A={amax}c -> dCl={rmax['dCl_at_0deg_vs_0amp']}, equiv flap={rmax['equiv_hinged_flap_deg']} deg")
    return out
