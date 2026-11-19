# Scheme comparison (A/B)

All values are **[C]** order-of-magnitude conceptual estimates produced by
`compare.py` from each scheme's `sizing.json` and `*-report.json`. This compares
configurations under stated assumptions; it is not a performance measurement.

| metric | kestrel-x1 | nova-bwb |
|---|---|---|
| MTOW_kg [C] | 21601 | 22191 |
| fuel_fraction [C] | 0.1458 | 0.1246 |
| wing_loading_kg_m2 [C] | 288.0 | 233.6 |
| aspect_ratio [C] | 16.33 | 12.89 |
| cruise_V_mps [C] | 179.6 | 185.8 |
| cruise_drag_N [C] | 10592 | 9892 |
| cruise_TW [C] | 0.05 | 0.0455 |
| takeoff_TW [T] | 0.28 | 0.26 |
| per_fan_cruise_power_kW [C] | 159.9 | 696.2 |
| model bbox length (m) | 40.06 | 40.55 |
| model bbox span (m) | 35.05 | 35.12 |
| model bbox height (m) | 5.9 | 4.74 |

## Reading the table

- Same payload (76 pax) and range (1,500 nm) targets for both schemes.
- Differences come only from the configuration assumptions, all visible in each
  scheme's `sizing.py` (wing area, L/D, empty-weight fraction, fan count).
- Per-fan power shows the DEP vs BLI trade: many small fans (kestrel-x1) vs
  few large aft fans (nova-bwb).
