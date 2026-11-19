import pathlib,sys
R=pathlib.Path(__file__).resolve().parents[1]
exec(compile((R/'scripts/prepare-furniture.py').read_text(encoding='utf8').split('results=[];bychar={}')[0],str(R/'scripts/prepare-furniture.py'),'exec'))
from UnityPy.helpers.MeshHelper import MeshHandler
for p in profiles:
    print('BODY',p['character'],p['root'],flush=True)
    for name,renderer,active in renderers(prefab(p['root'])):
        if 'Prop' not in name:continue
        m=MeshHandler(renderer.m_Mesh.read());m.process()
        print(name,'bones',[(b.read().m_GameObject.read().m_Name) for b in renderer.m_Bones],flush=True)
        print('weights',set(m.m_BoneWeights or []),'indices',set(m.m_BoneIndices or []),flush=True)
