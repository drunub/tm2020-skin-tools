FS_W = 3 # fakeshad bounds width
FS_L = 5 # length
FS_H = 0.1 # height, maybe dont change

IMAGE_W = 2048 # fakeshad generated texture
IMAGE_H = 2048

BAKE_TYPE = "AO"
# BAKE_TYPE = "SHADOW" # alternative


import bpy
from math import radians

FAKESHAD = "fakeshad"

D = bpy.data

fs_mat = D.materials.get(FAKESHAD, D.materials.new(name=FAKESHAD))

for obj in bpy.data.objects:
    if obj.type == "MESH" and FAKESHAD in obj.data.materials:
        bpy.data.objects.remove(obj, do_unlink=True)


bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, -FS_H), rotation=(0, 0, radians(0)), scale=(FS_W, FS_L, FS_H))
fs_obj = bpy.context.object
fs_obj.name = FAKESHAD

if FAKESHAD in D.images:
    D.images.remove(D.images[FAKESHAD], do_unlink=True)

fs_img = bpy.data.images.new(FAKESHAD, width=IMAGE_W, height=IMAGE_H, alpha=False)
fs_img.pixels = [1.0, 1.0, 1.0, 1.0] * IMAGE_W * IMAGE_H

fs_mat.use_nodes = True
fs_mat.node_tree.nodes.clear()

bsdf = fs_mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
output = fs_mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
fs_mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

texture_node = fs_mat.node_tree.nodes.new('ShaderNodeTexImage')
texture_node.image = fs_img
fs_mat.node_tree.links.new(texture_node.outputs['Color'], bsdf.inputs['Base Color'])


fs_obj.data.materials.clear()
fs_obj.data.materials.append(fs_mat)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.reset()

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.scene.render.engine = 'CYCLES'


bpy.ops.object.bake(type=BAKE_TYPE)

fs_obj.location = (0,0,0)

if arm_obj := D.objects.get("Hips"):
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_NAME')

# why no worky
#bpy.context.window.workspace = bpy.data.workspaces.get('Texture Paint', bpy.context.window.workspace)
#for area in bpy.context.screen.areas:
#    print(area.type)
#    if area.type == 'IMAGE_EDITOR':
#        area.spaces.active.image = fs_img
