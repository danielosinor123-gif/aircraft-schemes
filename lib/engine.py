"""Turbofan on-design cycle model + KESTREL-X1 propulsion sizing — PROP-1 [C].

Standard textbook on-design cycle (Mattingly-style), ideal gas with component
efficiencies:

    intake:  Tt2 = T0 (1+0.2 M^2),   Pt2 = pi_d p0 (1+0.2 M^2)^3.5
    fan:     Pt13 = pi_f Pt2,  Tt13 = Tt2 (1 + (pi_f^0.2857 - 1)/eta_f)
    comp:    Pt3 = pi_c Pt2,   Tt3  = Tt2 (1 + (pi_c^0.2857 - 1)/eta_c)
    burner:  Pt4 = pi_b Pt3,   f = cp_c (Tt4 - Tt3) / (eta_b LHV - cp_g Tt4)
    turbine: (1+f) cp_g (Tt4 - Tt5) = cp_c (Tt3 - Tt2) + BPR cp_c (Tt13 - Tt2)
             Pt5 = Pt4 (1 - (1 - Tt5/Tt4)/eta_t)^(g_g/(g_g-1))
    nozzles: Ve = sqrt(2 eta_n cp Tt (1 - (p0/Pt)^((g-1)/g)))   (fully expanded)
    F / m_dot_core = (1+f) Ve9 - U + BPR (Ve13 - U)
    TSFC [kg/(N s)] = f / (F/m_dot_core);   lb/(lbf h) = TSFC / 2.8325e-5

Self-tests vs published engine data [E] (verified via web sources 2026-11-21, see
docs/BUGS.md PROV-2026-11-21-07): CFM56-7B-class cruise TSFC ~0.667 lb/lbf/h
(AIAA 2026), LEAP-1A-class ~0.51 (manufacturer data), NASA NPSS advanced
single-aisle ~0.56 (SciTech 2024). Bands are deliberately wide — this idealized
cycle exists to catch order-of-magnitude errors, not to match NPSS.

KESTREL-X1 application: turbo-generator cycle at the M0.58 / 25,000 ft cruise
point, checked against the tsfc = 0.55 assumption baked into sizing.py; BPR and
Tt4 sensitivity; fan-loading check for the 14 DEP fans (0.64 m dia, per-fan cruise
power from sizing.json) and the aft BLI fan. Fuel-fraction sensitivity uses the
SAME Breguet convention as lib/sizing.py.

All outputs [C]. Caveats: on-design only (no off-design/spool matching), no BLI
inlet-distortion penalty, no bleed/accessories, fully-expanded ideal nozzles,
constant cp per stream. NOT validated.
"""
import json
import math
from pathlib import Path

GAMMA_C, GAMMA_G = 1.4, 1.333
CP_C, CP_G = 1004.5, 1156.0          # J/(kg K), cold / hot stream
LHV = 43.0e6                          # J/kg, Jet A
ETA_F, ETA_C, ETA_T = 0.90, 0.90, 0.92
ETA_B, ETA_N = 0.995, 0.98
PI_B, PI_N = 0.95, 0.98
LB_LBF_HR_TO_KG_N_S = 2.8325e-5       # 1 lb/(lbf h) = 2.8325e-5 kg/(N s)
R_GAS = 287.05


def isa(h_m):
    """ISA troposphere: T0 [K], p0 [Pa]."""
    T0 = 288.15 - 0.0065 * h_m
    p0 = 101325.0 * (T0 / 288.15) ** 5.2559
    return T0, p0


