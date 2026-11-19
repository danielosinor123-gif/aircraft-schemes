"""KESTREL-X1 scheme model: truss-braced high-AR wing + 14 trailing-edge DEP fans
(7/side, wake-filling placement) + 1 aft BLI fan position + morphing TE (concept).
Run from anywhere: python schemes/kestrel-x1/model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cadquery as cq
from cadquery import Vector

from lib import aero

P = dict(
    SPAN_HALF=17.5, ROOT_Y=1.3, LE_X=-2.0,
    CHORD_ROOT=4.6, CHORD_TIP=1.5, SWEEP_TIP=1.4,
    FAN_YS=[3, 5, 7, 9, 11, 13, 15], FAN_R=0.32, FAN_L=1.4,
    STRUT_ROOT=Vector(-4.0, 0.9, -1.2), STRUT_TIP=Vector(-1.0, 6.5, -0.30),
)

wing_r = aero.lofted_wing(P["LE_X"], P["ROOT_Y"], P["SPAN_HALF"],
                          P["CHORD_ROOT"], P["CHORD_TIP"], P["SWEEP_TIP"])
wing_l = aero.mirror_span(wing_r)

fus = aero.fuselage_loft([(-20, 0.02), (-18, 0.9), (-14, 1.55), (-6, 1.7), (8, 1.7),
                          (14, 1.4), (18.5, 0.7), (20, 0.15)])

strut = aero.strut_between(P["STRUT_ROOT"], P["STRUT_TIP"])
strut_l = aero.mirror_span(strut)

fans = [aero.fan_nacelle(
            aero.te_x(P["LE_X"], y, P["ROOT_Y"], P["SPAN_HALF"],
                      P["CHORD_ROOT"], P["CHORD_TIP"], P["SWEEP_TIP"]) - 0.3,
            y, 0.0, P["FAN_R"], P["FAN_L"]) for y in P["FAN_YS"]]
fans_l = [aero.mirror_span(f) for f in fans]

fin = cq.Workplane("XY").box(3.2, 0.18, 3.0).translate((16.2, 0, 2.6)).val()
stab = cq.Workplane("XY").box(2.4, 6.0, 0.16).translate((16.6, 0, 0.9)).val()

comp = cq.Compound.makeCompound([fus, wing_r, wing_l, strut, strut_l]
                                + fans + fans_l + [fin, stab])

outdir = Path(__file__).parent
aero.export_all(comp, outdir, "kestrel-x1")
aero.write_report(outdir, "kestrel-x1", comp,
                  {"fans_per_side": len(P["FAN_YS"]), "strut": True, "te_morphing": True})
