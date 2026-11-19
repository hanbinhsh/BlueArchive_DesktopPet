"""Clip cafe particle effects below the metal stage's authored ground plane.

The transparent desktop has no surrounding cafe floor to occlude the beams.
Stage vertices use local Z for height, with the lowest surface at Z~=0.
"""
import pathlib,sys
from glb import load,save
root=pathlib.Path(sys.argv[1]);path=root/'tsumugi/f211318_0.glb'
doc,binary=load(path);count=0
for material in doc['materials']:
    extra=material.get('extras',{});particle=extra.get('BA_cafeParticle',{})
    if particle:
        extra['BA_liquidReceiver']={'node':'furniture_5_bone_stage_main','normal':[0,0,1],'constant':0}
        count+=1
assert count>0
save(path,doc,binary)
print('Clipped stage particle materials:',count)
