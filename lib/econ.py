"""Electric-and-cheap check for KESTREL-X1 [C]: what does energy actually cost?

Compares jet fuel vs grid electricity per kWh, computes the energy cost of one
design mission (fuel mass from sizing.json), the break-even electricity price,
and the battery mass penalty vs jet fuel. All inputs are published-typical
values tagged [E]; outputs are [C] arithmetic on them.

Self-test: jet fuel must land at $0.08-0.30/kWh (Nov-2026 wholesale spot ~$0.124/kWh;
FBO retail up to ~$0.25/kWh). Recorded in the JSON; run() refuses to emit if it fails.

2026-11-21 verified inputs (see BUGS.md PROV-2026-11-21-07): EIA Gulf Coast Jet A spot
$4.48/gal (Nov 2026) = $1.18/L and EIA U.S. industrial electricity 9.64 c/kWh (Aug 2026)
mean grid electricity is now CHEAPER per kWh than wholesale jet fuel — the verdict below
reflects that. Prices move; recompute before any real use.
"""
import json
from pathlib import Path

# published-typical inputs [E] — verified via web sources 2026-11-21 (PROV-2026-11-21-07):
# Jet A wholesale spot ~$4.48/gal U.S. Gulf Coast (EIA, Nov 2026) = $1.18/L; FBO retail much
# higher ($8.5-9.34/gal, Aviation Week/GlobalAir Nov 2026); IATA global $169.82/bbl. Base = wholesale.
# Electricity: U.S. industrial average 9.64 c/kWh (EIA, Aug 2026); state range ~4-39 c/kWh.
JET_LHV_MJ_KG = 43.0        # Jet A lower heating value
JET_DENSITY_KG_L = 0.80     # Jet A density
JET_PRICE_USD_L = 4.48 / 3.78541   # EIA Gulf Coast spot $4.48/gal, Nov 2026 -> $/L
ELEC_PRICE_USD_KWH = 0.0964         # EIA U.S. industrial average, Aug 2026
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
                 "expected_range": [0.08, 0.30],
                 "pass": 0.08 <= jet_usd_per_kwh <= 0.30}
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
            f"At the Nov-2026 verified prices (jet ${jet_usd_per_kwh:.3f}/kWh wholesale, grid "
            f"${ELEC_PRICE_USD_KWH:.4f}/kWh industrial), battery-electric energy costs "
            f"{round(cost_elec/cost_fuel,2)}x jet fuel per mission [C] — grid power is now CHEAPER per "
            f"kWh than wholesale Jet A (break-even ${round(breakeven_elec,3)}/kWh), and FBO retail jet "
            "pushes further. BUT the ~48x battery mass penalty per kWh means an all-battery 1,500 nm "
            "mission is still not viable; the honest case for KESTREL's HYBRID-electric layout is "
            "cheaper energy + emissions + noise + maintenance, with the battery as a buffer. "
            "'Cheap' is price-dependent: recompute with current prices before relying on it."
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
