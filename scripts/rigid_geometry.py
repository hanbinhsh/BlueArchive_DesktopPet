"""Recover rigid props directly when export vertex merging loses joint identity."""
from glb import append_accessor
from compressed_skin import repair_compressed_skin

def rebuild_rigid_mesh(doc, binary, node, renderer, source, remap, *, weighted=False):
    positions=[(-v[0],v[1],v[2]) for v in source.m_Vertices]
    attrs={'POSITION':append_accessor(doc,binary,positions,'VEC3'),
           'JOINTS_0':append_accessor(doc,binary,[(remap[v[0]],0,0,0) for v in source.m_BoneIndices],'VEC4',5123),
           'WEIGHTS_0':append_accessor(doc,binary,[(1,0,0,0)]*len(positions),'VEC4')}
    if weighted:
        repaired=repair_compressed_skin(source)
        if repaired:doc.setdefault('extras',{}).setdefault('BA_packed_skin_repaired',[]).append({'node':node['name'],'vertices':repaired,'reason':'Unity 5-bit implied fourth weight decoded from original packed stream'})
        assert source.m_BoneWeights is not None
        assert all(len(w)<=4 and abs(sum(w)-1)<1e-4 for w in source.m_BoneWeights)
        attrs['JOINTS_0']=append_accessor(doc,binary,[tuple(remap[j] for j in row)+(0,)*(4-len(row)) for row in source.m_BoneIndices],'VEC4',5123)
        attrs['WEIGHTS_0']=append_accessor(doc,binary,[tuple(row)+(0,)*(4-len(row)) for row in source.m_BoneWeights],'VEC4')
    doc['accessors'][attrs['POSITION']].update(min=[min(v[i] for v in positions) for i in range(3)],max=[max(v[i] for v in positions) for i in range(3)])
    if source.m_Normals:attrs['NORMAL']=append_accessor(doc,binary,[(-v[0],v[1],v[2]) for v in source.m_Normals],'VEC3')
    if source.m_UV0:attrs['TEXCOORD_0']=append_accessor(doc,binary,[(v[0],1-v[1]) for v in source.m_UV0],'VEC2')
    mesh={'name':node['name'],'primitives':[]}
    for i,triangles in enumerate(source.get_triangles()):
        if not triangles:continue
        name=renderer.m_Materials[i].read().m_Name
        material=next((j for j,m in enumerate(doc['materials']) if m.get('name')==name),None)
        if material is None:material=len(doc['materials']);doc['materials'].append({'name':name})
        mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(doc,binary,[(v,) for a,b,c in triangles for v in (a,c,b)],'SCALAR',5125),'material':material})
    assert mesh['primitives'],'Original rigid mesh has no geometry'
    node['mesh']=len(doc['meshes']);doc['meshes'].append(mesh)
    doc.setdefault('extras',{}).setdefault('BA_rigid_topology_restored',[]).append(node['name'])
