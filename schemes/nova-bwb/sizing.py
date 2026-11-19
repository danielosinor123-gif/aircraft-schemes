"""NOVA-BWB conceptual sizing inputs. All outputs are [C] estimates."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib import sizing

PARAMS = dict(
    name="nova-bwb",
    seats=76, pax_kg=95, range_nm=1500, mach=0.60, alt_ft=25000,
    L_D=22, eta_prop=0.78, tsfc_1hr=0.55, we_frac=0.55,
    span_m=35.0, wing_area_m2=95.0,
    n_fans=3, eta_fan=0.88, takeoff_TW=0.26,
)

if __name__ == "__main__":
    sizing.run(Path(__file__).parent, PARAMS)
