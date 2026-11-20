"""Electric-and-cheap check for KESTREL-X1 [C]: what does energy actually cost?

Compares jet fuel vs grid electricity per kWh, computes the energy cost of one
design mission (fuel mass from sizing.json), the break-even electricity price,
and the battery mass penalty vs jet fuel. All inputs are published-typical
values tagged [E]; outputs are [C] arithmetic on them.

Self-test: jet fuel must land at $0.05-0.12/kWh (typical Jet A $0.55-1.10/L,
~9.6 kWh/L). Recorded in the JSON; run() refuses to emit if it fails.

Honest expectation (verified when run): at an industrial electricity price of
~$0.10/kWh, battery-electric energy is MORE expensive than jet fuel per kWh —
the real electric wins are emissions, noise, and maintenance, not energy cost,
unless electricity is cheap (off-peak/renewables ~$0.03-0.05/kWh).
"""
import json
from pathlib import Path

# published-typical inputs [E] (verify before citing):
JET_LHV_MJ_KG = 43.0        # Jet A lower heating value
JET_DENSITY_KG_L = 0.80     # Jet A density
JET_PRICE_USD_L = 0.70      # typical range $0.55-1.10/L
ELEC_PRICE_USD_KWH = 0.10   # US industrial average, range ~$0.08-0.13
BATTERY_KWH_KG = 0.25       # current Li-ion pack-level gravimetric energy
KWH_PER_MJ = 1.0 / 3.6


def run(outdir, P):
    """P keys: name, fuel_kg_per_mission."""
    outdir = Path(outdir)
    fuel_kg = P["fuel_kg_per_mission"]

    kwh_per_kg_fuel = JET_LHV_MJ_KG * KWH_PER_MJ          # 11.94 kWh/kg
    kwh_per_L = kwh_per_kg_fuel * JET_DENSITY_KG_L         # 9.56 kWh/L
    jet_usd_per_kwh = JET_PRICE_USD_L / kwh_per_L

    self_test = {"jet_usd_per_kwh": round(jet_usd_per_kwh, 4),
                 "expected_range": [0.05, 0.12],
                 "pass": 0.05 <= jet_usd_per_kwh <= 0.12}
    if not self_test["pass"]:
        raise SystemExit("econ self-test FAILED — check input prices")

    mission_kwh = fuel_kg * kwh_per_kg_fuel
    cost_fuel = mission_kwh * jet_usd_per_kwh
    cost_elec = mission_kwh * ELEC_PRICE_USD_KWH
    breakeven_elec = jet_usd_per_kwh
    battery_kg_per_fuel_kg = kwh_per_kg_fuel / BATTERY_KWH_KG   # ~48x heavier per kWh

    out = {
        "scheme": P["name"],
        "claim_id": "ECON-1",
        "tag": "[C] arithmetic on published-typical input prices [E] — NOT a DOC model. "
               "KESTREL-X1 is HYBRID-electric (turbo-generators burn fuel, battery is a buffer); "
               "the battery-electric comparison below is the all-electric bound.",
        "inputs_E": {
            "jet_LHV_MJ_per_kg": JET_LHV_MJ_KG, "jet_density_kg_per_L": JET_DENSITY_KG_L,
            "jet_price_usd_per_L": JET_PRICE_USD_L, "elec_price_usd_per_kwh": ELEC_PRICE_USD_KWH,
            "battery_kwh_per_kg_pack": BATTERY_KWH_KG,
            "note": "typical published values, ranges in comments — verify before citing",
        },
        "derived": {
            "kwh_per_kg_jet_fuel": round(kwh_per_kg_fuel, 2),
            "kwh_per_L_jet": round(kwh_per_L, 2),
            "jet_usd_per_kwh": round(jet_usd_per_kwh, 4),
            "battery_kg_per_kg_fuel_replaced": round(battery_kg_per_fuel_kg, 1),
        },
        "self_test": self_test,
        "mission": {
            "fuel_kg_per_design_mission [C from sizing.json]": round(fuel_kg, 0),
            "energy_kwh": round(mission_kwh, 0),
            "cost_usd_if_jet_fuel": round(cost_fuel, 0),
            "cost_usd_if_grid_electric": round(cost_elec, 0),
            "electric_over_fuel_ratio": round(cost_elec / cost_fuel, 3),
            "breakeven_elec_price_usd_per_kwh": round(breakeven_elec, 4),
        },
        "verdict": (
            f"At ${ELEC_PRICE_USD_KWH:.2f}/kWh grid power, battery-electric energy costs "
            f"{round(cost_elec/cost_fuel,2)}x jet fuel per mission — NOT cheaper on energy alone [C]. "
            f"Electric wins on energy price only below ${round(breakeven_elec,3)}/kWh (off-peak / "
            "renewables). The honest case for the hybrid-electric layout is emissions, noise, and "
            "maintenance — plus the ~48x mass penalty per kWh is why full battery-electric is hard "
            "for a 1,500 nm mission. 'Cheap' is therefore a [T] target with conditions, not a result."
        ),
        "caveats": [
            "Energy price only — excludes maintenance, engine overhaul, battery replacement cycles, "
            "and carbon pricing, which can flip the comparison (published direction: electric wins "
            "more as carbon prices rise) [E, verify].",
            "KESTREL-X1 as configured is hybrid-electric: the 2 turbo-generators burn Jet A; the "
            "battery is a takeoff/climb buffer, so its mission energy is mostly jet fuel today.",
            "Prices are point values with ranges in comments; recompute with current prices before "
            "any real use.",
        ],
    }
    adir = outdir / "analysis"
    adir.mkdir(exist_ok=True)
    path = adir / "energy-cost.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print("report:", path)
    print(f"  self-test pass={self_test['pass']}  jet=${jet_usd_per_kwh:.4f}/kWh  "
          f"elec=${ELEC_PRICE_USD_KWH}/kWh  ratio={cost_elec/cost_fuel:.2f}x  breakeven=${breakeven_elec:.3f}/kWh")
    return out
