"""Wake-filling benefit analysis for KESTREL-X1 — the scheme's one computed claim.

CLAIM-1 (full method + assumptions in docs/wake-filling.md): at the M0.58 /
25,000 ft cruise point, wake filling as configured is worth only a few percent
of cruise propulsive power, and it is dominated by the aft BLI fan — the
trailing-edge wing-body-junction fans contribute <0.1% and are packaging-driven,
not physics-driven.

Every number produced here is a [C] order-of-magnitude estimate, NOT a result.
Pure python (no cadquery) so CI can run it in the dependency-free job.

Physics chain:
  ISA atmosphere (A1)
  -> fuselage wetted area from the CAD section table (A2)
  -> turbulent flat-plate Cf (A3) -> fuselage drag D_fus
  -> momentum-normalized Gaussian wake at each TE fan inlet (A4, A5)
  -> velocity deficit dV at each fan (A6)
  -> ideal-fan power saving dP = T * dV (exact for an ideal propulsor)
  -> aft BLI fan ingesting the tail boundary layer (mass-averaged deficit).
"""
import json
import math
from pathlib import Path

R_AIR = 287.05
G0 = 9.80665


def isa(alt_ft):
    """ISA troposphere: T, p, rho, mu (Sutherland), nu, speed of sound."""
    T = 288.15 - 0.0065 * alt_ft * 0.3048
    p = 101325.0 * (T / 288.15) ** 5.2559
    rho = p / (R_AIR * T)
    mu = 1.716e-5 * (T / 273.15) ** 1.5 * (273.15 + 110.4) / (T + 110.4)
    return {"T_K": round(T, 2), "p_Pa": round(p, 1), "rho_kg_m3": round(rho, 5),
            "mu": mu, "nu_m2_s": round(mu / rho, 8), "a_mps": round(math.sqrt(1.4 * R_AIR * T), 2)}


def cf_turbulent(Re):
    """Turbulent flat-plate skin-friction coefficient (Prandtl-Schlichting)."""
    return 0.455 / (math.log10(Re) ** 2.58)


def theta_turbulent(x, V, nu):
    """(momentum thickness theta, Re_x) for a turbulent flat plate, zero PG."""
    Re_x = V * x / nu
    return 0.036 * x * Re_x ** (-0.2), Re_x


def fuselage_wetted_area(sections):
    """Lateral area of a lofted body of revolution from (x, r) sections."""
    a = 0.0
    for (x1, r1), (x2, r2) in zip(sections, sections[1:]):
        a += math.pi * (r1 + r2) * math.hypot(x2 - x1, r2 - r1)
    return a


def wake_peak_deficit(D, rho, U, half_width, sigma):
    """Peak dV0 of a Gaussian wake dV(y) = dV0*exp(-y^2/(2 sigma^2)), normalized
    so the momentum-deficit flux equals the body drag:
        D = rho * U * h * integral(dV dy),   h = 2*half_width (vertical extent)."""
    h = 2.0 * half_width
    return D / (rho * U * h * sigma * math.sqrt(2.0 * math.pi))


def deficit_at(y, dV0, sigma):
    return dV0 * math.exp(-(y * y) / (2.0 * sigma * sigma))


