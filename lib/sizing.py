"""Order-of-magnitude conceptual sizing (Breguet range + fixed empty-weight fraction).

Every output is a [C] estimate for scheme comparison only — NOT a performance claim.
"""
import json
import math
from pathlib import Path

G = 9.80665  # m/s^2


def speed_of_sound(alt_ft):
    """ISA troposphere speed of sound, m/s."""
    T = 288.15 - 0.0065 * alt_ft * 0.3048
    return math.sqrt(1.4 * 287.05 * T)


def size(p):
    """p keys: name, seats, pax_kg, range_nm, mach, alt_ft, L_D, eta_prop, tsfc_1hr,
    we_frac, span_m, wing_area_m2, n_fans, eta_fan, takeoff_TW."""
    V = p["mach"] * speed_of_sound(p["alt_ft"])          # m/s
    V_kt = V / 0.514444
    R = p["range_nm"]
    c = p["tsfc_1hr"]                                     # 1/hr
    payload_kg = p["seats"] * p["pax_kg"]
    # Breguet (jet form): R_nm = V_kt * (L/D) * eta / c * ln(W0/W1)
    ln_ratio = R * c / (V_kt * p["L_D"] * p["eta_prop"])
    wf = 1.0 - math.exp(-ln_ratio)                        # fuel fraction Wf/W0
    w0 = payload_kg / (1.0 - wf - p["we_frac"])           # kg, converged form
    W = w0 * G                                            # N
    return {
        "scheme": p["name"],
        "method": "Breguet range equation + fixed We/W0 fraction; order-of-magnitude [C] estimates",
        "inputs": p,
        "payload_kg": round(payload_kg),
        "MTOW_kg [C]": round(w0),
        "fuel_fraction [C]": round(wf, 4),
        "cruise_V_mps [C]": round(V, 1),
        "wing_loading_kg_m2 [C]": round(w0 / p["wing_area_m2"], 1),
        "aspect_ratio [C]": round(p["span_m"] ** 2 / p["wing_area_m2"], 2),
        "cruise_drag_N [C]": round(W / p["L_D"]),
        "cruise_TW [C]": round(1.0 / p["L_D"], 4),
        "takeoff_TW [T]": p["takeoff_TW"],
        "per_fan_cruise_power_kW [C]": round(W / p["L_D"] * V / (p["n_fans"] * p["eta_fan"]) / 1000, 1),
    }


def run(outdir, params):
    out = size(params)
    p = Path(outdir) / "sizing.json"
    p.write_text(json.dumps(out, indent=2))
    for k, v in out.items():
        print(f"  {k}: {v}")
    print("report:", p.name)
    return out
