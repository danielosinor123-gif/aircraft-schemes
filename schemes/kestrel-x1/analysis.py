"""KESTREL-X1 wake-filling analysis runner — writes analysis/wake-filling.json [C].

CLAIM-1 lives in docs/wake-filling.md. Run from repo root:
    python schemes/kestrel-x1/analysis.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root -> lib/
sys.path.insert(0, str(Path(__file__).resolve().parent))       # -> geom.py

import geom
from lib import wake_filling

PARAMS = dict(
    name="kestrel-x1",
    mach=0.58, alt_ft=25000, eta_fan=0.85,
    FUS_SECTIONS=geom.FUS_SECTIONS,
    FAN_YS=geom.FAN_YS, FAN_R=geom.FAN_R, FAN_L=geom.FAN_L,
    te_x=geom.te_x,
    radius_at=geom.radius_at,
    wake_spread=0.05,            # A5: axisymmetric turbulent wake half-angle
    bli_station_x=18.5,          # A6: aft BLI fan station (tail cone)
    bli_fan_r=0.9,               # A6: aft fan disc radius [T]
    thrust_splits=[0.3, 0.5, 0.7],  # aft-fan share of cruise thrust (sensitivity)
)

if __name__ == "__main__":
    wake_filling.run(Path(__file__).parent, PARAMS)
