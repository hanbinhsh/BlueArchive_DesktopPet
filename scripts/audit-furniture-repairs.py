"""Gate the furniture geometry, reviewed views and four reported regressions."""
import hashlib,json,math,pathlib,sys
from glb import load
R=pathlib.Path(__file__).resolve().parents[1]
records=json.loads((R/'.assets/furniture-adaptation.json').read_text(encoding='utf8'))
views=json.loads((R/'scripts/furniture-view-yaw.json').read_text())
assert records and all(r['status']=='ready' for r in records)
expected={(r['character'],r['model']) for r in records};actual=set();hashes={}
for file in (R/'characters').glob('*/character.json'):
    c=json.loads(file.read_text(encoding='utf8'))
    for f in c.get('furniture',[]):
        actual.add((c['id'],f['model']))
        assert abs(f['yaw']-math.pi*views[f['id'].split('_')[0][1:]])<1e-10
        hashes[c['id']+'/'+f['model']]=hashlib.sha256((file.parent/f['model']).read_bytes()).hexdigest()
assert actual==expected and len(views)==48
def find(character):return next(r for r in records if r['character']==character)
assert 'my_event076_board' in find('maki_camp')['geometry']['rigidSkins']
assert 'my_event22_stool' in find('toki_bunny')['geometry']['rigidSkins']
assert 'CH0246_Prop_Mesh' in find('mutsuki_dress')['bodyGeometry']['rigidSkins']
pond=find('kisaki_swimsuit');assert len(pond['geometry']['staticMeshes'])==5
doc,_=load(R/'characters/kisaki_swimsuit'/pond['model'])
trunk=next(n for n in doc['nodes'] if n.get('name','').endswith('_my_event093_fancypond_0'))
assert 'mesh' in trunk and abs(trunk['rotation'][0]+math.sqrt(.5))<1e-5
assert all(abs(a-b)<1e-5 for a,b in zip(trunk['scale'],[.538263,.538263,.770826]))
assert any(m.get('extras',{}).get('BA_waterSurface') for m in doc['materials'])
report={'ready':len(records),'reviewedFurnitureViews':len(views),'regressionsPassed':True,'resources':hashes,'sourceBindings':records}
(R/'test-results/furniture-repairs.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
print('Verified geometry repairs and view metadata for',len(records),'interactions')
