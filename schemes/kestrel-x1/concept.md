# KESTREL-X1 — Conceptual Aircraft Design Scheme

> **STATUS: CONCEPTUAL — NOT VALIDATED.** No CFD, wind-tunnel, structural, stability,
> acoustic, or certification analysis has been performed on this scheme. It is a
> learning/portfolio artifact: a novel *combination* of published research concepts.
> Tag legend: **[T]** = design target (a wish, not a result) · **[E]** = published
> estimate from a cited research program (verify against primary source before
> citing elsewhere) · **[C]** = computed in this repo from order-of-magnitude
> conceptual methods (`lib/sizing.py`, output in `sizing.json`).

## 1. The scheme in one paragraph

KESTREL-X1 is a **76-seat regional hybrid-electric aircraft** built around a
**truss-braced, high-aspect-ratio wing** (AR ≈ 16, span 35 m) that carries a
**distributed array of 7 ducted fans per wing trailing edge**, deliberately placed
toward the wing–fuselage junction so the fan wakes **fill the fuselage wake
("wake filling")**. A **wide double-bubble fuselage** feeds a single **aft-fuselage
boundary-layer-ingesting (BLI) fan**. Control is by a **morphing (flexible)
trailing edge** instead of hinged flaps/ailerons. Power: **two rear-mounted
turbo-generators plus a battery buffer**, feeding the electric fan array.

**Novelty statement (honest):** every individual element exists in published
research (see §4). What is novel here is the *integration scheme*: truss-enabled
span + wake-filling DEP array at the wing–body junction + aft BLI fan + morphing
trailing edge on one airframe, with fan placement chosen from wake physics rather
than packaging convenience.

## 2. Configuration (three-view)

See `view-top.svg`, `view-side.svg`, `view-front.svg` — **orthographic projections
generated from the CAD model itself** (`model.py`), not hand-drawn renders — plus
`kestrel-x1.step` / `kestrel-x1.stl` (parametric scheme model). Open the SVGs in any
browser; open the STEP in FreeCAD/Onshape/etc.

- **Top view:** straight high-AR wing, diagonal truss strut from lower fuselage
  to mid-wing, 7 ducted fans per side on the trailing edge, wide fuselage.
- **Side view:** conventional nose, double-bubble cross-section, raised aft
  fuselage with the BLI fan position at the tail, T-tail, strut visible.
- **Front view:** slight dihedral, strut, fan discs along the span.

Model check (last run, `kestrel-x1-report.json`): bounding box
**40.1 m × 35.1 m × 5.9 m** (length × span × height), 21 solids. The 35 m span
claim is asserted against the model in CI, not just written here.

## 3. Key parameters

| Parameter | Value | Tag |
|---|---|---|
| Seats | 76 (2+2, single aisle) | [T] |
| Design range | 1,500 nm | [T] |
| Cruise | Mach 0.58 @ 25,000 ft | [T] |
| Span (truss-braced) | 35 m | [T], verified vs model |
| Wing area | 75 m² | [T] |
| Aspect ratio | 35² / 75 ≈ 16.3 | [C] (in `sizing.json`) |
| MTOW | see `sizing.json` | [C] |
| Wing loading @ MTOW | see `sizing.json` | [C] |
| Wing airfoil | NACA 2412-class (12% t/c), scheme shape only | [T] |
| DEP fans | 14 × trailing-edge ducted fans (cruise power per fan in `sizing.json`) | [T]/[C] |
| Aft BLI fan | 1 | [T] |
| Turbo-generators | 2 × 2 MW, rear-mounted | [T] |
| Battery buffer | ~800 kWh (takeoff/climb boost) | [T] |
| Max L/D target | 20–22 used for sizing | [T] |
| T/W at takeoff | 0.28 | [T] |

## 4. Research map — what each element is and where it comes from

| Element | Published inspiration | Commonly cited claim [E] |
|---|---|---|
| Truss-braced high-AR wing | NASA/Boeing **X-66 Sustainable Flight Demonstrator** (TTB concept) | NASA targets up to ~30% fuel-burn reduction vs current single-aisle |
| Wide double-bubble fuselage | **MIT/Aurora D8** concept | D8 studies reported on the order of 40–50% fuel burn vs 737-class |
| Distributed electric propulsion, wake filling | **NASA N3-X**, LEAPTech | DEP + wake filling targeted at large drag savings |
| Aft-fuselage BLI fan | **NASA STARC-ABL** | BLI reported at roughly single-digit to ~10% fuel burn |
| Blended-wing direction | **Airbus MAVERIC** | Airbus cites ~20% fuel burn for BWB |
| Morphing trailing edge | FlexSys / NASA **adaptive compliant trailing edge** | noise and parts-count reduction vs hinged surfaces |

> Note: web search was unavailable when this doc was written; the figures above are
> the commonly cited published estimates for these programs. **Verify against the
> primary sources before using them in any application.**

## 5. Claim discipline — what this document does and does not claim

- DOES claim: a coherent, novel *combination* of published concepts, with a
  parametric CAD model and in-repo conceptual sizing (`sizing.json`).
- DOES NOT claim: any measured or simulated performance. No number marked
  [T]/[E] is a result. Nothing here may be quoted as "KESTREL-X1 achieves X%".

## 6. Limitations and required next steps before any real claim

1. **Aerodynamics:** CFD (OpenFOAM/SU2 — scaffold in `cfd/`) of the full
   configuration, especially fan–wing–fuselage wake interaction and BLI inlet
   distortion.
2. **Stability & control:** morphing-TE-only control needs a full control-law
   study; flutter of the truss joint is a known hard problem.
3. **Structures:** truss wing carry-through, battery crash/thermal runaway,
   lightning strike on composite morphing skins.
4. **Propulsion integration:** turbo-generator + battery + motor thermal
   management; acoustic model of 14 ducted fans + BLI fan.
5. **Certification path:** CS-25/FAR-25 has no rulebook for DEP/BLI/morphing
   control yet — the real bottleneck for the class, not the physics.
6. **Validation ladder:** CFD → wind tunnel (scale model) → iron bird → flight
   demonstrator. Only after that do [T] numbers become results.

## 7. Reproduce from this repo

```bash
pip install -r requirements.txt          # or: uv pip install -r requirements.txt
python schemes/kestrel-x1/model.py       # STEP/STL/SVG views + kestrel-x1-report.json
python schemes/kestrel-x1/sizing.py      # sizing.json
python tools/export_mesh.py              # cfd/ STL tessellation + blockMeshDict scaffold
python compare.py                        # docs/comparison.md (A/B vs nova-bwb)
```

Coordinates: x = longitudinal (nose −x), y = span, z = up, meters. **Scheme
model only** — the "airfoil" is a NACA 2412 polyline for shape, not flow analysis.

## 8. Sources (verify before citing)

- NASA Sustainable Flight Demonstrator / X-66 transonic truss-braced wing — nasa.gov
- MIT Aurora D8 double-bubble — mit.edu / aurora.aero
- NASA N3-X (DEP/BLI hybrid wing body) — nasa.gov / ntrs.nasa.gov
- NASA STARC-ABL (single-aisle turboelectric with aft BLI) — nasa.gov
- Airbus MAVERIC blended wing body — airbus.com
- FlexSys / NASA adaptive compliant trailing edge — flexsys.com, nasa.gov
