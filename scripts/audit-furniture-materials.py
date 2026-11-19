"""Check converted furniture transparency against cached official materials."""
import json, pathlib
import UnityPy
from glb import load

ROOT=pathlib.Path(__file__).resolve().parents[1]
env=UnityPy.load(*[str(p) for p in (ROOT/'.assets/selected').glob('*cafe*materials*.bundle')])
originals={o.read().m_Name:o.read() for o in env.objects if o.type.name=='Material'}
checked=[];errors=[];masks=[];waters=[]
for file in (ROOT/'characters').glob('*/character.json'):
    character=json.loads(file.read_text(encoding='utf-8'))
    for furniture in character.get('furniture',[]):
        doc,_=load(file.parent/furniture['model'])
        for mat in doc['materials']:
            original=originals.get(mat['name'])
            if original is None:continue
            floats=dict(original.m_SavedProperties.m_Floats)
            if mat.get('extras',{}).get('BA_waterSurface'):
                property=mat['extras'].get('BA_sourceColorProperty','_SurfaceColor')
                color=dict(original.m_SavedProperties.m_Colors)[property]
                assert mat.get('alphaMode')=='BLEND'
                assert all(abs(a-b)<1e-6 for a,b in zip(mat['pbrMetallicRoughness']['baseColorFactor'],[color.r,color.g,color.b,color.a])),mat['name']
                waters.append({'character':character['id'],'material':mat['name'],'sourceProperty':property,'rgba':mat['pbrMetallicRoughness']['baseColorFactor']})
            if floats.get('_SrcBlend') in (1,5) and floats.get('_DstBlend')==10:
                entry={'character':character['id'],'furniture':furniture['id'],'material':mat['name']}
                checked.append(entry)
                if mat.get('alphaMode')!='BLEND':errors.append(entry)
                color=dict(original.m_SavedProperties.m_Colors).get('_SurfaceColor' if mat.get('extras',{}).get('BA_waterSurface') else '_Color')
                if color and abs(mat.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])[3]-max(0,min(1,color.a)))>1e-6:errors.append(entry)
            if mat.get('extras',{}).get('BA_nonVisual'):
                assert mat['alphaMode']=='BLEND' and mat['pbrMetallicRoughness']['baseColorFactor'][3]==0
                masks.append({'character':character['id'],'furniture':furniture['id'],'material':mat['name']})
assert any(w['character']=='hina_swimsuit' and w['sourceProperty']=='_BaseColor' for w in waters)
report={'officialAlphaBlendMaterialsChecked':checked,'nonVisualMaskMaterials':masks,'waterMaterials':waters,'errors':errors}
(ROOT/'test-results/furniture-alpha-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not errors,errors
assert masks,'Window stencil helper must be invisible'
print('Verified',len(checked),'alpha-blended material instances and',len(masks),'non-color mask')
