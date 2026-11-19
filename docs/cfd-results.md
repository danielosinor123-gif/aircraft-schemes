# CFD results — first real solver runs (coarse, honest)

> **Tag [M] = measured/computed in this repo by OpenFOAM — but on a coarse mesh
> with an incompressible solver at Mach 0.58. These are real solver outputs with
> logged residuals, NOT validated engineering numbers.** Do not quote them as
> performance claims.

## Setup (reproducible from `tools/cfd-template/` + `tools/calc_forces.py`)

- OpenFOAM **v1912** (Ubuntu noble distro package), `simpleFoam` (steady,
  incompressible), `kOmegaSST` RAS, serial run.
- Mesh: `blockMesh` background box (padded 10 m) + `snappyHexMesh` castellated
  only (no boundary layers) around the scheme STL; wall patch `aircraft`.
  - kestrel-x1: **50,873 cells**, 11,389 wall faces
  - nova-bwb: **54,429 cells**, 13,956 wall faces
- Flow: ISA 25,000 ft, rho = 0.549 kg/m³, nu = 3.27e-5 m²/s
  - kestrel-x1: U = 179.6 m/s (M 0.58), Aref = 75 m², 300 iterations
  - nova-bwb: U = 185.8 m/s (M 0.60), Aref = 95 m², 206 iterations (stopped by
    `residualControl`: p 1.7e-06, U ~1e-06..1e-05)
- Forces: pressure forces integrated directly from the solved `p` field over the
  wall patch (`tools/calc_forces.py`, polyMesh geometry). The distro build's
  `forceCoeffs` function object fails on file write ("sha1" IOstream error), so
  forces are computed by direct integration instead — auditable Python, no black box.
  Skin friction is an **analytic estimate** (turbulent flat plate,
  Cf = 0.455/(log10 Re)^2.58, wetted area from the mesh), not from the solver.

## Results at α = 0

| metric | kestrel-x1 | nova-bwb |
|---|---|---|
| Cd (pressure, [M]) | **0.2688** | **0.2694** |
| Cl (pressure, [M]) | −0.214 | +0.024 |
| Cd skin friction (estimate, [C]) | 0.0197 | 0.0194 |
| Cd total (estimate) | ≈ 0.288 | ≈ 0.289 |
| Re_L | 2.2e8 | 2.3e8 |

Full data: `schemes/*/cfd/results.json`.

## What this does and does not show

- **Does show:** both scheme models can be meshed and solved end-to-end in-repo;
  the pipeline (STL → mesh → solve → force integration) is reproducible and CI-able;
  residuals converge (p ~1e-06..1e-07).
- **Does NOT show:** the [T] L/D ≈ 20–22 sizing targets are **not confirmed** —
  at α=0 these bluff scheme models (exposed fan nacelles, strut, fin, no internal
  flow, no boundary-layer mesh) sit at Cd ≈ 0.27. A real design-point L/D needs an
  α sweep at design Cl plus a much finer near-wall mesh.
- **Known anomalies, reported not hidden:** kestrel-x1 shows Cl = −0.21 at α=0,
  which should be ≈ 0; the cause is the z-asymmetric fin/stab in the scheme model
  plus coarse-mesh asymmetry. nova-bwb (z-symmetric) gives Cl = +0.024 — the
  expected near-zero, which validates the force-integration sign conventions.
- **Solver limitation:** incompressible `simpleFoam` at M 0.58–0.60 ignores
  compressibility (M² ≈ 0.34 — not negligible). Next step: `rhoSimpleFoam`.

## Next steps (in order)

1. `rhoSimpleFoam` (compressible) at the same conditions.
2. Mesh refinement study (cells 50k → 200k → 800k) — Cd convergence.
3. α sweep (−2°..+6°) → drag polar, then design-point L/D.
4. Boundary layers (`addLayers`) for skin friction from the solver instead of the
   analytic estimate.
