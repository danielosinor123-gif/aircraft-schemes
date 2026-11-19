"""KESTREL-X1 pure-python geometry parameters — no cadquery import.

Shared by model.py (CAD) and analysis.py (wake-filling claim) so the numbers
and the model can never silently diverge. Units: meters.
Coordinates: x = longitudinal (nose at -x), y = span (+ = right), z = up.
"""

SPAN_HALF = 17.5
ROOT_Y = 1.3
LE_X = -2.0
CHORD_ROOT = 4.6
CHORD_TIP = 1.5
SWEEP_TIP = 1.4
FAN_YS = [3, 5, 7, 9, 11, 13, 15]
FAN_R = 0.32
FAN_L = 1.4
# Fuselage loft sections (x, radius) — single source of truth for model.py
# and for the wake-filling analysis (wetted area, wake station).
FUS_SECTIONS = [(-20, 0.02), (-18, 0.9), (-14, 1.55), (-6, 1.7), (8, 1.7),
                (14, 1.4), (18.5, 0.7), (20, 0.15)]


def chord_at(y):
    f = (y - ROOT_Y) / (SPAN_HALF - ROOT_Y)
    return CHORD_ROOT + (CHORD_TIP - CHORD_ROOT) * f


def te_x(y):
    """Trailing-edge x of the wing at span station y (matches aero.te_x)."""
    f = (y - ROOT_Y) / (SPAN_HALF - ROOT_Y)
    return LE_X + chord_at(y) + SWEEP_TIP * f


def radius_at(x):
    """Fuselage radius at longitudinal station x (linear interp of sections)."""
    xs = [s[0] for s in FUS_SECTIONS]
    if x <= xs[0]:
        return FUS_SECTIONS[0][1]
    if x >= xs[-1]:
        return FUS_SECTIONS[-1][1]
    for (x1, r1), (x2, r2) in zip(FUS_SECTIONS, FUS_SECTIONS[1:]):
        if x1 <= x <= x2:
            f = (x - x1) / (x2 - x1)
            return r1 + (r2 - r1) * f
    return 0.0
