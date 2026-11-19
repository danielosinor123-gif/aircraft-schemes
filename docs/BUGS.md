# BUGS / provenance log

## BUG-2026-11-19-03 — generated blockMeshDict had duplicate/missing faces

`tools/export_mesh.py` emitted a `sides` boundary with faces `(0 3 2 1)` and
`(4 5 6 7)` — those are the z-min and z-max planes (duplicating `bottom`/`top`),
while the actual y-min/y-max faces were missing, so the block would not close.
Found when the first real case needed a hand-written blockMeshDict anyway.
**Fix:** six distinct faces (inlet/outlet/back/front/bottom/top). The runnable
case template now lives in `tools/cfd-template/`.

## BUG-2026-11-19-01 — mirror plane wrong axis: model span 20.5 m instead of 35 m

`Shape.mirror("YZ")` reflects across the YZ plane, which flips **x**, not the span
axis y. The first KESTREL-X1 build therefore had both "wings" on the same side
(measured bbox span 20.5 m vs the 35 m the concept doc claimed).

- **Caught by:** bounding-box check against the documented span (the doc claimed
  35 m; the model said 20.5 m — the mismatch was the alarm).
- **Fix:** `mirror_span()` in `lib/aero.py` uses `mirror("XZ")` (y → −y).
- **Regression gate:** CI asserts both schemes' `*-report.json` bbox span is in
  [34, 36] m on every push.

## PROV-2026-11-19-02 — AI image render unavailable → three-views are model-derived

The three-view render via a paid image API failed (account has no credits). The
`view-*.svg` drawings are instead **orthographic projections exported from the CAD
model itself** — stronger provenance, since they cannot diverge from the model.
