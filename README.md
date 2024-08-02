# tm2020-skin-tools
documentation of findings and collection of tools/scripts i created that allow and ease the creation of 3d trackmania 2020 skins

i will release a tutorial eventually in document and video form

you should also check out [bmx22c's tutorial](https://www.youtube.com/watch?v=yXS1dwcq1Cs), you can incorporate the tools here with it

thanks to bmx22c for the original export technique and helping with stuff and thx to the schadocalex for gbx-py

all these tools are intended to be used with each other. boner.py and fakeshad.py are optional, but i seriously recommend boner.py, it will make ur life a lot easier

it's possible the specific use or behaviour of these will change in the future, but i will keep the readme up to date

the blender scripts were created with blender 4.3 nightly, but the 4.x versions before will work, and probably some of the later 3.x versions

damage models should be possible, but not sure exactly how atm (i think it's the secondary positions "Position1" in the vertex streams)

if you have any questions pls feel free to message me on telegram, twitter, or discord by the same name

## blender/boner.py
completely automates the armature creation for a 3d car skin

**tldr: make a 3d skin the tm2 way, select all parts, run script, and then you should be good for next step**

you can create a tm2020 3d car the old (tmf/tm2) way using meshes/empties, select all the relevant objects, run the script

if you have the source model (like the .3ds/.fbx) for a tmf/tm2 skin, you can simply run this script with it, but you should use ``TM2 = True``, to stop the damage models being turned into sockets because of the similar naming

for example, if you have the mesh wFLWheel_Lod1, it will use LOD 1, be given the material "DetailsDmgNormal_Wheels" (because of the "w" prefix), the FLWheel bone will be moved to the mesh's origin, and the entire mesh will be assigned to its vertex group

the bones are only moved once and will use the origin of the lowest-value LOD mesh

the _Lod suffix is nadeoimporter specific, it is case-sensitive. when not specified, meshes are assigned LOD 1

it's intended to be used with skinfix.py, so the material prefixes are:

s -> SkinDmg_Skin

d -> DetailsDmgNormal_Details

w -> DetailsDmgNormal_Wheels

g -> GlassDmgCrack_Glass

if you don't want the script to touch the materials of a specific mesh (e.g. if you already have multiple materials assigned), simply use a letter not in the list e.g. xBody_Lod1

sockets use underscore prefix, and will create the same name for the bone, so ensure MainBody.MeshParams.xml also has SkelSocketPrefix="_"

in tm2020, the only sockets i'm aware of that work are LightFProj and Exhaust1/Exhaust2, the rest are just listed to ensure the meshes don't sneak through. sockets are basically the equivalent to empties in tmf/tm2

## blender/fakeshad.py
automatically create fakeshad mesh and texture

the fakeshad in 2020 is defined by a bounding box, which can be converted from mesh to bounding box by skinfix.py. fakeshad is optional but baked shadows look cool :0)

run the script after you have finished your skin. you can find the resulting fakeshad texture saved as "fakeshad" in the image editor. the resulting mesh is assigned the material "fakeshad".  skinfix.py needs this mesh to generate the bounding box. ensure MainBody.MeshParams.xml has this in the materials or nadeoimporter will refuse to export:
``<Material Name="fakeshad" Model="SkinDmg" />``

the width and length of the fakeshad bounds can be controlled by ``FS_W`` and ``FS_L``, and i don't recommend changing the height because it will make the shadow faint if too large. the texture size can be changed with ``IMAGE_W/H``, but it must follow the usual TM texture rules regarding size (use 1024x1024, 1024x2048 etc). recommend saving as BC1 DDS texture.

you should set ``BAKE_TYPE`` to ``"AO"`` or ``"SHADOW"``. ambient occlusion bake is noisy but much faster.

blender will freeze during the bake. you should configure the cycles samples and device in the render properties, use GPU if available


## skinfix.py
until nadeo release tools or documentation for skin creation, this is needed for textures and fakeshad to work

requirements:
- python 3.11
- gbx-py (dev branch)
- construct

i will release an executable packaged with python runtime, etc so you dont have to install dependencies

once you've exported your mesh with nadeoimporter, you can use this tool on it with the command (or simply drag the gbx onto the script):

``skinfix.py mainbody.mesh.gbx`` (alternatively .exe if you have the packaged version)

the input file will be overwritten unless specified with the ``-o FILE`` option, e.g. 

``skinfix.py mainbody.mesh.gbx -o out.mesh.gbx``

custom lod distances can be specified with ``-l LOD1 LOD2 LOD3`` e.g:

``skinfix.py mainbody.mesh.gbx -l 10 20 40 80``

i don't recommend changing lod dists, and you shouldn't use more than 5 LODs

honestly just use 3 LODs, it looks fine, and you don't have to worry about armature LODs (certain bones are unused at certain LODs)
