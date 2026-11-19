"""KESTREL-X1 morphing-TE analysis runner — writes analysis/morphing-te.json [C].

CLAIM-2 lives in docs/morphing-te.md. Run from repo root:
    python schemes/kestrel-x1/morph.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root -> lib/
sys.path.insert(0, str(Path(__file__).resolve().parent))       # -> geom.py

import geom
from lib import morph

PARAMS = dict(
    name="kestrel-x1",
    m=0.02, p=0.4,                    # NACA 2412-class scheme profile (as model.py)
    chord_m=geom.CHORD_ROOT,          # root chord 4.6 m
    junction=geom.MORPH_JUNCTION,     # morph starts at 75% chord
    amps=[0.0, 0.005, 0.01, 0.02, 0.03],   # droop amplitude, fraction of chord
    alphas_deg=[0, 5],                # report Cl at 0 and 5 deg (cruise Cl~0.32 ~ 5 deg)
    self_test_alpha_L0_deg=-2.07,     # published [E] alpha_L0 of NACA 2412
)

if __name__ == "__main__":
    morph.run(Path(__file__).parent, PARAMS)
