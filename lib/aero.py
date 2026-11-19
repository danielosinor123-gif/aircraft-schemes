"""Shared geometry helpers for aircraft-schemes. Units: meters.

Coordinates: x = longitudinal (nose at -x, tail at +x), y = span (+ = right), z = up.
All models are SCHEME models: proportions only, not aerodynamic surfaces.
"""
import json
import math
from pathlib import Path

import cadquery as cq
from cadquery import Vector


def naca4(m, p, t, chord, n=48):
    """Closed NACA 4-digit profile loop as (x, z) points, LE at x=0, chord along +x."""
    up, lo = [], []
    for i in range(n + 1):
        b = math.pi * i / n
        u = 0.5 * (1 - math.cos(b))
        x = u * chord
        yt = 5 * t * chord * (0.2969 * math.sqrt(u) - 0.1260 * u - 0.3516 * u**2
                              + 0.2843 * u**3 - 0.1036 * u**4)
        if u < p:
            yc = m / p**2 * (2 * p * u - u**2) * chord
            dyc = 2 * m / p**2 * (p - u)
        else:
            yc = m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * u - u**2) * chord
            dyc = 2 * m / (1 - p)**2 * (p - u)
        th = math.atan(dyc)
        up.append((x - yt * math.sin(th), yc + yt * math.cos(th)))
        lo.append((x + yt * math.sin(th), yc - yt * math.cos(th)))
    return up + lo[::-1]


def chord_at(y, root_y, tip_y, chord_root, chord_tip):
    f = (y - root_y) / (tip_y - root_y)
    return chord_root + (chord_tip - chord_root) * f


def wing_wire(le_x, y, root_y, tip_y, chord_root, chord_tip, sweep_tip,
              m=0.02, p=0.4, t=0.12):
    f = (y - root_y) / (tip_y - root_y)
    sw = sweep_tip * f
    pts = naca4(m, p, t, chord_at(y, root_y, tip_y, chord_root, chord_tip))
    return cq.Wire.makePolygon([Vector(le_x + sw + x, y, z) for x, z in pts], close=True)


def lofted_wing(le_x, root_y, tip_y, chord_root, chord_tip, sweep_tip, **kw):
    """Right wing solid lofted root->tip. Caller mirrors for the left side."""
    return cq.Solid.makeLoft([
        wing_wire(le_x, root_y, root_y, tip_y, chord_root, chord_tip, sweep_tip, **kw),
        wing_wire(le_x, tip_y, root_y, tip_y, chord_root, chord_tip, sweep_tip, **kw)])


def fuselage_loft(sections):
    """sections: list of (x, radius); circular sections normal to x."""
    return cq.Solid.makeLoft([cq.Wire.makeCircle(r, Vector(x, 0, 0), Vector(1, 0, 0))
                              for x, r in sections])


def mirror_span(shape):
    """Mirror across the XZ plane (y -> -y). NOTE: mirror("YZ") flips x, not y —
    see docs/BUGS.md entry BUG-2026-11-19-01."""
    return shape.mirror("XZ")


def strut_between(p1, p2, radius=0.14):
    d = p2 - p1
    return cq.Solid.makeCylinder(radius, d.Length, p1, d.normalized())


def fan_nacelle(x_center, y, z, radius, length):
    """Ducted fan nacelle: cylinder with axis along x."""
    return cq.Solid.makeCylinder(radius, length,
                                 Vector(x_center - length / 2, y, z), Vector(1, 0, 0))


def te_x(le_x, y, root_y, tip_y, chord_root, chord_tip, sweep_tip):
    f = (y - root_y) / (tip_y - root_y)
    return le_x + chord_at(y, root_y, tip_y, chord_root, chord_tip) + sweep_tip * f


def export_all(comp, outdir, base,
               views=(("view-top", (0, -1, 0), 1400, 500),
                      ("view-side", (1, 0, 0), 1400, 400),
                      ("view-front", (0, 0, 1), 700, 500))):
    outdir = Path(outdir)
    cq.exporters.export(comp, str(outdir / (base + ".step")))
    cq.exporters.export(comp, str(outdir / (base + ".stl")))
    for name, pdir, w, h in views:
        cq.exporters.export(comp, str(outdir / (name + ".svg")), opt={
            "projectionDir": pdir, "width": w, "height": h,
            "marginLeft": 30, "marginTop": 30, "showAxes": False,
            "strokeWidth": 0.35, "showHidden": True})
        print("saved", name + ".svg")


def write_report(outdir, name, comp, extra=None):
    bb = comp.BoundingBox()
    rep = {"scheme": name,
           "bbox_m": {"length": round(bb.xlen, 2), "span": round(bb.ylen, 2),
                      "height": round(bb.zlen, 2)},
           "solids": len(comp.Solids()),
           "note": "scheme model; proportions only, not aerodynamic surfaces"}
    if extra:
        rep.update(extra)
    p = Path(outdir) / (name + "-report.json")
    p.write_text(json.dumps(rep, indent=2))
    print("report:", p.name, rep["bbox_m"], "solids:", rep["solids"])
    return rep
