# Passenger-first design requirements — what KESTREL-X1 is actually FOR

> Reframed 2026-11-20: the headline is no longer "burns less fuel" but **"the
> regional jet passengers don't hate."** Fuel efficiency stays as the [T]
> constraint that pays for the plane (airlines buy on operating cost); the
> *design targets* below are the passenger complaints we design against.
> Tags: **[T]** target · **[E]** published estimate (verify) · **[C]** computed
> in this repo · **[M]** in-repo CFD (caveated).

## Complaint → measurable target → which feature addresses it

| # | Passenger complaint | Measurable target [T] | Feature that addresses it | Evidence |
|---|---|---|---|---|
| 1 | **Noise** — takeoff roar, cabin hum, ear popping | Cabin cruise < 70 dB; takeoff well under ICAO Chapter 14 limits | Aft **BLI fan** (shielded by the fuselage) + 14 **low-RPM ducted DEP fans** + hybrid-electric (electric motors are far quieter than turbines) + **morphing TE** instead of slatted noisier high-lift devices | Direction [E]: DEP/BLI programs (N3-X, STARC-ABL) and electric propulsion (Eviation Alice, Heart ES-30) are published as quieter — commonly cited, **verify against primary sources**. No acoustic model in-repo yet (limitation §6 of concept.md) |
| 2 | **Turbulence bumpiness** | Gust load factor at 50 ft/s gust reduced ~75%+ vs rigid wing; target: passenger-perceived bump in top quartile of fleet = "smooth" | **KESTREL-TE morphing trailing edge as an active gust-alleviation surface** — CLAIM-3 | **[C] computed here:** `analysis/gust-alleviation.json` — a 50 ft/s sharp gust adds Δn ≈ 1.49 (n = 1 → 2.49); the morph law at its demonstrated 3%-chord droop cancels ≈77% of the gust lift increment; full cancel needs ~180 mm droop at root chord. Quasi-steady, actuation rate untested — falsification path is unsteady CFD |
| 3 | **Boarding time** (40 min on single-aisle) | Turnaround boarding < 15 min | **BWB layout** (nova-bwb A/B baseline): multiple doors/aisles vs KESTREL's single aisle | [E]: BWB studies (MAVERIC, N3-X) cite faster boarding from multi-aisle cabins — commonly cited, verify. Honest note: on KESTREL-X1's single-aisle tube this target is NOT met; it's an argument for the BWB variant |
| 4 | **Cabin comfort** — dry air, "wiped out" feeling, cramped | Cabin altitude ≤ 6,000 ft equivalent + higher humidity (composite fuselage allows it); 18.5" seats at 2+2 | Wide double-bubble fuselage (D8 direction); composite structure | [E]: 787's composite hull is published at 6,000 ft cabin vs ~8,000 ft aluminum — verify. KESTREL-X1's double-bubble is the enabling shape; pressurization system not modeled in-repo |
| 5 | **"Electric and cheap"** | Energy cost per mission ≤ jet-fuel cost; emissions ↓ | Hybrid-electric: 2 turbo-generators + battery buffer feeding the fan array | **[C] computed here:** `analysis/energy-cost.json` — at $0.10/kWh grid power, battery-electric energy costs **~1.4× jet fuel** per mission; electric is cheaper only below **~$0.073/kWh** (off-peak/renewables). Plus batteries are ~48× heavier per kWh than jet fuel. So: **"cheap" is conditional, not a result** — the honest case is emissions + noise + maintenance, with cost parity at cheap electricity |

## What we honestly do NOT claim

- No acoustic model exists in this repo — the noise row is [E] direction + [T] target only.
- Boarding-time and cabin-comfort rows are [E]/[T]; only turbulence (CLAIM-3) and energy cost (ECON-1) are computed in-repo [C].
- "Smoother ride" from CLAIM-3 is aerodynamic authority (lift cancellation), not a measured ride-quality number — ride quality needs structural dynamics + human factors, not in scope.
- Fuel-burn reduction remains the paying constraint: CLAIM-1 (wake filling ≈ 2.1% of cruise power [C]) and the X-66-class truss-wing benefit [E] are what make the ticket affordable.

## Reproduce

```bash
python schemes/kestrel-x1/gust.py     # analysis/gust-alleviation.json — CLAIM-3 [C]
python schemes/kestrel-x1/econ.py     # analysis/energy-cost.json — ECON-1 [C]
```

CI reruns both and fails (exit 2) if the committed JSONs are stale.
