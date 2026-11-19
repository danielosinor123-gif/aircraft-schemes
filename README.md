# aircraft-schemes

Conceptual aircraft design schemes — portfolio artifacts, built evidence-first.

> **Nothing here is validated.** No wind tunnel, structural, stability, or
> certification work has been done. Number tags everywhere: **[T]** design target ·
> **[E]** published estimate from a cited program (verify against primary sources) ·
> **[C]** computed in this repo by order-of-magnitude methods (`lib/sizing.py`) ·
> **[M]** computed in this repo by OpenFOAM CFD — coarse mesh, incompressible at
> M 0.58, not validated (see `docs/cfd-results.md`).

## Schemes

| Scheme | Configuration | Doc |
|---|---|---|
| `schemes/kestrel-x1` | Truss-braced high-AR wing (35 m span) + 14 trailing-edge wake-filling DEP fans + 1 aft BLI fan + morphing TE, hybrid-electric | `schemes/kestrel-x1/concept.md` |
| `schemes/nova-bwb` | Blended wing body + 3 aft BLI fans + winglets, hybrid-electric (A/B baseline) | `schemes/nova-bwb/concept.md` |

A/B comparison (generated): `docs/comparison.md` via `python compare.py`.
First real CFD runs (OpenFOAM v1912, coarse mesh, [M] tagged with caveats):
`docs/cfd-results.md` + `schemes/*/cfd/results.json`, reproducible via
`tools/cfd-template/` and `tools/calc_forces.py`.

## Verify this repo yourself (fresh clone)

```bash
git clone https://github.com/danielosinor123-gif/aircraft-schemes && cd aircraft-schemes
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
python schemes/kestrel-x1/model.py        # STEP + STL + SVG three-views + report json
python schemes/nova-bwb/model.py
python schemes/kestrel-x1/sizing.py       # sizing.json [C] estimates
python schemes/nova-bwb/sizing.py
python compare.py                         # docs/comparison.md
python tools/export_mesh.py               # cfd/ STL tessellation + OpenFOAM blockMeshDict scaffold
```

CI runs the same sequence on every push to `main`, including a geometry gate:
both models' reported span must be 34–36 m (`*-report.json`).

## Layout

```
lib/aero.py        shared CadQuery helpers (NACA profiles, lofts, mirror, exports)
lib/sizing.py      Breguet + fixed-We conceptual sizing -> sizing.json
schemes/<name>/    model.py, sizing.py, concept.md, generated artifacts, cfd/
tools/export_mesh.py  fine STL + blockMeshDict scaffold per scheme
compare.py         A/B table generator -> docs/comparison.md
docs/BUGS.md       bug & provenance log
```

## Honesty contract

- Scheme models are **proportions, not aerodynamic surfaces**; the "airfoil" is a
  NACA 2412 polyline for shape only.
- `[E]` figures are commonly cited published estimates; web search was unavailable
  at writing time — **verify against primary sources (NASA/MIT/Airbus) before citing**.
- `cfd/` is a scaffold (geometry + background mesh), not a solved case.
- Bugs and provenance incidents are logged in `docs/BUGS.md`.
