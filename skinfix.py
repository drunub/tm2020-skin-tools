from gbx_py_dev.src.gbx_structs import GbxStruct, GbxStructWithoutBodyParsed, NodeRef
from gbx_py_dev.src.parser import parse_file, generate_file
from construct import ListContainer, Container, Array
from collections import OrderedDict
import sys
import re
import argparse

pattern_mat = re.compile(r'^(?P<mat>.+?)(?:_lod(?P<lod>\d+))?(?P<damage>_)?$', re.IGNORECASE)
pattern_light = re.compile(r'^light\d+', re.IGNORECASE)


def light_user_model(name):
    light = Container(
            version=1,
            Spot=False,
            Color=Container(x=1.0, y=1.0, z=1.0),
            Intensity=10.0,
            Distance=10.0,
            PointEmissionRadius=0.0, #?
            PointEmissionLength=0.0, #
            SpotInnerAngle=0,
            SpotOuterAngle=45.0,
            SpotEmissionSizeX=0.0, #
            SpotEmissionSizeY=0.0, #
            NightOnly=False,
    )
    
    parts = re.findall(r"_([a-z]+)(\d+\.?\d*)?", name.lower())
    
    for k, v in parts:
        if k == "r":
            light.Color.x = float(v)
        elif k == "g":
            light.Color.y = float(v)
        elif k == "b":
            light.Color.z = float(v)
        elif k == "i":
            light.Intensity = float(v)
        elif k == "d":
            light.Distance = float(v)
        elif k == "ao" or k == "a":
            light.Spot = True
            light.SpotOuterAngle = float(v)
        elif k == "ai":
            light.SpotInnerAngle = float(v)
        elif k == "n":
            light.NightOnly = True
    
    #print(light)
    #input()
    
    if not light.SpotInnerAngle:
        light.SpotInnerAngle = light.SpotOuterAngle * 0.7
    
    body = OrderedDict(
        [
            (
                0x090F9000,
                light,
            ),
            (0xFACADE01, None),  # end-of-node marker
        ]
    )
    
    print("Light -", name)
    return NodeRef(0x090F9000, body)



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
LOD_DISTS = [4, 10, 40, 80]
             

def fix_skin(file_in=None, file_out=None, lod_dists=None):
    file_out = file_out or file_in

    data = parse_file(file_in)
    
    solid2 = data.body[0x90bb000]
    fakeshad = data.body[0x90bb002]
    skel = solid2.skel.body[0x90ba000]

    solid2.materialsNames = []

    custom_mats = [m.materialUserInst.body[0x90fd000].materialName for m in solid2.customMaterials]
    
    lods = set()

    if not solid2.customMaterials:
        print("Nothing to do - no custom materials")
        return


    for g in solid2.shadedGeoms:
        mat_idx = g.materialIndex
        
        mat = solid2.customMaterials[mat_idx].materialUserInst.body[0x90fd000].materialName
        vis_idx = g.visualIndex
        visual = solid2.visuals[vis_idx]
        vert_count = visual.body[0x0900600F].VertexCount
        
        m = pattern_mat.match(mat)
        mat, lod, is_damage = m.group('mat'), m.group('lod'), m.group('damage')
        
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
    
    
    for sock_idx, sock in enumerate(skel.sockets):
        if pattern_light.match(sock.name):
            light_model = light_user_model(sock.name)
            if light_model in solid2.lightUserModels:
                model_index = solid2.lightUserModels.index(light_model)
            else:
                solid2.lightUserModels.append(light_model)
                model_index = len(solid2.lightUserModels) - 1
            solid2.lightInsts.append(
                Container(modelIndex=model_index, socketIndex=sock_idx)
            )
    
    solid2.lodDistances = lod_dists[4-min(4, len(lods)-1):]

    solid2.listVersion02 = 10
    solid2.materials = []
    solid2.materialCount = 0
    solid2.customMaterials = []
    solid2.u14 = -1
    
    new_bytes = generate_file(data, reindex_nodes=True)
    
    open(file_out, "wb").write(new_bytes)


def parse_args():
    arg_parser = argparse.ArgumentParser()
    
    arg_parser.add_argument('file_in',
                        metavar="IN_FILE",
                        type=str,
                        help="Input file")
    
    arg_parser.add_argument("-l", "--lod-dists", 
                            dest="lod_dists",
                            metavar="LOD_DIST",
                            nargs="+",
                            default=LOD_DISTS,
                            type=float,
                            help='List of lod distances')
    
    arg_parser.add_argument("-o", "--out", 
                            dest="file_out",
                            metavar='OUT_FILE',
                            type=str,
                            help='Output file path, write to input file if empty')
    
    return arg_parser.parse_args()



if __name__ == "__main__":
    args = vars(parse_args())
    
    sys.exit(fix_skin(**args))
