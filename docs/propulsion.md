# PROP-1 — the jet engines, computed in-repo [C]

> **Tag [C] = computed in this repo by `lib/engine.py`, an idealized on-design
> turbofan cycle self-tested against published engine data [E]. NOT validated —
> no off-design map, no BLI distortion penalty, no bleed/installation losses.**
> Machine-readable: `schemes/kestrel-x1/analysis/propulsion.json` (CI freshness +
> schema gated; `tests/test_claims.py` stress-tests it).

## What was done

A standard textbook on-design turbofan cycle (intake → fan → compressor → burner
→ turbine → nozzles, constant-cp streams, component efficiencies) implemented from
scratch in `lib/engine.py`:

```
Tt2 = T0(1+0.2M²),  Pt2 = π_d p0 (1+0.2M²)^3.5
Tt13 = Tt2(1+(π_f^0.2857−1)/η_f),  Pt13 = π_f Pt2
Tt3  = Tt2(1+(π_c^0.2857−1)/η_c),  Pt3  = π_c Pt2
f    = cp_c(Tt4−Tt3)/(η_b·LHV − cp_g·Tt4)
(1+f)cp_g(Tt4−Tt5) = cp_c(Tt3−Tt2) + BPR·cp_c(Tt13−Tt2)
F/ṁ_core = (1+f)Ve9 − U + BPR(Ve13 − U),   TSFC = f/(F/ṁ_core)
```

**Self-tests against published engines [E, verified 2026-11-21]** (all pass, bands
are deliberately wide — the point is catching order-of-magnitude errors):

| engine class | published cruise TSFC [E] | computed [C] |
|---|---|---|
| CFM56-7B (737-800) | 0.667 lb/lbf/h | **0.603** |
| LEAP-1A (A320neo) | 0.51 | **0.564** |
| NASA NPSS advanced single-aisle | 0.56 | **0.574** |

## KESTREL-X1 turbo-generator cycle at the M0.58 / 25,000 ft cruise point

BPR 9, OPR 45, FPR 1.55, Tt4 1750 K (a modern geared/ultra-high-bypass-class core
[T]): **TSFC = 0.455 lb/lbf/h [C]**.

- **Stress test of sizing.py:** the `tsfc_1hr = 0.55` assumption baked into the
  Breguet sizing is *conservative* vs this cycle (0.455 computed) — within the ±20%
  check band, so the sizing fuel fraction is not an artifact. Sensitivity: at the
  computed 0.455, fuel fraction 0.1458 → ~0.121 and MTOW −6.6% [C].
- **BPR sweep** (OPR 45, Tt4 1750 K): TSFC 0.52 @ BPR 5.5 → 0.455 @ 9 → ~0.40 @ 14 —
  the published "higher BPR = lower TSFC" trend reproduces [C].
- **Tt4 sweep** (BPR 9): 0.49 @ 1550 K → 0.455 @ 1750 K → ~0.43 @ 1850 K [C].

## Fan loading check (are the 14 DEP fans + aft BLI fan plausible?)

At cruise, 159.9 kW per 0.64 m DEP fan at 120 m/s face velocity [T assumption] →
ṁ ≈ 21 kg/s, specific work ≈ 7.6 kJ/kg → **implied FPR ≈ 1.10** [C]. The 1.8 m aft
BLI fan at 50% of propulsive power → **FPR ≈ 1.08** [C]. Both are low-pressure-ratio,
quiet-fan territory — consistent with the noise target in `docs/passenger-first.md`.

## Caveats (why this is [C], not a result)

On-design only; no off-design/spool matching; no BLI inlet-distortion penalty on the
aft fan (STARC-ABL/D8 work shows some loss — BLI fan numbers are optimistic); no
bleed/accessories; fully expanded ideal nozzles; fan-face velocity is an assumption.
Next rungs: off-design map (NPSS-class), distortion-tolerant fan model, acoustic
model for the noise target.

## Reproduce

```bash
python schemes/kestrel-x1/propulsion.py   # analysis/propulsion.json
python -m pytest tests -q                 # stress-tests incl. PROP-1 self-tests
```
