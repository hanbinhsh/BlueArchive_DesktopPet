"""Restore original static geometry and exact rigid bone assignments."""
from UnityPy.helpers.MeshHelper import MeshHandler
from glb import append_accessor,read_accessor
from rigid_geometry import rebuild_rigid_mesh
import re

def original_name(name, originals):
    return name if name in originals else re.sub(r'_\d+$','',name)

def restore_geometry(doc,data,originals,defaults,restore_static=True):
    restored=[];repaired=[];inactive=[];empty=[]
    for name,renderer in originals.items():
        if not restore_static:continue
        if renderer.object_reader.type.name!='MeshRenderer':continue
        if not defaults[name]:inactive.append(name);continue
        transform=next(c.component.read() for c in renderer.m_GameObject.read().m_Component if c.component.deref().type.name=='Transform')
        p,q,s=transform.m_LocalPosition,transform.m_LocalRotation,transform.m_LocalScale
        expected={'translation':[-p.x,p.y,p.z],'rotation':[q.x,-q.y,-q.z,q.w],'scale':[s.x,s.y,s.z]}
        candidates=[n for n in doc['nodes'] if original_name(n.get('name',''),originals)==name and 'skin' not in n]
        def difference(n):
            distance=0
            for key,values in expected.items():
                actual=n.get(key,{'translation':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}[key])
                squared=sum((a-b)**2 for a,b in zip(actual,values))
                # A quaternion and its negation represent the same orientation.
                if key=='rotation':squared=min(squared,sum((a+b)**2 for a,b in zip(actual,values)))
                distance+=squared
            return distance
        candidates.sort(key=difference)
        if not candidates or difference(candidates[0])>1e-8:raise ValueError('Missing matching original furniture transform '+name)
        node=candidates[0]
        if 'mesh' in node:continue
        go=renderer.m_GameObject.read()
        filt=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshFilter'),None)
        if not filt or not filt.m_Mesh.m_PathID:continue
        source=MeshHandler(filt.m_Mesh.read());source.process()
        positions=[(-v[0],v[1],v[2]) for v in source.m_Vertices]
        attrs={'POSITION':append_accessor(doc,data,positions,'VEC3')}
        doc['accessors'][attrs['POSITION']].update(min=[min(v[i] for v in positions) for i in range(3)],max=[max(v[i] for v in positions) for i in range(3)])
        if source.m_Normals:attrs['NORMAL']=append_accessor(doc,data,[(-v[0],v[1],v[2]) for v in source.m_Normals],'VEC3')
        if source.m_UV0:attrs['TEXCOORD_0']=append_accessor(doc,data,[(v[0],1-v[1]) for v in source.m_UV0],'VEC2')
        mesh={'name':filt.m_Mesh.read().m_Name,'primitives':[]}
        for i,triangles in enumerate(source.get_triangles()):
            if not triangles:continue
            mat=renderer.m_Materials[i].read().m_Name
            mi=next((i for i,m in enumerate(doc['materials']) if m.get('name')==mat),None)
            if mi is None:mi=len(doc['materials']);doc['materials'].append({'name':mat})
            mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(doc,data,[(v,) for a,b,c in triangles for v in (a,c,b)],'SCALAR',5125),'material':mi})
        node['mesh']=len(doc['meshes']);doc['meshes'].append(mesh);restored.append(name)
    for node in doc['nodes']:
        if 'mesh' not in node or 'skin' not in node:continue
        name=original_name(node.get('name',''),originals);renderer=originals.get(name)
        if renderer is None or renderer.object_reader.type.name!='SkinnedMeshRenderer':continue
        # Some original cafe prefabs retain enabled placeholder renderers with
        # an explicitly null mesh. They have no source surface to reconstruct.
        if not renderer.m_Mesh.m_PathID:
            node.pop('mesh',None);node.pop('skin',None);node.setdefault('extras',{})['BA_exportPlaceholder']=True;defaults[name]=False;empty.append(name);continue
        source=MeshHandler(renderer.m_Mesh.read());source.process()
        indices=source.m_BoneIndices
        if source.m_BoneWeights is not None or not indices or not all(len(v)==1 for v in indices):continue
        joints=doc['skins'][node['skin']]['joints'];joint_names=[doc['nodes'][i]['name'] for i in joints]
        remap=[joint_names.index(b.read().m_GameObject.read().m_Name) for b in renderer.m_Bones]
        positions={}
        for v,p in enumerate(source.m_Vertices):positions.setdefault(tuple(round(x,6) for x in (-p[0],p[1],p[2])),[]).append(v)
        rebuilt_rigid=False
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            uv=read_accessor(doc,data,primitive['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in primitive['attributes'] else None
            normals=read_accessor(doc,data,primitive['attributes']['NORMAL']) if 'NORMAL' in primitive['attributes'] else None
            bindings=[]
            for v,p in enumerate(read_accessor(doc,data,primitive['attributes']['POSITION'])):
                candidates=positions.get(tuple(round(x,6) for x in p),[])
                choices={remap[indices[i][0]] for i in candidates}
                if len(choices)>1 and uv and normals:
                    candidates=[i for i in candidates if max(abs(a-b) for a,b in zip((*uv[v],*normals[v]),(source.m_UV0[i][0],1-source.m_UV0[i][1],-source.m_Normals[i][0],source.m_Normals[i][1],source.m_Normals[i][2])))<1e-4]
                    choices={remap[indices[i][0]] for i in candidates}
                if len(choices)!=1:
                    rebuild_rigid_mesh(doc,data,node,renderer,source,remap)
                    rebuilt_rigid=True
                    break
                bindings.append((next(iter(choices)),0,0,0))
            if rebuilt_rigid:break
            primitive['attributes']['JOINTS_0']=append_accessor(doc,data,bindings,'VEC4',5123)
            primitive['attributes']['WEIGHTS_0']=append_accessor(doc,data,[(1,0,0,0)]*len(bindings),'VEC4')
        repaired.append(name)
    result={'staticMeshes':restored,'rigidSkins':repaired,'inactiveStaticMeshes':inactive,'emptySkins':empty}
    doc.setdefault('extras',{})['BA_geometry_repairs']=result
    return result
