"""Validate added packs against their official exported clips and prior release."""
import hashlib, json, pathlib, zipfile
from glb import load, read_accessor
R=pathlib.Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
specs=read(R/'scripts/roster-extras.json')
profiles=read(R/'scripts/extra-costume-profiles.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for pack,(prefix,label) in specs.items():
    path=R/'characters'/pack
    manifest=read(path/'character.json');doc,binary=load(path/'model.glb')
    assert manifest['id']==pack and manifest['name']==label
    assert not manifest.get('auditOnly') and (path/'thumbnail.png').is_file()
    exports=[p for p in (R/'.assets/exported/extra-costumes').rglob('*.glb') if p.stem==prefix]
    assert len(exports)==1,(pack,exports)
    original,raw=load(exports[0])
    expected={a[0]:a[2] for a in profiles[pack]['actions']}
    assert {a['id'] for a in manifest['actions']}==set(expected)
    meta={c['track']:c for c in doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']}
    source_meta={c['track']:c for c in original['scenes'][0]['extras']['BAAD_unity_animation']['clips']}
    offsets={o['clip']:o for o in doc['scenes'][0]['extras'].get('BA_scene_placement_offsets',[])}
    curves=0
    for action in manifest['actions']:
        track=action['clip'];assert meta[track]['name']==expected[action['id']]
        assert meta[track]==source_meta[track]
        actual=next(a for a in doc['animations'] if a['name']==track)
        source=next(a for a in original['animations'] if a['name']==track)
        assert actual['channels']==source['channels']
        for channel in actual['channels']:
            a=actual['samplers'][channel['sampler']]
            s=source['samplers'][channel['sampler']]
            assert a.get('interpolation')==s.get('interpolation')
            assert read_accessor(doc,binary,a['input'])==read_accessor(original,raw,s['input'])
            values=read_accessor(doc,binary,a['output']);before=read_accessor(original,raw,s['output'])
            placement=offsets.get(track)
            if placement and channel['target']=={'node':placement['node'],'path':'translation'}:
                cubic=a.get('interpolation')=='CUBICSPLINE'
                for i,(now,old) in enumerate(zip(values,before)):
                    delta=placement['translation'] if not cubic or i%3==1 else [0,0,0]
                    assert all(abs(now[j]-old[j]-delta[j])<1e-6 for j in range(3))
            else:assert values==before,(pack,track,channel)
            curves+=1
    halo=doc['scenes'][0]['extras']['BA_halo_follow']
    assert 'Halo' in doc['nodes'][halo['node']]['name']
    assert not any(a.get('uri') for a in doc.get('images',[])+doc.get('buffers',[]))
    rows.append({'id':pack,'modelSha256':sha(path/'model.glb'),'sourceExportSha256':sha(exports[0]),
                 'actions':expected,'unchangedAuthoredChannelsOrDocumentedPlacement':curves,
                 'scenePlacementOffsets':list(offsets.values()),'halo':halo,
                 'dragMode':'pickup' if 'pickup' in expected else 'idle'})
unchanged=[]
with zipfile.ZipFile(R/'release/BA-Desktop-Pet-0.1.16-win-x64.zip') as archive:
    for name in archive.namelist():
        if not name.startswith('resources/characters/') or name.endswith('/'):continue
        relative=name.removeprefix('resources/characters/')
        assert archive.read(name)==(R/'characters'/relative).read_bytes(),relative
        unchanged.append(relative)
assert len(list((R/'characters').glob('*/character.json')))==65
report={'version':'0.1.17','added':rows,'previousVersion':'0.1.16','unchangedPreviousFiles':unchanged}
(R/'test-results/extra-costume-resources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified',len(rows),'new packs, original animation channels/events, and',len(unchanged),'unchanged previous files.')
