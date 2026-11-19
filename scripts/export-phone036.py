"""Export Yakumo's character-owned phone effects, absent from ControlTracks."""
import os,sys,runpy,json
from pathlib import Path
from glb import load
from phone_timeline import phone_controls
os.environ['BA_FX_OUTPUT']='.assets/cafe-phone036'
sys.argv=['export-cafe-effects.py','my_event086_salesdesk']
v=runpy.run_path('scripts/export-cafe-effects.py');env=v['env']
for p in Path('.assets/selected').glob('*ch0228*prefabs*.bundle'):env.load_file(str(p))
timeline=v['timelines'][0]
for name in ['FX_my_event086_salesdesk_CH0228_Phone_01','FX_my_event086_salesdesk_CH0228_Phone_02','FX_my_event086_salesdesk_CH0228_Phone_03']:
 matches=[o.read() for o in list(env.objects) if o.type.name=='GameObject' and o.read().m_Name==name]
 assert matches,name
 # Prefer the actual character prefab over stripped dependency copies.
 go=max(matches,key=lambda go:len(go.m_Component));key=name+'__existing'
 v['effects'][key]=v['visit'](go)
profiles=json.loads(Path('.assets/furniture-profiles.json').read_text('utf8'))
profile=next(p for p in profiles if p['character']=='yakumo' and p['icon']=='my_event086_salesdesk')
body,_=load(max(Path('.assets/furniture-exported/all').rglob('CH0228.glb'),key=lambda p:p.stat().st_mtime))
timeline['controls'].extend(phone_controls(body['scenes'][0]['extras']['BAAD_unity_animation']['clips'],profile['studentTrack'],profile['group'],[key.removesuffix('__existing') for key in v['effects'] if 'Phone_' in key]))
Path('.assets/cafe-phone036/source.json').write_text(json.dumps({'timelines':v['timelines'],'effects':v['effects'],'errors':v['errors']}),'utf8')
print('phone roots',len(matches),'effects',len(v['effects']))
