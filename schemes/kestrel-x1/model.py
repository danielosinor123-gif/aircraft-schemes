"""KESTREL-X1 scheme model: truss-braced high-AR wing + 14 trailing-edge DEP fans
(7/side, wake-filling placement) + 1 aft BLI fan position + morphing TE (concept).
Run from anywhere: python schemes/kestrel-x1/model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cadquery as cq
from cadquery import Vector

import geom
from lib import aero

# Strut endpoints stay here (they use cadquery Vector); all airframe/fan/fuselage
# geometry lives in geom.py, shared with analysis.py.
STRUT_ROOT = Vector(-4.0, 0.9, -1.2)
STRUT_TIP = Vector(-1.0, 6.5, -0.30)

wing_r = aero.lofted_wing(geom.LE_X, geom.ROOT_Y, geom.SPAN_HALF,
                          geom.CHORD_ROOT, geom.CHORD_TIP, geom.SWEEP_TIP)
wing_l = aero.mirror_span(wing_r)

fus = aero.fuselage_loft(geom.FUS_SECTIONS)

strut = aero.strut_between(STRUT_ROOT, STRUT_TIP)
strut_l = aero.mirror_span(strut)

fans = [aero.fan_nacelle(geom.te_x(y) - 0.3, y, 0.0, geom.FAN_R, geom.FAN_L)
        for y in geom.FAN_YS]
fans_l = [aero.mirror_span(f) for f in fans]

fin = cq.Workplane("XY").box(3.2, 0.18, 3.0).translate((16.2, 0, 2.6)).val()
stab = cq.Workplane("XY").box(2.4, 6.0, 0.16).translate((16.6, 0, 0.9)).val()

comp = cq.Compound.makeCompound([fus, wing_r, wing_l, strut, strut_l]
                                + fans + fans_l + [fin, stab])

outdir = Path(__file__).parent
aero.export_all(comp, outdir, "kestrel-x1")
aero.write_report(outdir, "kestrel-x1", comp,
                  {"fans_per_side": len(geom.FAN_YS), "strut": True, "te_morphing": True})
