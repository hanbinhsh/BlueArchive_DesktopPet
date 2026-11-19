"""Repair visibility bindings only; preserve all original geometry and curves."""
from pathlib import Path
import json,copy,hashlib,shutil
from glb import load,save
from visibility import attach_visibility
from renderer_event_layout import renderer_event_layout
R=Path(__file__).resolve().parents[1];stage=R/'.assets/repair044';stage.mkdir(exist_ok=True);target=stage/'chiaki'
if not target.exists():shutil.copytree(R/'characters/chiaki',target)
source=json.loads((R/'test-results/chiaki044-face-source.json').read_text('utf8'));layout=renderer_event_layout('chiaki',[r['name']for r in source['original']]);report=[]
for p in target.glob('*.glb'):
 d,b=load(p);before=copy.deepcopy(d);e=d['scenes'][0]['extras'];old=copy.deepcopy(e['BA_pet_visibility'])
 attach_visibility(d,layout);corrected=e['BA_pet_visibility'];corrected['defaults']=old['defaults']
 if p.name!='model.glb':
  faces={i for i,n in enumerate(d['nodes'])if n.get('name')in ['CH0238_Face01','CH0238_Face02','CH0238_Halo']}
  for key,tracks in old['clips'].items():
   corrected['clips'][key]=[t for t in tracks if t['node']not in faces]+[t for t in corrected['clips'].get(key,[])if t['node']in faces]
 e['BA_renderer_event_layout']={'7':'CH0238_Face01','8':'CH0238_Face02'}
 assert d['animations']==before['animations']and d['meshes']==before['meshes']and d['materials']==before['materials']and d['nodes']==before['nodes']
 save(p,d,b);report.append(dict(file=p.name,unchangedChannels=sum(len(a['channels'])for a in d['animations']),changedOnlyVisibility=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(R/'test-results/chiaki044-repair.json').write_text(json.dumps(report,indent=2),'utf8');print(report)
