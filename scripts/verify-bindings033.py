"""Regression for complete Timeline bindings and untouched non-FX assets."""
from pathlib import Path
import hashlib,json
from glb import load

source=json.loads(Path('.assets/cafe-fx-bindings033/source.json').read_text('utf8'))
assert not source['errors']
expected={
 'chinatsu_onsen':('f6200_0','My_Hotsprings_01_Massagechair',3),
 'izuna':('f203303_0','my_event06_hotspringswindow',5),
 'mari':('f207314_1','my_event20_prayerchair',1),
}
report={'bindings':[],'changedFiles':[],'resourceFiles':0}
for character,(model,icon,count) in expected.items():
    timeline=next(t for t in source['timelines'] if t['icon']==icon)
    controls=timeline['controls'] if character!='mari' else [c for c in timeline['controls'] if c['exposedReference']=='0']
    assert len(controls)==count
    d,b=load(Path('characters')/character/(model+'.glb'))
    particles=[m['extras']['BA_cafeParticle'] for m in d['materials'] if m.get('extras',{}).get('BA_cafeParticle')]
    for c in controls:
        matches=[p for p in particles if p['control']['prefab']==c['prefab']]
        assert matches,c['prefab']
        assert all(p['control']['start']==c['start'] and p['control']['duration']==c['duration'] for p in matches)
        assert c['bindingResolved'] or c['exposedReference']=='0'
        report['bindings'].append({'prefab':c['prefab'],'parent':c['binding'] if c['bindingResolved'] else 'unparented prefab space','particles':len(matches)})
    for m in d['materials']:
        if m.get('extras',{}).get('BA_surfaceAdaptation')=='original-urp-unlit-alpha':
            assert all(0<=v<=1 for v in m['pbrMetallicRoughness']['baseColorFactor'])
            assert m['alphaMode']=='BLEND' and not m['extras']['BA_depthWrite']

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in Path('characters').rglob('*'):
    if not p.is_file():continue
    report['resourceFiles']+=1
    rel=p.relative_to('characters');previous=Path('release/v0.2.12/win-unpacked/resources/characters')/rel
    if digest(p)!=digest(previous):report['changedFiles'].append(rel.as_posix())
assert sorted(report['changedFiles'])==sorted(c+'/'+v[0]+'.glb' for c,v in expected.items())
Path('test-results/bindings033-verification.json').write_text(json.dumps(report,indent=2),'utf8')
print(json.dumps(report,indent=2))
