import json
import pathlib
import UnityPy

work = pathlib.Path(__file__).resolve().parents[1] / '.assets'
env = UnityPy.load(*map(str, (work / 'selected').glob('*serika_original*.bundle')))
materials = []
halos = []
for obj in env.objects:
    if obj.type.name == 'Material':
        materials.append(obj.read_typetree())
    if obj.type.name in ['GameObject', 'Transform', 'MeshRenderer', 'MeshFilter', 'ParticleSystem', 'ParticleSystemRenderer']:
        data = obj.read()
        if obj.type.name == 'GameObject':
            name = data.m_Name
        else:
            try:
                name = data.m_GameObject.read().m_Name
            except Exception:
                continue
        if 'halo' in name.lower():
            halos.append({'type': obj.type.name, 'name': name, 'data': obj.read_typetree()})
(work / 'unity-materials.json').write_text(json.dumps(materials, indent=2), encoding='utf-8')
(work / 'unity-halos.json').write_text(json.dumps(halos, indent=2), encoding='utf-8')
for m in materials:
    print(m['m_Name'], json.dumps(m['m_SavedProperties']))
print('Halo component count:', len(halos))
