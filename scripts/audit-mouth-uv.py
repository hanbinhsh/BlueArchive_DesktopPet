"""Verify each mouth primitive samples its declared base atlas cell."""
import json, sys
from pathlib import Path
from glb import load, read_accessor

report = []
for path in Path('characters').glob('*/character.json'):
    manifest = json.loads(path.read_text('utf-8'))
    if sys.argv[1:] and manifest['id'] not in sys.argv[1:]: continue
    mouth = manifest.get('mouth')
    if not mouth: continue
    doc, binary = load(path.parent/manifest['model'])
    cols, rows = mouth.get('columns',8), mouth.get('rows',8)
    col, row = mouth['defaultTile'] % 100, mouth['defaultTile'] // 100
    u0,v0=mouth.get('baseUV',[col/cols,row/rows])
    bounds = [u0,u0+1/cols,1-v0-1/rows,1-v0]
    coordinates = []
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if doc['materials'][primitive['material']]['name'] != mouth['material']: continue
            uv = read_accessor(doc,binary,primitive['attributes']['TEXCOORD_0'])
            for index, in read_accessor(doc,binary,primitive['indices']): coordinates.append(uv[index])
    assert coordinates, manifest['id']
    for u,v in coordinates:
        assert bounds[0]-1e-4 <= u <= bounds[1]+1e-4 and bounds[2]-1e-4 <= v <= bounds[3]+1e-4, (manifest['id'],u,v,bounds)
    report.append({'character':manifest['id'],'baseTile':mouth['defaultTile'],'atlas':[cols,rows],
                   'u':[min(u for u,v in coordinates),max(u for u,v in coordinates)],
                   'v':[min(v for u,v in coordinates),max(v for u,v in coordinates)],
                   'mirroredEvents':sum(e.get('flipped',False) for es in mouth['events'].values() for e in es)})
Path('test-results/mouth-uv.json').write_text(json.dumps(report,indent=2))
print(len(report),'mouths sample the correct base atlas cell')
