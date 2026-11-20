"""Compute pressure force coefficients on a wall patch from an OpenFOAM case,
by integrating the solved pressure field over the patch faces (polyMesh geometry).

Usage: python3 calc_forces.py <case_dir> <patch> <rho> <U> <Aref> <time_dir> [alpha_deg]
Prints JSON with pressure forces only (viscous drag is estimated separately).
alpha_deg rotates the drag/lift projection axes (inflow in the x-z plane).
"""
import json
import math
import re
import sys
from pathlib import Path


def tokenize(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"//[^\n]*", "", s)
    s = s.replace(";", " ")
    for a, b in [("{", " { "), ("}", " } "), ("(", " ( "), (")", " ) ")]:
        s = s.replace(a, b)
    return s.split()


def parse(tokens, i=0):
    tok = tokens[i]
    if tok in ("(", "{"):
        close = ")" if tok == "(" else "}"
        lst = []
        i += 1
        while tokens[i] != close:
            v, i = parse(tokens, i)
            lst.append(v)
        return lst, i + 1
    for conv in (int, float):
        try:
            return conv(tok), i + 1
        except ValueError:
            pass
    return tok, i + 1


def load(path):
    toks = tokenize(Path(path).read_text())
    vals, i = [], 0
    while i < len(toks):
        v, i = parse(toks, i)
        vals.append(v)
    return vals


def find_first(obj, pred):
    if isinstance(obj, list):
        if pred(obj):
            return obj
        for v in obj:
            r = find_first(v, pred)
            if r is not None:
                return r
    return None


def find_key(obj, key):
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            if v == key and i + 1 < len(obj):
                return obj[i + 1]
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def main():
    case, patch = sys.argv[1], sys.argv[2]
    rho, U, Aref, tdir = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
    alpha_deg = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0   # AoA: inflow rotated in x-z plane
    pm = Path(case) / "constant" / "polyMesh"

    raw = load(pm / "points")
    pts = find_first(raw, lambda v: v and isinstance(v[0], list) and len(v[0]) == 3
                     and all(isinstance(c, float) for c in v[0]))
    raw = load(pm / "faces")
    raw_faces = find_first(raw, lambda v: len(v) > 200 and isinstance(v, list)
                           and all(isinstance(v[i], int) for i in range(0, len(v), 2))
                           and all(isinstance(v[i], list) for i in range(1, len(v), 2)))
    faces = [raw_faces[i] for i in range(1, len(raw_faces), 2)]
    raw = load(pm / "boundary")
    patches = find_first(raw, lambda v: len(v) > 4 and isinstance(v[0], str) and v[0] != "FoamFile"
                         and isinstance(v[1], list) and all(isinstance(v[i], str) and isinstance(v[i + 1], list) for i in range(0, len(v), 2)))
    idx = patches.index(patch)
    info = patches[idx + 1]
    start = find_key(info, "startFace")
    n = find_key(info, "nFaces")

    def big_numeric(obj):
        best = None
        if isinstance(obj, list):
            if obj and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in obj) and len(obj) > 100:
                if best is None or len(obj) > len(best):
                    best = obj
            for v in obj:
                r = big_numeric(v)
                if r is not None and (best is None or len(r) > len(best)):
                    best = r
        return best

    pfield = load(Path(case) / tdir / "p")
    pvals = big_numeric(pfield)
    owner_raw = load(pm / "owner")
    owner = big_numeric(owner_raw)
    assert pvals is not None and owner is not None and len(owner) >= start + n
    vals = [pvals[owner[start + k]] for k in range(n)]  # zeroGradient: wall p = owner-cell p

    F = [0.0, 0.0, 0.0]
    area = 0.0
    for k in range(n):
        fv = faces[start + k]
        sf = [0.0, 0.0, 0.0]
        m = len(fv)
        for i in range(m):
            p1, p2 = pts[fv[i]], pts[fv[(i + 1) % m]]
            sf[0] += p1[1] * p2[2] - p1[2] * p2[1]
            sf[1] += p1[2] * p2[0] - p1[0] * p2[2]
            sf[2] += p1[0] * p2[1] - p1[1] * p2[0]
        sf = [0.5 * c for c in sf]
        for c in range(3):
            F[c] += vals[k] * sf[c]   # boundary Sf points out of fluid (into body): F_body = rho * sum(p*Sf)
        area += sum(c * c for c in sf) ** 0.5

    F = [rho * c for c in F]           # p is kinematic pressure [m^2/s^2]

    q = 0.5 * rho * U * U
    a = math.radians(alpha_deg)
    drag_dir = (math.cos(a), 0.0, math.sin(a))     # along the inflow
    lift_dir = (-math.sin(a), 0.0, math.cos(a))    # perpendicular, +z at alpha=0
    Fd = sum(F[i] * drag_dir[i] for i in range(3))
    Fl = sum(F[i] * lift_dir[i] for i in range(3))
    print(json.dumps({
        "patch": patch, "nFaces": n, "patch_area_m2": round(area, 2),
        "alpha_deg": alpha_deg,
        "F_pressure_N": [round(c, 2) for c in F], "q_Pa": round(q, 1),
        "Cd_pressure": round(Fd / (q * Aref), 5),
        "Cl_pressure": round(Fl / (q * Aref), 5),
        "note": "pressure forces integrated from solved p, projected onto flow-aligned "
                "drag/lift axes; viscous drag estimated separately",
    }, indent=2))


if __name__ == "__main__":
    main()
