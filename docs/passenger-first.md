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
| 1 | **Noise** — takeoff roar, cabin hum, ear popping | Cabin cruise < 70 dB; takeoff well under ICAO Chapter 14 limits | Aft **BLI fan** (shielded by the fuselage) + 14 **low-RPM ducted DEP fans** + hybrid-electric (electric motors are far quieter than turbines) + **morphing TE** instead of slatted noisier high-lift devices | [E, verified 2026-11-21]: ICAO Chapter 14 = Chapter 3 minus 17 EPNdB cumulative (min 1 dB margin per measurement point); DEP/BLI and electric propulsion are published as quieter (STARC-ABL, N3-X); Heart Aerospace X1 — the world's largest electric aircraft — first flew Jul 2026, ES-30 30-seat hybrid targets certification 2031; Eviation Alice flew 2022. No acoustic model in-repo yet (limitation §6 of concept.md) |
| 2 | **Turbulence bumpiness** | Gust load factor at 50 ft/s gust reduced ~75%+ vs rigid wing; target: passenger-perceived bump in top quartile of fleet = "smooth" | **KESTREL-TE morphing trailing edge as an active gust-alleviation surface** — CLAIM-3 | Why it matters [E, verified 2026-11-21]: NTSB 2008-2023 — 136 turbulence accidents, 143 serious injuries, flight attendants involved in 92.6% of them; FAA: ~163 serious injuries 2009-2022, ~80% crew; severe clear-air turbulence +55% over the N. Atlantic and +41% over N. America since 1979 (U. Reading), projected to roughly double by 2050. **[C] computed here:** `analysis/gust-alleviation.json` — a 50 ft/s sharp gust adds Δn ≈ 1.49 (n = 1 → 2.49); the morph law at its demonstrated 3%-chord droop cancels ≈77% of the gust lift increment; full cancel needs ~180 mm droop at root chord. Quasi-steady, actuation rate untested — falsification path is unsteady CFD |
| 3 | **Boarding time** (40 min on single-aisle) | Turnaround boarding < 15 min | **BWB layout** (nova-bwb A/B baseline): multiple doors/aisles vs KESTREL's single aisle | [E, verified 2026-11-21]: boarding/evacuation simulation studies of BWB cabins (multi-aisle, overtaking strategies) report large boarding-time reductions and 90 s evacuation compliance in sims. Honest notes: (a) on KESTREL-X1's single-aisle tube this target is NOT met — it is an argument for the NOVA-BWB variant; (b) a 2016 U. Toronto study finds the BWB *fuel* advantage mainly at large sizes, so at 76 seats the BWB case rests on boarding/cabin, not fuel |
| 4 | **Cabin comfort** — dry air, "wiped out" feeling, cramped | Cabin altitude ≤ 6,000 ft equivalent + higher humidity (composite fuselage allows it); 18.5" seats at 2+2 | Wide double-bubble fuselage (D8 direction); composite structure | [E]: 787's composite hull is published at 6,000 ft cabin vs ~8,000 ft aluminum — verify. KESTREL-X1's double-bubble is the enabling shape; pressurization system not modeled in-repo |
| 5 | **"Electric and cheap"** | Energy cost per mission ≤ jet-fuel cost; emissions ↓ | Hybrid-electric: 2 turbo-generators + battery buffer feeding the fan array | **[C] computed here:** `analysis/energy-cost.json` — with **Nov-2026 verified prices** (EIA: Jet A wholesale spot $4.48/gal ≈ **$0.124/kWh**; U.S. industrial electricity 9.64¢/kWh, Aug 2026), grid-electric energy is **0.78× the cost of jet fuel** per mission — electric is now cheaper per kWh at industrial rates (break-even $0.124/kWh; FBO retail jet is even higher). BUT batteries are ~48× heavier per kWh, so an all-battery 1,500 nm mission is still not viable, and KESTREL-X1 as configured is hybrid (turbo-generators burn Jet A; battery is a buffer). Verdict: "cheap" is now true on energy price at industrial rates, price-dependent, and NOT the whole story — emissions, noise, maintenance remain the case |

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

## Sources (verified via web search 2026-11-21 — see `docs/BUGS.md` PROV-2026-11-21-07)

- ICAO Annex 16 Vol I Chapter 14 noise stringency (Chapter 3 −17 EPNdB cumulative, +1 dB/point min) — icao.int, 14 CFR Part 36
- NTSB turbulence injury analysis 2008-2023 (136 accidents, 143 serious injuries, FAs 92.6%) — Shekhar & Ruskin, Aerospace Medicine and Human Performance, published 2025-11
- FAA ~163 serious turbulence injuries 2009-2022, ~80% cabin crew — via BBC Science Focus, May 2026
- Clear-air turbulence +55% severe over N. Atlantic, +41% over N. America since 1979; ~doubling by 2050 — U. Reading (Williams et al.), GRL 2017 + 2025-2026 updates
- Boeing 787 composite fuselage enables 6,000 ft cabin altitude vs ~8,000 ft aluminum — Boeing/press
- Airbus MAVERIC "up to 20%" — Airbus press release 2020-02-11; U. Toronto 2016 BWB sizing study (advantage mainly large aircraft)
- Heart Aerospace X1 first flight Jul 2026 (FAA-cleared, world's largest electric aircraft); ES-30 30-seat hybrid, certification target 2031, 125 mi electric / 500 mi hybrid — heartaerospace.com, AVweb, 2026
- Eviation Alice first flight 2022 — airdatanews 2026
- EIA Nov 2026: U.S. Gulf Coast kerosene-jet spot $4.48/gal; IATA global jet fuel $169.82/bbl; FBO retail $8.5-9.34/gal (Aviation Week/GlobalAir Nov 2026)
- EIA Aug 2026: U.S. industrial electricity average 9.64 c/kWh (state range ~4-39 c/kWh)
- BWB boarding/evacuation studies — Energies 2018 (MDPI) generic boarding model; Waseda Univ. boarding strategies; airEXODUS evacuation sims
