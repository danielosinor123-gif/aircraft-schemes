# CFD scaffold (geometry only — no results claimed)

1. `blockMesh` with `system/blockMeshDict` (generated from the model bounding box, padded 10 m).
2. Put the surface STL (`<scheme>-cfd.stl`, fine tessellation) in `constant/triSurface/`.
3. `surfaceFeatureExtract`, then `snappyHexMesh` refining around the STL, then `checkMesh`.
4. The boundary types above are placeholders. A real case needs a proper far-field
   (inlet/outlet or far-field), wall boundary on the aircraft, and a turbulence model.

NOTE: coarse solver runs HAVE since been done on these surfaces — see
`docs/cfd-results.md` and `results.json` in this directory ([M] tag, caveated).
