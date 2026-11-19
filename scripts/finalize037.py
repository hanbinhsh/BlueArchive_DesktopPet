"""Named, auditable material/visibility/surface adaptations for the 037 fixes."""
from pathlib import Path
import json
from glb import load,save
root=Path('.assets/fx037-stage')
p=root/'miyako_swimsuit/f210310_0.glb';d,b=load(p)
floor=next(n['name']for n in d['nodes']if n.get('name')=='furniture_0_my_event057_showerbooth')
for n in d['nodes']:
 if n.get('name','').endswith('_Ground_Water_Wave'):
  n['translation'][1]=.018;n.setdefault('extras',{})['BA_groundSurfaceClearance']=0
for m in d['materials']:
 s=m.get('extras',{}).get('BA_cafeParticle',{})
 if any('/'+n in s.get('sourceName','')for n in ['Bubble_Drop','Water_Paritcle_Ground','Water_Paritcle_Head','Hose_Water_Flow']):
  m['extras']['BA_liquidReceiver']={'node':floor,'normal':[0,1,0],'constant':-.0315}
for m in d['materials']:
 s=m.get('extras',{}).get('BA_cafeParticle',{})
 if '/Ground_Water_Wave' in s.get('sourceName',''):
  m['extras'].pop('BA_depthTest',None);m['extras'].pop('BA_desktopGroundOverlay',None)
save(p,d,b)

p=root/'yakumo/f210387_0.glb';d,b=load(p)
vis=d['scenes'][0]['extras']['BA_pet_visibility']
phone=next(i for i,n in enumerate(d['nodes'])if n.get('name')=='CH0228_Prop03_Outline' and 'mesh'in n)
for tracks in vis['clips'].values():tracks[:]=[t for t in tracks if t['node']!=phone]
vis['defaults'][str(phone)]=True
d.setdefault('extras',{})['BA_phoneVisibilityRepair']={'node':phone,'reason':'Preserve the original physical phone while the cafe timeline uses its phone FX; the legacy renderer-index event hid this mesh.'}
save(p,d,b)
print('Finalized phone visibility and shower receiving surface')
