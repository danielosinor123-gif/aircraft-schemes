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

---

## 2026-11-20 — refined mesh (158,783 cells) + α sweep attempt — polar INVALID, honestly reported

> **Tag [M] for the runs below, but the α sweep is declared NOT a valid drag polar.**
> Machine-readable: `schemes/kestrel-x1/cfd/drag-polar.json`.

### What was done

- Refined mesh: same case, `snappyHexMesh` level **(3 4)** → **158,783 cells**
  (3.1× coarse), 40,068 wall faces, wall area 781.5 m², `checkMesh` OK
  (max skewness 1.0004). ν corrected to **2.805e-5** (ISA 25,000 ft, Sutherland;
  BUG-2026-11-19-04).
- α = 0, 271 iterations, converged (p ~3e-07, U ~1e-06..1e-05):
  **Cd_pressure = 0.23301, Cl_pressure = +0.02735**.
  The coarse-mesh Cl = −0.21 fin/stab asymmetry artifact is **gone** on the refined
  mesh (+0.027 ≈ 0, as expected for a near-symmetric body at α=0). Cd dropped 13%
  with refinement (0.2688 → 0.2330).
- α sweep at −2, +2, +4, +6°, ~250 iterations each, warm-started from the α=0 field.
  Forces recomputed with an α-aware projection integrator
  (`tools/calc_forces.py ... <time> <alpha_deg>` — drag/lift axes rotated into the
  inflow direction). Skin-friction Cd ≈ **0.0195** added analytically
  (Cf = 0.455/(log10 Re_L)^2.58, Re_L = 2.57e8, Swet = 781.5 m²).

### The sweep results — and why they are NOT a drag polar

| α | Cd_pressure | Cl_pressure | Cd total (est.) |
|---|---|---|---|
| −2° | 0.24103 | +0.0369 | 0.2605 |
| 0° | 0.23301 | +0.0274 | 0.2525 |
| +2° | 0.22462 | +0.0184 | 0.2441 |
| +4° | 0.21582 | +0.0102 | 0.2353 |
| +6° | 0.20672 | +0.0028 | 0.2262 |

**Cl should rise ~0.1 per degree; it falls toward zero instead.** Diagnosis:
the wing is under-resolved — surface cells ~0.25–0.5 m against a wing thickness of
0.55 m (root) / 0.18 m (tip), i.e. ~1–2 cells across the airfoil, so the pressure
difference between upper and lower wing surfaces is not captured. Confirmed by the
wall-pressure split at α=6: upper −3872 vs lower −3376 m²/s² ⇒ only Cl ≈ 0.03.
A cold-start α=6 run reproduced the same numbers, so it is not a warm-start artifact.
**The Cd values are fuselage-dominated and plausible; the Cl (and hence any L/D or
polar) is not.** The design-point Cl from sizing is ≈ 0.319 — nowhere near what
this mesh produces — so the **[T] L/D = 20–22 remains UNCONFIRMED**.

### CFD ladder (next rungs, in order)

1. Finer surface mesh on the wing (level 5–6 + boundary layers) — **needs > 5 GB RAM**,
   this WSL box has 5 GB; run on bigger hardware.
2. `rhoSimpleFoam` (compressible) instead of `simpleFoam` at M 0.58.
3. Freestream far-field BCs instead of symmetry-plane box.
4. Re-extract the α sweep → drag polar → design-point L/D.
5. CFD of the CLAIM-2 morphed geometry (`morph-demo.stl`) vs unmorphed at several α
   — the falsification path for the KESTREL-TE law.

