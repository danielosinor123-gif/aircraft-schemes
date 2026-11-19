"""KESTREL-X1 conceptual sizing inputs. All outputs are [C] estimates."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib import sizing

PARAMS = dict(
    name="kestrel-x1",
    seats=76, pax_kg=95, range_nm=1500, mach=0.58, alt_ft=25000,
    L_D=20, eta_prop=0.75, tsfc_1hr=0.55, we_frac=0.52,
    span_m=35.0, wing_area_m2=75.0,
    n_fans=14, eta_fan=0.85, takeoff_TW=0.28,
)

if __name__ == "__main__":
    sizing.run(Path(__file__).parent, PARAMS)
