from gbx_py import GbxStruct, GbxStructWithoutBodyParsed
from gbx_py import parse_file, generate_file
from construct import ListContainer, Container, Array
import sys
import re
import argparse
from math import log2

mat_pattern = re.compile(r"(?:_lod(\d+))?(_?)$")


def fakeshad_bounds(**kwargs):
    return ListContainer([
        Container(
            u01=5,
            u02=0,
            u03=0,
            u04=Container(
                x=0.7071067690849304,
                y=0.0,
                z=0.0,
                w=0.7071067690849304
            ), 
            u05=0.0004372596740722656,
            u06=kwargs.get("y1", -0.011875271797180176),
            u07=kwargs.get("y2", 0.2736610174179077),
            u08=kwargs.get("x1", -1.3362849950790405),
            u09=kwargs.get("z1", -2.1567556858062744),
            u10=kwargs.get("x2", 1.3362849950790405),
            u11=kwargs.get("z2", 2.1567554473876953)
        )
    ])


def get_bbox(verts):
    x = [v.x for v in verts]
    y = [v.y for v in verts]
    z = [v.z for v in verts]
    return Container(
        x1 = min(x),
        x2 = max(x),
        y1 = min(y),
        y2 = max(y),
        z1 = min(z),
        z2 = max(z)
    )



# penis
LOD_DISTS = [[], # used for 1 lod
             [80],
             [40, 80], # lagoon/tm2 lod dists
             [10, 40, 80],
             [4, 10, 40, 80]] # 2020 lod dists - used for 5 lods
             

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('file',
                    metavar="IN_FILE",
                    type=str,
                    help="Input file")

arg_parser.add_argument("-l", "--lod-dists", 
                        dest="lod_dists",
                        metavar="LOD_DIST",
                        nargs="+",
                        type=float,
                        help='List of lod distances')

arg_parser.add_argument("-o", "--out", 
                        dest="out_path",
                        metavar='OUT_FILE',
                        type=str,
                        help='Output file path, write to input file if empty')

args = arg_parser.parse_args()


lod_dists = args.lod_dists or LOD_DISTS

file_path = args.file
file_path_out = args.out_path or file_path

data = parse_file(file_path)


solid2 = data.body[0x90bb000]
fakeshad = data.body[0x90bb002]
skel = solid2.skel.body[0x90ba000]

solid2.materialsNames = []

custom_mats = [m.materialUserInst.body[0x90fd000].materialName for m in solid2.customMaterials]


lods = set()

if not solid2.customMaterials:
    print("Nothing to do - no custom materials")
    quit()


for g in solid2.shadedGeoms:
    mat_idx = g.materialIndex
    
    
    mat = solid2.customMaterials[mat_idx].materialUserInst.body[0x90fd000].materialName
    vis_idx = g.visualIndex
    visual = solid2.visuals[vis_idx]
    vert_count = visual.body[0x0900600F].VertexCount
    
    
    mat_data = mat_pattern.search(mat)
    lod, is_damage = mat_data.group(1), bool(mat_data.group(2))
    mat = mat_pattern.sub("", mat)
    
    if is_damage: # unimplemented
        print(f"Visual {vis_idx:3} - Removed damage mesh")
        solid2.shadedGeoms.remove(g)
        continue
    
    if mat.lower().startswith("fakeshad"):
        print(f"Visual {vis_idx:3} - Fakeshad")
        solid2.shadedGeoms.remove(g)
        bbox = get_bbox(visual.body[0x0900600f].vertexStreams[0].body[0x9056000].Data[0])
        fakeshad.u01 = fakeshad_bounds(**bbox)
        continue
    
    if lod:
        lod = int(lod)
        lod = 2 ** (lod - 1)
        g.lod = lod
    
    
    print(f"Visual {vis_idx:3} - lod {g.lod:3} - {vert_count:6} verts - {mat}")
    
    lods.add(g.lod)
    
    mat= "_" + mat
    
    if mat in solid2.materialsNames:
        g.materialIndex = solid2.materialsNames.index(mat)
    else:
        g.materialIndex = len(solid2.materialsNames)
        solid2.materialsNames.append(mat)


solid2.lodDistances = LOD_DISTS[len(lods)-1] # car will go disappear if mismatched

solid2.listVersion02 = 10
solid2.materials = []
solid2.materialCount = 0
solid2.customMaterials = []
solid2.u14 = -1


new_bytes = generate_file(data)

open(file_path_out, "wb").write(new_bytes)
