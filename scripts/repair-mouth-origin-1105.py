"""Retain verified fractional MouthDefaultUV origins, including reset commands."""
import json,pathlib,shutil
from glb import load,save
from mouth_events import mouth_events
root=pathlib.Path('characters');report=[];specs={}
for character,uv in [('kayoko_dress',[.11999999731779099,.5]),('tsumugi',[.3799999952316284,0])]:
 p=root/character/'character.json';c=json.loads(p.read_text('utf8'));s=c['mouth'];s['baseUV']=uv
 backup=pathlib.Path('.assets/pre-029')/character/'character.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copyfile(p,backup)
 d,b=load(p.parent/c['model'])
 for clip in d['scenes'][0]['extras']['BAAD_unity_animation']['clips']:
  if clip['track'] in s['events']:s['events'][clip['track']]=mouth_events(clip,s['defaultTile'])
 for f in c.get('furniture',[]):
  fd,fb=load(p.parent/f['model'])
  clip=next(x for x in fd['scenes'][0]['extras']['BAAD_unity_animation']['clips'] if x['track']==f['clip'])
  f['mouthEvents']=mouth_events(clip,s['defaultTile'])
 specs[s['material']]=(uv,c)
 p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n','utf8');report.append(character)
for p in root.glob('*/*.glb'):
 d,b=load(p);changed=False
 for scene in d['scenes']:
  for s in scene.get('extras',{}).get('BA_furniture_mouths',[]):
   if s['material'] not in specs:continue
   uv,c=specs[s['material']];s['baseUV']=uv;changed=True
   for key,events in s['events'].items():
    normalized=lambda es:[{k:v for k,v in e.items() if k!='reset'} for e in es]
    matches=[f['mouthEvents'] for f in c.get('furniture',[]) if normalized(f['mouthEvents'])==normalized(events)]
    assert matches,(p,key)
    s['events'][key]=matches[0]
 if changed:
  backup=pathlib.Path('.assets/pre-029')/p.relative_to(root);backup.parent.mkdir(parents=True,exist_ok=True)
  if not backup.exists():shutil.copyfile(p,backup)
  save(p,d,b);report.append(str(p))
pathlib.Path('test-results/mouth-origin-repairs.json').write_text(json.dumps(report));print(report)
