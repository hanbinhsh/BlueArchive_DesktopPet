"""Inspect original renderer geometry and exported omissions for cafe props."""
import pathlib,sys,json
R=pathlib.Path(__file__).resolve().parents[1]
code=(R/'scripts/prepare-furniture.py').read_text(encoding='utf-8').split('results=[];bychar={}')[0]
exec(compile(code,str(R/'scripts/prepare-furniture.py'),'exec'))
for pack in sys.argv[1:]:
    for p in profiles:
        if p['character']!=pack:continue
        doc,data=exported(p['icon']);names={n.get('name'):n for n in doc['nodes']}
        print('PROFILE',pack,p['icon'],flush=True)
        for name,renderer,active in renderers(prefab(p['icon'])):
            mesh=getattr(renderer,'m_Mesh',None)
            if mesh is None:
                go=renderer.m_GameObject.read()
                filt=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshFilter'),None)
                mesh=filt.m_Mesh if filt else None
            n=names.get(name) or names.get(name+'_0')
            print(name,'active',active,'type',renderer.object_reader.type.name,'mesh',mesh.read().m_Name if mesh and mesh.m_PathID else None,'export',n and ('mesh' in n),'material',[m.read().m_Name for m in renderer.m_Materials],flush=True)
            if n and 'mesh' not in n:print('NODE',n,flush=True)
            if renderer.object_reader.type.name=='MeshRenderer':
                t=next(c.component.read() for c in renderer.m_GameObject.read().m_Component if c.component.deref().type.name=='Transform')
                print('SOURCE TRANSFORM',t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale,flush=True)
            if renderer.object_reader.type.name=='SkinnedMeshRenderer':
                from UnityPy.helpers.MeshHelper import MeshHandler
                mh=MeshHandler(mesh.read());mh.process()
                print('SKIN',name,'indices',mh.m_BoneIndices[:3] if mh.m_BoneIndices else None,'weights',mh.m_BoneWeights[:3] if mh.m_BoneWeights else None,flush=True)
