"""KESTREL-X1 PROP-1 runner — turbofan cycle + propulsion sizing [C].

Writes analysis/propulsion.json. Run from repo root:
    python schemes/kestrel-x1/propulsion.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root -> lib/
sys.path.insert(0, str(Path(__file__).resolve().parent))       # -> geom.py

import geom
from lib import engine

if __name__ == "__main__":
    here = Path(__file__).parent
    sizing = json.loads((here / "sizing.json").read_text())
    inp = sizing["inputs"]
    engine.run(here, dict(
        name="kestrel-x1",
        cruise=dict(
            alt_m=inp["alt_ft"] * 0.3048, M=inp["mach"], pi_d=0.98,
            BPR=9.0, pi_c=45.0, pi_f=1.55, Tt4=1750.0,      # turbo-generator cycle [T]
            tsfc_assumed_lb=inp["tsfc_1hr"],                # the 0.55 baked into sizing.py
        ),
        sizing=dict(
            cruise_drag_N=sizing["cruise_drag_N [C]"],
            cruise_V_mps=sizing["cruise_V_mps [C]"],
            eta_fan=inp["eta_fan"], eta_prop=inp["eta_prop"],
            L_D=inp["L_D"], range_nm=inp["range_nm"],
            payload_kg=sizing["payload_kg"], we_frac=inp["we_frac"],
            per_fan_cruise_power_kW=sizing["per_fan_cruise_power_kW [C]"],
            n_dep_fans=inp["n_fans"], fan_d_m=2 * geom.FAN_R,
            rho=0.54895,                                     # ISA 25,000 ft
        ),
        bli_fan_d_m=1.8,      # aft BLI fan disc diameter [T] (tail cone ~1.4 m radius max)
        bli_power_frac=0.5,   # aft-fan share of cruise propulsive power (CLAIM-1 mid case)
    ))