def cycle(alt_m, M, BPR, pi_c, pi_f, Tt4, pi_d):
    """On-design turbofan point. Returns dict with TSFC in lb/(lbf h) and SI."""
    T0, p0 = isa(alt_m)
    a0 = math.sqrt(GAMMA_C * R_GAS * T0)
    U = M * a0
    ram = 1.0 + 0.2 * M * M
    Tt2 = T0 * ram
    Pt2 = pi_d * p0 * ram ** 3.5

    Pt13 = pi_f * Pt2
    Tt13 = Tt2 * (1.0 + (pi_f ** 0.2857 - 1.0) / ETA_F)
    Pt3 = pi_c * Pt2
    Tt3 = Tt2 * (1.0 + (pi_c ** 0.2857 - 1.0) / ETA_C)
    Pt4 = PI_B * Pt3
    f = CP_C * (Tt4 - Tt3) / (ETA_B * LHV - CP_G * Tt4)   # fuel-air ratio

    # turbine work balance (per kg core airflow)
    Tt5 = Tt4 - (CP_C * (Tt3 - Tt2) + BPR * CP_C * (Tt13 - Tt2)) / ((1.0 + f) * CP_G)
    Pt5 = Pt4 * (1.0 - (1.0 - Tt5 / Tt4) / ETA_T) ** (GAMMA_G / (GAMMA_G - 1.0))

    Pt9, Pt19 = PI_N * Pt5, PI_N * Pt13
    if Pt9 > p0:
        pr9 = p0 / Pt9
        Ve9 = math.sqrt(2.0 * ETA_N * CP_G * Tt5 * (1.0 - pr9 ** ((GAMMA_G - 1.0) / GAMMA_G)))
    else:
        Ve9 = 0.0
    if Pt19 > p0:
        pr19 = p0 / Pt19
        Ve13 = math.sqrt(2.0 * ETA_N * CP_C * Tt13 * (1.0 - pr19 ** ((GAMMA_C - 1.0) / GAMMA_C)))
    else:
        Ve13 = 0.0

    F_per_mcore = (1.0 + f) * Ve9 - U + BPR * (Ve13 - U)   # N per kg/s core flow
    tsfc_si = f / F_per_mcore                              # kg/(N s)
    return {
        "alt_m": alt_m, "M": M, "U_mps": round(U, 1), "BPR": BPR, "pi_c_OPR": pi_c,
        "pi_f_FPR": pi_f, "Tt4_K": Tt4, "fuel_air_ratio": round(f, 5),
        "Tt3_K": round(Tt3, 0), "Tt5_K": round(Tt5, 0),
        "Ve9_mps": round(Ve9, 1), "Ve13_mps": round(Ve13, 1),
        "F_per_kg_s_core_N": round(F_per_mcore, 1),
        "TSFC_kg_Ns": tsfc_si,
        "TSFC_lb_lbf_h": tsfc_si / LB_LBF_HR_TO_KG_N_S,
    }


# Self-test points: published cruise TSFC [E] (verified 2026-11-21)
SELF_TEST_POINTS = [
    {"name": "CFM56-7B-class (737-800)", "published_TSFC": 0.667, "band": [0.55, 0.78],
     "alt_m": 10668, "M": 0.80, "pi_d": 0.90, "BPR": 5.5, "pi_c": 32.0, "pi_f": 1.7, "Tt4": 1550},
    {"name": "LEAP-1A-class (A320neo)", "published_TSFC": 0.51, "band": [0.45, 0.60],
     "alt_m": 10668, "M": 0.80, "pi_d": 0.90, "BPR": 11.0, "pi_c": 40.0, "pi_f": 1.55, "Tt4": 1750},
    {"name": "NASA NPSS advanced single-aisle (SciTech 2024)", "published_TSFC": 0.56, "band": [0.48, 0.66],
     "alt_m": 10668, "M": 0.80, "pi_d": 0.90, "BPR": 8.6, "pi_c": 44.6, "pi_f": 1.6, "Tt4": 1750},
]


def fan_loading(rho, Tt2, fan_d_m, power_W, v_face_mps=120.0):
    """Fan disc loading check [C]: mass flow at assumed face velocity, specific
    work, implied fan pressure ratio."""
    A = math.pi / 4.0 * fan_d_m ** 2
    m_dot = rho * A * v_face_mps
    w_spec = power_W / m_dot                       # J/kg
    dT = w_spec / CP_C
    FPR = (1.0 + ETA_F * dT / Tt2) ** (GAMMA_C / (GAMMA_C - 1.0))
    return {"fan_d_m": fan_d_m, "area_m2": round(A, 3), "v_face_mps": v_face_mps,
            "m_dot_kg_s": round(m_dot, 1), "power_W": round(power_W, 0),
            "specific_work_kJ_kg": round(w_spec / 1000.0, 2),
            "FPR_implied": round(FPR, 4)}


