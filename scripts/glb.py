"""Small GLB container helpers for lossless game-asset adaptation."""
import json
import struct

def load(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + size])
    return doc, bytearray(raw[28 + size:])

def save(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'] = [{'byteLength': len(binary)}]
    text = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode()
    text += b' ' * (-len(text) % 4)
    path.write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(text) + len(binary)) + struct.pack('<II', len(text), 0x4E4F534A) + text + struct.pack('<II', len(binary), 0x004E4942) + binary)

def read_accessor(doc, binary, index):
    acc = doc['accessors'][index]
    view = doc['bufferViews'][acc['bufferView']]
    fmt = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[acc['componentType']]
    count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[acc['type']]
    fmt = '<' + fmt * count
    stride = view.get('byteStride', struct.calcsize(fmt))
    offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    return [struct.unpack_from(fmt, binary, offset + i * stride) for i in range(acc['count'])]

def append_view(doc, binary, data, target=None):
    binary += b'\0' * (-len(binary) % 4)
    view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}
    if target:
        view['target'] = target
    views = doc.setdefault('bufferViews', [])
    index = len(views)
    views.append(view)
    binary.extend(data)
    return index

def append_accessor(doc, binary, values, kind, component=5126):
    fmt = {5123: 'H', 5125: 'I', 5126: 'f'}[component]
    data = b''.join(struct.pack('<' + fmt * len(v), *v) for v in values)
    view = append_view(doc, binary, data, 34963 if kind == 'SCALAR' else 34962)
    accessors = doc.setdefault('accessors', [])
    index = len(accessors)
    accessors.append({'bufferView': view, 'componentType': component, 'count': len(values), 'type': kind})
    return index

def compact(doc, binary):
    """Keep referenced embedded data only, deduplicating identical buffer views."""
    def select(key, used):
        ids=sorted(set(used));mapping={old:new for new,old in enumerate(ids)}
        doc[key]=[doc.get(key,[])[i] for i in ids]
        return mapping
    primitives=[p for m in doc.get('meshes',[]) for p in m['primitives']]
    materials=select('materials',[p['material'] for p in primitives if 'material' in p])
    for p in primitives:
        if 'material' in p:p['material']=materials[p['material']]
    def texture_infos(value):
        if not isinstance(value,dict):return []
        is_texture=lambda k,v:k.endswith(('Texture','Tex')) and isinstance(v,dict) and 'index' in v
        return [v for k,v in value.items() if is_texture(k,v)]+[x for k,v in value.items() if not is_texture(k,v) for x in texture_infos(v)]
    infos=[v for m in doc['materials'] for v in texture_infos(m)]
    textures=select('textures',[v['index'] for v in infos])
    for v in infos:v['index']=textures[v['index']]
    images=select('images',[v['source'] for v in doc['textures']])
    samplers=select('samplers',[v['sampler'] for v in doc['textures'] if 'sampler' in v])
    for t in doc['textures']:
        t['source']=images[t['source']]
        if 'sampler' in t:t['sampler']=samplers[t['sampler']]
    used=[]
    for p in primitives:
        used.extend(p['attributes'].values())
        if 'indices' in p:used.append(p['indices'])
        for t in p.get('targets',[]):used.extend(t.values())
    used.extend(s['inverseBindMatrices'] for s in doc.get('skins',[]) if 'inverseBindMatrices' in s)
    used.extend(s[k] for a in doc.get('animations',[]) for s in a['samplers'] for k in ['input','output'])
    accessors=select('accessors',used)
    for p in primitives:
        p['attributes']={k:accessors[v] for k,v in p['attributes'].items()}
        if 'indices' in p:p['indices']=accessors[p['indices']]
        if 'targets' in p:p['targets']=[{k:accessors[v] for k,v in t.items()} for t in p['targets']]
    for s in doc.get('skins',[]):
        if 'inverseBindMatrices' in s:s['inverseBindMatrices']=accessors[s['inverseBindMatrices']]
    for a in doc.get('animations',[]):
        for s in a['samplers']:
            for k in ['input','output']:s[k]=accessors[s[k]]
    assert not any('sparse' in a for a in doc['accessors'])
    referenced=[*doc['accessors'],*doc['images']]
    view_ids=sorted({v['bufferView'] for v in referenced});views=[];mapping={};seen={};output=bytearray()
    for old in view_ids:
        view=doc['bufferViews'][old];offset=view.get('byteOffset',0);raw=bytes(binary[offset:offset+view['byteLength']])
        key=(raw,view.get('byteStride'),view.get('target'))
        if key not in seen:
            output.extend(b'\0'*(-len(output)%4));seen[key]=len(views)
            views.append({**view,'buffer':0,'byteOffset':len(output)});output.extend(raw)
        mapping[old]=seen[key]
    for v in referenced:v['bufferView']=mapping[v['bufferView']]
    doc['bufferViews']=views
    return output
