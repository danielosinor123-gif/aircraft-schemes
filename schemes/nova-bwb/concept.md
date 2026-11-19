# NOVA-BWB — Conceptual Aircraft Design Scheme (A/B partner to KESTREL-X1)

> **STATUS: CONCEPTUAL — NOT VALIDATED.** Same tag legend as kestrel-x1:
> [T] target · [E] published estimate (verify) · [C] computed in-repo.

## The scheme

A **76-seat blended wing body (BWB)** regional aircraft: wide lifting center body,
moderate-AR blended wings (AR ≈ 13), **three large aft boundary-layer-ingesting
(BLI) fans** embedded across the rear fuselage (NASA N3-X direction), winglets,
morphing trailing edge, hybrid-electric turbo-generators + battery buffer.

**Purpose in this repo:** the A/B comparison baseline against
`schemes/kestrel-x1` (truss-braced + distributed trailing-edge fans). The
comparison table is generated, not hand-written: `python compare.py` →
`docs/comparison.md`, from each scheme's `sizing.json` and `*-report.json`.

## Research map [E]

| Element | Inspiration | Commonly cited claim |
|---|---|---|
| BWB planform | Airbus **MAVERIC**; NASA N3-X | ~20% fuel burn (Airbus); N3-X targeted large DEP/BLI savings |
| Aft BLI fans | NASA **STARC-ABL** / N3-X | single-digit to ~10% fuel burn from BLI |
| Morphing TE | FlexSys / NASA ACTE | noise / parts-count reduction |

## Limitations

Same ladder as kestrel-x1 (see `schemes/kestrel-x1/concept.md` §6): no CFD, no
structures, no stability analysis, no certification path. BWB pressurization and
evacuation are known hard problems. All sizing numbers are [C] estimates from
`sizing.py` — not results.

## Reproduce

```bash
python schemes/nova-bwb/model.py     # STEP/STL/SVG + nova-bwb-report.json
python schemes/nova-bwb/sizing.py    # sizing.json
python compare.py                    # docs/comparison.md
```