def run(outdir, P):
    """P keys: name, cruise{alt_m,M,pi_d,BPR,pi_c,pi_f,Tt4,tsfc_assumed_lb},
    sizing{cruise_drag_N,cruise_V_mps,eta_fan,eta_prop,L_D,range_nm,payload_kg,we_frac,
    per_fan_cruise_power_kW,n_dep_fans,fan_d_m,rho}, bli_fan_d_m, bli_power_frac."""
    outdir = Path(outdir)
    cr, sz = P["cruise"], P["sizing"]

    # --- self-tests against published engine data
    st = []
    for pt in SELF_TEST_POINTS:
        r = cycle(pt["alt_m"], pt["M"], pt["BPR"], pt["pi_c"], pt["pi_f"], pt["Tt4"], pt["pi_d"])
        tsfc = r["TSFC_lb_lbf_h"]
        ok = pt["band"][0] <= tsfc <= pt["band"][1]
        st.append({"point": pt["name"], "published_TSFC_lb_lbf_h [E]": pt["published_TSFC"],
                   "computed_TSFC_lb_lbf_h": round(tsfc, 3), "band": pt["band"], "pass": ok})
    all_pass = all(s["pass"] for s in st)
    if not all_pass:
        raise SystemExit("PROP-1 self-test FAILED — cycle model out of published bands; do not commit")

    # --- KESTREL turbo-generator cycle at the cruise point
    k = cycle(cr["alt_m"], cr["M"], cr["BPR"], cr["pi_c"], cr["pi_f"], cr["Tt4"], cr["pi_d"])
    tsfc_k = k["TSFC_lb_lbf_h"]
    ratio = tsfc_k / cr["tsfc_assumed_lb"]
    check = {"computed_TSFC_lb_lbf_h": round(tsfc_k, 3),
             "sizing_assumption_tsfc_1hr": cr["tsfc_assumed_lb"],
             "ratio_computed_over_assumed": round(ratio, 3),
             "within_20pct": abs(ratio - 1.0) <= 0.20,
             "verdict": ("sizing.py's tsfc=0.55 is consistent with a modern high-BPR cycle at this "
                         "cruise point" if abs(ratio - 1.0) <= 0.20 else
                         "sizing.py's tsfc=0.55 is NOT matched by this cycle — investigate")}

    # --- sensitivity sweeps at the cruise point
    bpr_sweep = [{"BPR": b, "TSFC_lb_lbf_h": round(cycle(cr["alt_m"], cr["M"], b, cr["pi_c"], cr["pi_f"], cr["Tt4"], cr["pi_d"])["TSFC_lb_lbf_h"], 3)}
                 for b in [5.5, 8.0, 9.0, 11.0, 14.0]]
    tt4_sweep = [{"Tt4_K": t, "TSFC_lb_lbf_h": round(cycle(cr["alt_m"], cr["M"], cr["BPR"], cr["pi_c"], cr["pi_f"], t, cr["pi_d"])["TSFC_lb_lbf_h"], 3)}
                 for t in [1550, 1650, 1750, 1850]]

    # --- fuel-fraction sensitivity, SAME Breguet convention as lib/sizing.py
    V_kt = sz["cruise_V_mps"] / 0.514444
    def fuel_frac(c):
        return 1.0 - math.exp(-sz["range_nm"] * c / (V_kt * sz["L_D"] * sz["eta_prop"]))
    wf_assumed = fuel_frac(cr["tsfc_assumed_lb"])
    wf_computed = fuel_frac(tsfc_k)
    def mtow(wf):
        return sz["payload_kg"] / (1.0 - wf - sz["we_frac"])
    fuel_sens = {"fuel_fraction_at_tsfc_0.55": round(wf_assumed, 4),
                 "fuel_fraction_at_computed_tsfc": round(wf_computed, 4),
                 "MTOW_kg_at_0.55": round(mtow(wf_assumed), 0),
                 "MTOW_kg_at_computed": round(mtow(wf_computed), 0),
                 "dMTOW_pct": round(100.0 * (mtow(wf_computed) / mtow(wf_assumed) - 1.0), 2)}

    # --- fan loading: DEP fans + aft BLI fan
    T0, p0 = isa(cr["alt_m"])
    Tt2 = T0 * (1.0 + 0.2 * cr["M"] ** 2)
    P_total = sz["cruise_drag_N"] * sz["cruise_V_mps"] / sz["eta_fan"]      # W
    dep = fan_loading(sz["rho"], Tt2, sz["fan_d_m"], sz["per_fan_cruise_power_kW"] * 1000.0)
    bli = fan_loading(sz["rho"], Tt2, P["bli_fan_d_m"], P_total * P["bli_power_frac"])
    fan = {"total_cruise_propulsive_power_W": round(P_total, 0),
           "DEP_fans": {"n": sz["n_dep_fans"], "per_fan": dep},
           "aft_BLI_fan": {"power_frac_of_total": P["bli_power_frac"], "loading": bli}}

    out = {
        "scheme": P["name"],
        "claim_id": "PROP-1",
        "tag": "[C] computed in-repo by lib/engine.py — idealized on-design turbofan cycle, "
               "self-tested against published engine TSFCs [E]. NOT validated; no off-design, "
               "no BLI distortion penalty, no bleed.",
        "self_tests_vs_published": st,
        "kestrel_turbogenerator_cycle_at_cruise": {**{k2: k[k2] for k2 in ("BPR", "pi_c_OPR", "pi_f_FPR", "Tt4_K", "fuel_air_ratio", "TSFC_lb_lbf_h")},
                                                   "TSFC_lb_lbf_h": round(tsfc_k, 3)},
        "sizing_tsfc_assumption_check": check,
        "sensitivity": {"BPR_sweep": bpr_sweep, "Tt4_sweep_K": tt4_sweep,
                        "note": "higher BPR / higher Tt4 lower TSFC, as published trends show [E]"},
        "fuel_fraction_sensitivity": fuel_sens,
        "fan_loading_check": fan,
        "headline": {
            "cruise_TSFC_computed_lb_lbf_h": round(tsfc_k, 3),
            "vs_sizing_assumption_0.55": check["verdict"],
            "DEP_fan_FPR_implied": dep["FPR_implied"],
            "BLI_fan_FPR_implied": bli["FPR_implied"],
        },
        "caveats": [
            "On-design only: no off-design/spool matching, throttle, or altitude/Mach map.",
            "No BLI inlet-distortion efficiency penalty on the aft fan (real STARC-ABL/D8 work "
            "shows some loss — treat BLI fan numbers as optimistic).",
            "No bleed air, accessories, or installation losses; fully expanded ideal nozzles.",
            "Fan-face velocity 120 m/s is an assumption [T], not a design; FPR values are "
            "order-of-magnitude loading checks, not fan designs.",
            "TSFC in lb/(lbf h) is numerically 1/hr in consistent units — same convention as "
            "lib/sizing.py, so the fuel-fraction sensitivity is directly comparable.",
        ],
    }
    adir = outdir / "analysis"
    adir.mkdir(exist_ok=True)
    path = adir / "propulsion.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print("report:", path)
    for s in st:
        print(f"  self-test {s['point']}: computed {s['computed_TSFC_lb_lbf_h']} vs published {s['published_TSFC_lb_lbf_h [E]']} pass={s['pass']}")
    print(f"  KESTREL cycle TSFC={tsfc_k:.3f} vs assumed 0.55 -> {check['verdict']}")
    print(f"  DEP fan FPR={dep['FPR_implied']}, BLI fan FPR={bli['FPR_implied']}, dMTOW={fuel_sens['dMTOW_pct']}%")
    return out
