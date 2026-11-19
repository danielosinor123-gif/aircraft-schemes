"""NOVA-BWB scheme model: blended wing body, 3 aft boundary-layer-ingesting fans,
winglets, no truss. A/B comparison partner to kestrel-x1.
Run: python schemes/nova-bwb/model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cadquery as cq

from lib import aero

P = dict(SPAN_HALF=17.5, ROOT_Y=2.0, LE_X=-4.0,
         CHORD_ROOT=7.0, CHORD_TIP=1.2, SWEEP_TIP=2.0)

body = aero.fuselage_loft([(-20, 0.02), (-17, 1.2), (-12, 2.2), (-4, 2.3), (6, 2.3),
                           (13, 2.0), (18, 1.2), (20.5, 0.2)])

wing_r = aero.lofted_wing(P["LE_X"], P["ROOT_Y"], P["SPAN_HALF"],
                          P["CHORD_ROOT"], P["CHORD_TIP"], P["SWEEP_TIP"])
wing_l = aero.mirror_span(wing_r)

bli_fans = [aero.fan_nacelle(17.0, y, 1.0, 0.85, 2.0) for y in (-2.2, 0.0, 2.2)]

winglet_r = cq.Workplane("XY").box(0.9, 0.12, 1.6).translate(
    (P["LE_X"] + P["SWEEP_TIP"] + P["CHORD_TIP"] - 0.45, P["SPAN_HALF"], 0.8)).val()
winglet_l = aero.mirror_span(winglet_r)

comp = cq.Compound.makeCompound([body, wing_r, wing_l] + bli_fans + [winglet_r, winglet_l])

outdir = Path(__file__).parent
aero.export_all(comp, outdir, "nova-bwb")
aero.write_report(outdir, "nova-bwb", comp,
                  {"fans_aft_bli": 3, "strut": False, "te_morphing": True})
