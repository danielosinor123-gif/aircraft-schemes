# CLAIM-2 — the KESTREL-TE morphing trailing-edge law, authored here [C]

> **Tag [C] = computed in this repo by `lib/morph.py` (2-D inviscid thin-airfoil
> theory implemented from scratch). NOT validated by CFD or experiment.**
> Machine-readable output: `schemes/kestrel-x1/analysis/morphing-te.json`
> (regenerated + freshness-gated by CI). Demo geometry: `schemes/kestrel-x1/morph-demo.stl`.

## The law (ours, not copied)

FlexSys/NASA publish *that* adaptive compliant trailing edges work; they do not
publish a camber law you can cite as yours. This one is authored in this repo
(first public commit 2026-11-19, `lib/morph.py`):

```
dz(xi) = -A · s² · (3 - 2s),   s = (xi - j)/(1 - j),   xi = x/c,  xi >= j
```

- **j = 0.75**: morphing starts at 75% chord; **A** = droop amplitude (fraction
  of chord). z positive up, so **A > 0 = TE down = droop** (more lift),
  A < 0 = reflex (cruise drag reduction).
- **smoothstep s²(3−2s)**: zero slope at the junction *and* at the tip → C¹
  continuous camber line, **no hinge line, no gap, no actuator step** — that is
  the claimed advantage over a hinged flap.
- Camber-only: thickness distribution unchanged (scheme model).

## Method — thin-airfoil theory implemented from first principles

Glauert series on the θ-grid (ξ = (1−cosθ)/2), trapezoid over the actual
(non-uniform) θ spacing, slopes by central differences:

```
A0 = α − (1/π)∫(dζ/dξ)dθ,   An = (2/π)∫(dζ/dξ)cos(nθ)dθ
Cl = 2π(A0 + A1/2),   Cm_ac = −(π/4)(A1 − A2)   [= Cm_le + Cl/4]
α_L0 = (1/π)∫(dζ/dξ)dθ − A1/2
```

**Self-test (recorded in the JSON):** plain NACA 2412 gives α_L0 = **−2.077°**
vs the published [E] −2.07° — abs err 0.007°, pass. The integrator is validated
against a known airfoil before any morphing number is trusted. (First version
of this code integrated on a uniform-θ grid while sampling uniform-ξ — it
gave −1.53° and a flipped lift sign; caught by the self-test, fixed, logged in
`docs/BUGS.md` as BUG-2026-11-19-05.)

**Flap equivalence:** a hinged flap at the same junction (dζ/dξ −= δ for
ξ ≥ j) is exactly linear in δ in thin-airfoil theory, so one finite difference
gives dCl/dδ exactly; δ_eq = ΔCl_morph / (dCl/dδ).

## Results (NACA 2412-class profile, root chord 4.6 m, j = 0.75, α = 0)

| A (fraction of chord) | A (mm) | ΔCl vs A=0 | α_L0 (deg) | ΔCm_ac | equivalent hinged flap |
|---|---|---|---|---|---|
| 0.005 | 23 | +0.060 | −2.63 | −0.009 | 0.23° |
| 0.010 | 46 | +0.121 | −3.18 | −0.018 | 0.45° |
| 0.020 | 92 | +0.242 | −4.28 | −0.035 | 0.91° |
| 0.030 | 138 | **+0.363** | −5.39 | −0.053 | **1.36°** |

Full table incl. Cl at α = 5°: `analysis/morphing-te.json`.

**Reading:** a 3%-of-chord droop of the KESTREL-TE law buys ΔCl ≈ +0.36 — the
same lift change as a **1.36° hinged flap** at the same 75% junction — but with
a smooth camber line (no hinge gap, no step, no discrete actuator). The
nose-down ΔCm_ac ≈ −0.05 is the pitching moment a control law must trim
(that's also what a flap does).

## What this is and is not

- **Is:** an original, parameterized morphing-TE law + an in-repo aero estimate
  of its lift/moment effect, with the analysis code self-tested against a
  published airfoil property. Dated public record in this repo's commit history.
- **Is not:** validated aerodynamics. Thin-airfoil is 2-D, inviscid, thin. Real
  effects NOT modeled: viscous hinge/gap drag (favors the morphing law),
  3-D spanwise effects on a 35 m truss-braced wing, structural morphing
  actuation loads, control-law trim. Falsification path: CFD of `morph-demo`
  geometry vs the unmorphed wing at several α (next rung of the CFD ladder in
  `docs/cfd-results.md`), then wind tunnel.

## Reproduce

```bash
python schemes/kestrel-x1/morph.py     # writes analysis/morphing-te.json
python schemes/kestrel-x1/model.py     # also exports morph-demo.stl (2% droop)
```

CI reruns `morph.py` and fails (exit 2) if the committed JSON is stale.
