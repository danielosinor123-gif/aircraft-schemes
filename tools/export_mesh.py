"""CFD-ready export per scheme: fine binary STL tessellation + OpenFOAM background
blockMeshDict + README. Geometry only — no flow solution is claimed or implied.
Run: python tools/export_mesh.py   (after the scheme model.py runs)
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cadquery as cq

SCHEMES = {"schemes/kestrel-x1": "kestrel-x1", "schemes/nova-bwb": "nova-bwb"}


def write_binary_stl(path, verts, tris):
    with open(path, "wb") as f:
        f.write(b"aircraft-schemes CFD surface mesh".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            p = [verts[i] for i in t]
            ux, uy, uz = p[1].x - p[0].x, p[1].y - p[0].y, p[1].z - p[0].z
            vx, vy, vz = p[2].x - p[0].x, p[2].y - p[0].y, p[2].z - p[0].z
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
            f.write(struct.pack("<3f", nx / ln, ny / ln, nz / ln))
            for q in p:
                f.write(struct.pack("<3f", q.x, q.y, q.z))
            f.write(struct.pack("<H", 0))


def block_mesh_dict(bb, pad=10.0, n=(80, 80, 24)):
    x0, x1 = bb.xmin - pad, bb.xmax + pad
    y0, y1 = bb.ymin - pad, bb.ymax + pad
    z0, z1 = bb.zmin - pad, bb.zmax + pad
    return f"""/* Background blockMesh for the scheme surface — STARTING SCAFFOLD, not a validated case. */
FoamFile {{ version 2.0; format ascii; class dictionary; location "system"; object blockMeshDict; }}
convertToMeters 1;
vertices (
    ({x0:.2f} {y0:.2f} {z0:.2f}) ({x1:.2f} {y0:.2f} {z0:.2f}) ({x1:.2f} {y1:.2f} {z0:.2f}) ({x0:.2f} {y1:.2f} {z0:.2f})
    ({x0:.2f} {y0:.2f} {z1:.2f}) ({x1:.2f} {y0:.2f} {z1:.2f}) ({x1:.2f} {y1:.2f} {z1:.2f}) ({x0:.2f} {y1:.2f} {z1:.2f})
);
blocks (
    hex (0 1 2 3 4 5 6 7) ({n[0]} {n[1]} {n[2]}) simpleGrading (1 1 1)
);
edges ();
boundary (
    inlet  {{ type patch; faces ((0 4 7 3)); }}
    outlet {{ type patch; faces ((1 2 6 5)); }}
    top    {{ type symmetryPlane; faces ((3 7 6 2)); }}
    bottom {{ type symmetryPlane; faces ((0 1 5 4)); }}
    sides  {{ type patch; faces ((0 3 2 1) (4 5 6 7)); }}
);
mergedPatchPairs ();
"""


CFD_README = """# CFD scaffold (geometry only — no results claimed)

1. `blockMesh` with `system/blockMeshDict` (generated from the model bounding box, padded 10 m).
2. Put the surface STL (`<scheme>-cfd.stl`, fine tessellation) in `constant/triSurface/`.
3. `surfaceFeatureExtract`, then `snappyHexMesh` refining around the STL, then `checkMesh`.
4. The boundary types above are placeholders. A real case needs a proper far-field
   (inlet/outlet or far-field), wall boundary on the aircraft, and a turbulence model.
   None of that has been done here — this directory is a starting point, not a result.
"""


def main():
    root = Path(__file__).resolve().parents[1]
    for rel, base in SCHEMES.items():
        sdir = root / rel
        shape = cq.importers.importStep(str(sdir / (base + ".step"))).val()
        verts, tris = shape.tessellate(0.05, 0.3)
        cfd = sdir / "cfd"
        cfd.mkdir(exist_ok=True)
        stl = cfd / (base + "-cfd.stl")
        write_binary_stl(stl, verts, tris)
        (cfd / "blockMeshDict").write_text(block_mesh_dict(shape.BoundingBox()))
        (cfd / "README.md").write_text(CFD_README)
        print(f"{base}: {len(tris)} triangles -> {stl.relative_to(root)}; blockMeshDict written")


if __name__ == "__main__":
    main()
