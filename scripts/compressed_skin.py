"""Decode Unity's 5-bit skin stream, including its implied fourth influence."""
def decode_packed_skin(weight_values,bone_values,vertex_count):
    bones=iter(bone_values);rows=[];indices=[];weights=[];joints=[];total=0
    for raw in weight_values:
        raw=int(raw)
        if not 0<=raw<=31:raise ValueError('Invalid 5-bit skin weight')
        try:joint=int(next(bones))
        except StopIteration:raise ValueError('Truncated bone-index stream')from None
        total+=raw
        if total>31:raise ValueError('Skin weight sum exceeds packed unit')
        weights.append(raw/31);joints.append(joint)
        if total<31 and len(weights)==3:
            try:joints.append(int(next(bones)))
            except StopIteration:raise ValueError('Missing implied influence index')from None
            weights.append((31-total)/31);total=31
        if total==31:
            rows.append(tuple(weights)+(0.,)*(4-len(weights)));indices.append(tuple(joints)+(0,)*(4-len(joints)))
            weights=[];joints=[];total=0
    if weights or len(rows)!=vertex_count:raise ValueError('Incomplete packed skin vertices')
    if next(bones,None)is not None:raise ValueError('Unexpected trailing bone indices')
    return rows,indices

def repair_compressed_skin(source):
    weights=source.m_BoneWeights
    if weights is None or all(all(v>=0 for v in row)and abs(sum(row)-1)<1e-4 for row in weights):return 0
    packed=getattr(source.src,'m_CompressedMesh',None)
    if packed is None or not packed.m_Weights.m_NumItems:raise ValueError('Invalid native skin without packed source')
    from UnityPy.helpers.MeshHelper import unpack_ints
    corrected,indices=decode_packed_skin(unpack_ints(packed.m_Weights),unpack_ints(packed.m_BoneIndices),len(source.m_Vertices))
    assert list(map(tuple,source.m_BoneIndices))==indices,'Packed skin changed source bone references'
    changed=sum(a!=b for a,b in zip(map(tuple,weights),corrected));source.m_BoneWeights=corrected
    return changed