def run(outdir, P):
    """P keys: name, mach, alt_ft, eta_fan, FUS_SECTIONS, FAN_YS, FAN_R, FAN_L,
    te_x (callable), wake_spread, bli_station_x, bli_fan_r, thrust_splits."""
    outdir = Path(outdir)
    atm = isa(P["alt_ft"])
    nu = atm["nu_m2_s"]
    U = P["mach"] * atm["a_mps"]
    rho = atm["rho_kg_m3"]
    q = 0.5 * rho * U * U

    sizing = json.loads((outdir / "sizing.json").read_text())
    D = sizing["cruise_drag_N [C]"]
    P_total = D * U / P["eta_fan"]          # cruise propulsive power, W
    n_te = 2 * len(P["FAN_YS"])              # both wings

    # --- fuselage drag (A2, A3: wetted area x flat-plate Cf, no form factor) ---
    fus = P["FUS_SECTIONS"]
    x_nose, x_tail = fus[0][0], fus[-1][0]
    L = x_tail - x_nose
    Swet = fuselage_wetted_area(fus)
    Re_L = U * L / nu
    Cf = cf_turbulent(Re_L)
    D_fus = q * Cf * Swet

    # --- fuselage wake at each TE fan inlet (A4-A6) ---
    R_max = max(r for _, r in fus)
    s = P["wake_spread"]
    fans = []
    for y in P["FAN_YS"]:
        x_in = P["te_x"](y) - 0.3 - P["FAN_L"] / 2.0      # fan inlet plane
        dist = x_in - x_nose
        b = R_max + s * dist                               # wake half-width
        sigma = b / 2.0
        dV0 = wake_peak_deficit(D_fus, rho, U, b, sigma)
        dV = deficit_at(y, dV0, sigma)
        fans.append({"y_m": y, "x_inlet_m": round(x_in, 2),
                     "wake_halfwidth_m": round(b, 3),
                     "peak_deficit_mps": round(dV0, 4),
                     "deficit_at_fan_mps": round(dV, 4),
                     "deficit_frac_of_U": round(dV / U, 6)})

    # --- aft BLI fan ingesting the tail boundary layer (A6) ---
    x_bli = P["bli_station_x"]
    r_surf = P["radius_at"](x_bli)
    r_fan = P["bli_fan_r"]
    theta, Re_bli = theta_turbulent(x_bli - x_nose, U, nu)
    A_fan = math.pi * r_fan ** 2
    P_bl = 2.0 * math.pi * r_surf
    # mass-averaged deficit over the fan disc: momentum flux rho*U^2*theta*P_bl
    # spread over the fan area
    dV_bli = U * theta * P_bl / A_fan

    # --- benefits per aft-fan thrust split phi ---
    sens = []
    for phi in P["thrust_splits"]:
        T_aft = phi * D
        dP_aft = T_aft * dV_bli                        # dP = T * dV (ideal fan)
        T_fan = (1.0 - phi) * D / n_te
        dP_te = sum(2 * T_fan * f["deficit_at_fan_mps"] for f in fans)  # +/- y
        dP_tot = dP_aft + dP_te
        sens.append({"aft_thrust_split": phi,
                     "T_aft_N": round(T_aft, 1),
                     "dP_aft_kW": round(dP_aft / 1000.0, 3),
                     "dP_te_fans_kW": round(dP_te / 1000.0, 4),
                     "dP_total_kW": round(dP_tot / 1000.0, 3),
                     "pct_of_propulsive_power": round(100.0 * dP_tot / P_total, 3)})

    base = next(s for s in sens if s["aft_thrust_split"] == 0.5) \
        if any(s["aft_thrust_split"] == 0.5 for s in sens) else sens[len(sens) // 2]

    out = {
        "scheme": P["name"],
        "claim_id": "CLAIM-1",
        "tag": "[C] computed in-repo by lib/wake_filling.py — order-of-magnitude, NOT validated",
        "claim": ("At the M0.58 / 25,000 ft cruise point, wake filling as configured is worth "
                  f"~{base['pct_of_propulsive_power']}% of cruise propulsive power, dominated by the "
                  "aft BLI fan; the TE wing-body-junction fans contribute <0.1% (packaging-driven, "
                  "not physics-driven). Falsifiable via CFD with actuator-disc fans or a wind-tunnel "
                  "wake survey — see docs/wake-filling.md."),
        "atmosphere_isa": atm,
        "cruise": {"U_mps": round(U, 2), "q_Pa": round(q, 1), "rho": rho, "nu": nu},
        "inputs": {k: v for k, v in P.items() if not callable(v)},
        "fuselage": {"length_m": L, "wetted_area_m2": round(Swet, 1), "Re_L": round(Re_L),
                     "Cf": round(Cf, 6), "drag_N": round(D_fus, 1),
                     "share_of_total_drag": round(D_fus / D, 4)},
        "total_cruise": {"drag_N": D, "propulsive_power_kW": round(P_total / 1000.0, 1),
                         "n_te_fans": n_te, "te_fan_thrust_N_at_phi_0.5": round(0.5 * D / n_te, 1)},
        "te_fans_in_fuselage_wake": fans,
        "aft_bli_fan": {"station_x_m": x_bli, "fuselage_r_m": round(r_surf, 3),
                        "fan_r_m": r_fan, "fan_area_m2": round(A_fan, 3),
                        "theta_m": round(theta, 5), "Re_at_station": round(Re_bli),
                        "avg_ingested_deficit_mps": round(dV_bli, 3),
                        "deficit_frac_of_U": round(dV_bli / U, 4)},
        "sensitivity_aft_thrust_split": sens,
        "baseline": base,
        "method_notes": [
            "dP = T * dV is exact for an ideal propulsor ingesting a streamtube with velocity deficit dV (derived in docs/wake-filling.md).",
            "Wake model: Gaussian in span, momentum-normalized to fuselage drag; spreading half-angle s = wake_spread.",
            "Aft BLI: fan disc at the tail cone ingests the fuselage boundary layer; deficit = U*theta*P_bl/A_fan.",
            "TE fans also ingest the wing wake at any span station (baseline DEP effect, not placement-dependent) — out of scope for this claim.",
        ],
    }
    adir = outdir / "analysis"
    adir.mkdir(exist_ok=True)
    p = adir / "wake-filling.json"
    p.write_text(json.dumps(out, indent=2) + "\n")
    print("report:", p)
    print(f"  baseline: {base['pct_of_propulsive_power']}% of propulsive power "
          f"(aft BLI {base['dP_aft_kW']} kW + TE fans {base['dP_te_fans_kW']} kW)")
    return out
