"""Document the absent legacy Otogi renderer before ignoring its events."""
import json,pathlib,UnityPy
from glb import load
R=pathlib.Path(__file__).resolve().parents[1]
env=UnityPy.load(*[str(p) for p in (R/'.assets/selected').glob('*.bundle') if 'ch0174-' in p.name])
roots=[];components=[]
for o in env.objects:
    if o.type.name=='GameObject' and o.read().m_Name=='CH0174':roots.append(o.read())
    if o.type.name=='MonoBehaviour':
        d=o.read_typetree()
        if 'MouthDefaultUV' in d:components.append(d)
renderers=[]
def walk(go):
    for c in go.m_Component:
        obj=c.component.read();kind=obj.object_reader.type.name
        if kind in ['MeshRenderer','SkinnedMeshRenderer']:renderers.append(go.m_Name)
        if kind=='Transform':
            for child in obj.m_Children:walk(child.read().m_GameObject.read())
assert len(roots)==1
walk(roots[0]);assert len(renderers)<=10
doc,_=load(R/'.assets/exported/otogi/Assets/_MX/AddressableAsset/Character/CH0174/CH0174.glb')
clips=doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']
ignored=[{'clip':c['name'],'index':e['int'],'function':e['function'],'time':e['time']} for c in clips for e in c['events'] if e['int']==10 and e['function']=='AniEvt_DisableChildRenderer']
assert len(ignored)==4
report={'renderers':renderers,'components':components,'ignoredEvents':ignored,'reason':'Original prefab has fewer than eleven renderers; index 10 has no renderer. No substitute target is guessed.'}
(R/'test-results/wave9-otogi-bindings.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
p=R/'scripts/wave9-profiles.json';profiles=json.loads(p.read_text(encoding='utf8'))
choices=[['idle','待机','Cafe_Idle'],['interact','咖啡厅互动','Cafe_Reaction'],['walk','原地走路','Cafe_Walk'],['victory','胜利动作','Victory_Start'],['reload','换弹','Normal_Reload'],['pickup','编队提起','Formation_Pickup']]
profiles['otogi']={'actions':[[i,l,'CH0174_'+s] for i,l,s in choices if any(c['name']=='CH0174_'+s for c in clips)],'ignoredRendererEvents':ignored}
p.write_text(json.dumps(profiles,ensure_ascii=False,indent=2),encoding='utf8')
print('Original renderers:',renderers,'; documented missing index 10:',len(ignored),'events')
