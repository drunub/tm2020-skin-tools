ADD_REACTOR = True

TM2 = False 
# enable if using tm2 model source, it will delete the damage meshes for you

import bpy
import math
from bpy_types import Mesh
from mathutils import Euler, Vector, Matrix
from math import radians
import re

lod_pattern = re.compile(r"_Lod(\d+)$")


D = bpy.data

BONE_UNMOVED = (Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)))

MATS = {"s": "SkinDmg_Skin",
        "g": "GlassDmgCrack_Glass",
        "d": "DetailsDmgNormal_Details",
        "w": "DetailsDmgNormal_Wheels"}

FRLR = ["FL", "FR", "RL", "RR"]

def frlr(p):
    return [pos + p for pos in FRLR]

SOCKETS = ["LightFProj", # tmnf/tm2 names that should be sockets
           "LightFL1", 
           "LightFR1", 
           "LightRL", 
           "LightRR", 
           "FLLight",
           "FRLight",
           "RLLight",
           "RRLight",
           "ProjShad",
           "Exhaust1",
           "Exhaust2",]

EXTRA_JOINTS = ["Exhaust", # optional
                "PilHead",
                "PilHead2",
                "PlayerSeat_Pilot01",
                "FLArmDir",
                "FRArmDir",
                "RLArmDir",
                "RRArmDir",
                "Hood",
                "Trunk",
                "LDoor",
                "RDoor",
                "FLCardan",
                "FRCardan",
                "FWShieldGlass",
                "LDoorGlass",
                "RDoorGlass",
                "TrunkGlass",]

CAR_SKEL = ["Body", ["FLHub", ["FLGuard", "FLWheel"], # stuff seems to break if bone indices are different or certain bones are missing
                               "FLReactor",
                               "FLArmBot",
                               "FLArmTop",
                               "FLSusp"],
                    ["FRHub", ["FRGuard", "FRWheel"],
                               "FRReactor",
                               "FRArmBot",
                               "FRArmTop",
                               "FRSusp"],
                    ["RLHub", ["RLGuard", ["RLCardan", "RLWheel"]],
                               "RLReactor",
                               "RLSusp",
                               "RLCardan",
                               "RLArmBot",
                               "RLArmTop"],
                    ["RRHub", ["RRGuard", ["RRCardan", "RRWheel"]],
                               "RRReactor",
                               "RRSusp",
                               "RRCardanB",
                               "RRArmBot",
                               "RRArmTop"]]


def flatten(l):
    for itm in l:
        if isinstance(itm, list):
            yield from flatten(itm)
        else:
            yield itm

ALL_BONES = set(flatten(CAR_SKEL + SOCKETS + EXTRA_JOINTS))

REMOVE = ["WheelMin", "FakeShad"]

def add_bones(arm, bones, parent=None):
    bones = iter(bones)
    new_parent = arm.edit_bones.new(next(bones))
    new_parent.tail = BONE_UNMOVED[1]
    new_parent.parent = parent
    for b in bones:
        if type(b) is list:
            add_bones(arm, b, new_parent)
        else:
            if not ADD_REACTOR and "Reactor" in b: continue
            new_bone = arm.edit_bones.new(b)
            new_bone.parent = new_parent
            new_bone.tail = BONE_UNMOVED[1]


objects = bpy.context.selected_objects

arm = bpy.data.armatures.new("Hips")
arm_obj = bpy.data.objects.new("Hips", arm)
bpy.context.scene.collection.objects.link(arm_obj)

bpy.context.view_layer.objects.active = arm_obj

bpy.ops.object.mode_set(mode='EDIT')
add_bones(arm, CAR_SKEL)

class Part():
    def __init__(self, obj):
        self.obj = obj
        obj_name = obj.name
        
        self.mat_name = None
        self.lod_level = 1
        self.is_damage = False
        self.is_socket = False
        
        # socket/tm2 damage
        if obj_name[0] == "_":
            if TM2:
                self.is_damage = True
            else:
                self.is_socket = True
            obj_name = obj_name[1:]
        
        
        # mat letter
        m = obj_name[0]
        if m.islower():
            self.mat_name = MATS.get(m)
            obj_name = obj_name[1:]

        
        # damage part (it doesnt work yet but maybe in da future)
        if obj_name[-1] == "_":
            self.is_damage = True
            obj_name = obj_name[:-1]
        
        
        # lod
        lod_level = lod_pattern.search(obj_name)
        if lod_level:
            self.lod_level = int(lod_level.group(1))
            obj_name = lod_pattern.sub("", obj_name)
        
        self.part_name = obj_name
        
        self.is_socket = self.part_name in SOCKETS
        self.ignore = self.part_name in REMOVE


parts = map(Part, objects)

for p in sorted(parts, key=lambda d: d.lod_level): # prioritise lod1 for bones
    part = p.obj
    if p.ignore:
        bpy.data.objects.remove(part)
        continue
    
    part_name = p.part_name
    mat_name = p.mat_name
    is_socket = p.is_socket
    is_damage = p.is_damage
    lod_level = p.lod_level
    
    print(part.name, part_name)
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    part_mesh = part.data
    
    #move_bone = False

    if not part_name in arm.edit_bones:
        if not part_name in ALL_BONES: 
            part_name = "Body" # bind unknown parts to Body
            is_socket = False
            is_damage = False
        new_bone = arm.edit_bones.new(["","_"][is_socket] + part_name)
        new_bone.tail = BONE_UNMOVED[1]
    
    bone = arm.edit_bones[["","_"][is_socket] + part_name]
    if (bone.head, bone.tail) == BONE_UNMOVED:
        bone.matrix = part.matrix_world @ Matrix.Rotation(radians(90.0), 4, 'X')
        
        if ADD_REACTOR and part_name[2:] == "Wheel":
            reactor_name = part_name[:2] + "Reactor"
            bone = arm.edit_bones[reactor_name]
            bone.matrix = part.matrix_world @ Matrix.Rotation(radians(90.0), 4, 'X')
    else:
        print("Bone already moved")
    
    
    if part_mesh and not is_socket:
        bpy.ops.object.mode_set(mode='OBJECT')
        if mat_name:
            if lod_level > 3: # nadeoimporter is weird if you use more than 3 lods, it will be corrected in skinfix.py
                mat_name += "_Lod" + str(lod_level)
            if is_damage:
                mat_name += "_"
                
            mat = D.materials.get(mat_name, D.materials.new(name=mat_name))
            part_mesh.materials.clear()
            part_mesh.materials.append(mat)
        
        bpy.ops.object.select_all(action='DESELECT')
        part.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.parent_set(type='ARMATURE_NAME')
        
        if part_name in part.vertex_groups:
            vert_group = part.vertex_groups[part_name]
        else:
            vert_group = part.vertex_groups["Body"]
        
        all_verts = range(len(part_mesh.vertices))
        vert_group.add(all_verts, 1.0, "REPLACE")
    
    if is_socket or is_damage:
        bpy.data.objects.remove(part) # sockets dont have mesh and damage dont work yet
    

        
