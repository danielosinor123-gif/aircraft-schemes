"""A/B comparison of scheme sizing outputs -> docs/comparison.md.

All numbers are [C] order-of-magnitude estimates from lib/sizing.py —
scheme comparison only, not performance claims.
Run: python compare.py   (after running each scheme's sizing.py)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMES = ["schemes/kestrel-x1", "schemes/nova-bwb"]
KEYS = ["MTOW_kg [C]", "fuel_fraction [C]", "wing_loading_kg_m2 [C]", "aspect_ratio [C]",
        "cruise_V_mps [C]", "cruise_drag_N [C]", "cruise_TW [C]", "takeoff_TW [T]",
        "per_fan_cruise_power_kW [C]"]


def main():
    data = {}
    for s in SCHEMES:
        name = Path(s).name
        data[s] = json.loads((ROOT / s / "sizing.json").read_text())
        data[s]["_report"] = json.loads((ROOT / s / f"{name}-report.json").read_text())

    names = [Path(s).name for s in SCHEMES]
    lines = ["# Scheme comparison (A/B)", "",
             "All values are **[C]** order-of-magnitude conceptual estimates produced by",
             "`compare.py` from each scheme's `sizing.json` and `*-report.json`. This compares",
             "configurations under stated assumptions; it is not a performance measurement.", "",
             "| metric | " + " | ".join(names) + " |",
             "|---|" + "---|" * len(names)]
    for k in KEYS:
        lines.append("| " + k + " | " + " | ".join(str(data[s].get(k, "—")) for s in SCHEMES) + " |")
    for b in ("length", "span", "height"):
        lines.append("| model bbox " + b + " (m) | "
                     + " | ".join(str(data[s]["_report"]["bbox_m"][b]) for s in SCHEMES) + " |")
    lines += ["", "## Reading the table", "",
              "- Same payload (76 pax) and range (1,500 nm) targets for both schemes.",
              "- Differences come only from the configuration assumptions, all visible in each",
              "  scheme's `sizing.py` (wing area, L/D, empty-weight fraction, fan count).",
              "- Per-fan power shows the DEP vs BLI trade: many small fans (kestrel-x1) vs",
              "  few large aft fans (nova-bwb).", ""]
    out = ROOT / "docs" / "comparison.md"
    out.write_text("\n".join(lines))
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
