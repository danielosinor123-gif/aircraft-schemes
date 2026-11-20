"""KESTREL-X1 ECON-1 runner — is electric actually cheap? [C].

Writes analysis/energy-cost.json. Run from repo root:
    python schemes/kestrel-x1/econ.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root -> lib/

from lib import econ

if __name__ == "__main__":
    here = Path(__file__).parent
    sizing = json.loads((here / "sizing.json").read_text())
    fuel_kg = sizing["fuel_fraction [C]"] * sizing["MTOW_kg [C]"]
    econ.run(here, dict(name="kestrel-x1", fuel_kg_per_mission=fuel_kg))
