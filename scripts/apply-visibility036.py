"""Repair repeated boolean Timeline clips without rebuilding unrelated geometry."""
from pathlib import Path
import json,re,shutil
from glb import load,save
from timeline_visibility import boolean_curves
root=Path('.assets/fx036-stage');profiles=json.loads(Path('.assets/furniture-profiles.json').read_text('utf8'))
rows=json.loads(Path('test-results/visibility036-audit.json').read_text('utf8'));report=[]
for row in rows:
 char=row['character'];cp=Path('characters')/char/'character.json';manifest=json.loads(cp.read_text('utf8'));f=next(f for f in manifest['furniture'] if f['model']==row['model'])
 p=root/char/row['model']
 if not p.parent.exists():shutil.copytree(cp.parent,p.parent)
 d,b=load(p);meta=d['scenes'][0]['extras']['BA_furniture'];icon=f.get('sourceTimeline',meta.get('sourceTimeline'));group=f.get('sourceGroup',meta.get('group'))
 profile=next(r for r in profiles if r['character']==char and r['icon']==icon and r['group']==group)
 files=[q for q in Path('.assets/furniture-exported/all').rglob(profile['root']+'*.glb') if re.fullmatch(re.escape(profile['root'])+r'(?:_\d+)?',q.stem)]
 source,_=load(max(files,key=lambda q:q.stat().st_mtime));curves=boolean_curves(source['scenes'][0]['extras']['BAAD_unity_animation']['clips'],profile['studentTrack'])
 names={n.get('name'):i for i,n in enumerate(d['nodes'])};vis=d['scenes'][0]['extras']['BA_pet_visibility'];tracks=vis['clips'][f['clip']];changed=[]
 for curve in curves:
  name=curve['path'].split('/')[-1]
  if name not in names:continue
  node=names[name];new={'node':node,'keys':[[t,v>=.5]for t,v in curve['keys']]};old=next((t for t in tracks if t['node']==node),None)
  if new!=old:
   tracks[:]=[t for t in tracks if t['node']!=node];tracks.append(new);changed.append({'name':name,'old':old,'new':new})
 if changed:
  save(p,d,b);report.append({'character':char,'model':row['model'],'changes':changed})
Path('test-results/visibility036-applied.json').write_text(json.dumps(report,indent=2),'utf8');print('repaired',len(report),'models')
