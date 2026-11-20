"""KESTREL-X1 CLAIM-3 runner — gust alleviation via the KESTREL-TE law [C].

Writes analysis/gust-alleviation.json. Run from repo root:
    python schemes/kestrel-x1/gust.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root -> lib/
sys.path.insert(0, str(Path(__file__).resolve().parent))       # -> geom.py

import geom
from lib import gust

# ISA 25,000 ft (same constants as the CFD cases — see docs/cfd-results.md)
RHO = 0.54895
U = 179.61          # M 0.58

if __name__ == "__main__":
    here = Path(__file__).parent
    sizing = json.loads((here / "sizing.json").read_text())
    W_N = sizing["MTOW_kg [C]"] * 9.80665
    S = sizing["inputs"]["wing_area_m2"]
    AR = sizing["aspect_ratio [C]"]
    gust.run(here, dict(
        name="kestrel-x1",
        W_N=W_N, S_m2=S, AR=AR, U_mps=U, rho=RHO,
        chord_m=geom.CHORD_ROOT, junction=geom.MORPH_JUNCTION,
        m=0.02, p=0.4,
    ))
