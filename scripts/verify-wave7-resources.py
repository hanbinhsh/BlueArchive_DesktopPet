"""Check authored clip parity, embedded resources, and the previous release."""
import hashlib,json,pathlib,zipfile
from glb import load,read_accessor
R=pathlib.Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
specs=read(R/'scripts/roster-wave7.json');rows=[]
for pack,(prefix,label) in specs.items():
    folder=R/'characters'/pack;manifest=read(folder/'character.json');doc,data=load(folder/'model.glb')
    assert manifest['id']==pack and manifest['name']==label and (folder/'thumbnail.png').is_file()
    exports=[p for p in (R/'.assets/exported'/pack).rglob('*.glb') if p.stem==prefix]
    assert len(exports)==1,(pack,exports)
    original,raw=load(exports[0]);extras=doc['scenes'][0]['extras']
    metadata={c['track']:c for c in extras['BAAD_unity_animation']['clips']}
    source_meta={c['track']:c for c in original['scenes'][0]['extras']['BAAD_unity_animation']['clips']}
    curves=0
    for action in manifest['actions']:
        clip=action['clip'];assert metadata[clip]==source_meta[clip]
        actual=next(a for a in doc['animations'] if a['name']==clip)
        source=next(a for a in original['animations'] if a['name']==clip)
        assert actual['channels']==source['channels']
        for channel in actual['channels']:
            a=actual['samplers'][channel['sampler']];s=source['samplers'][channel['sampler']]
            assert a.get('interpolation')==s.get('interpolation')
            for key in ['input','output']:
                assert read_accessor(doc,data,a[key])==read_accessor(original,raw,s[key]),(pack,clip,key)
            curves+=1
    halo=extras['BA_halo_follow'];assert 'Halo' in doc['nodes'][halo['node']]['name']
    assert not any(x.get('uri') for x in doc.get('images',[])+doc.get('buffers',[]))
    assert 'pickup' in {a['id'] for a in manifest['actions']}
    if pack=='shun_swimsuit_small':
        assert doc['extras']['BA_renderer_event_layout']=={'3':'CH0355_02_Face01_Mesh','4':'CH0355_02_Face02_Mesh'}
    if pack=='izuna':
        assert manifest['scale']==1 and manifest['framing']['actions']['victory']=={'zoom':.62,'centerY':2}
        assert len(doc['extras']['BA_unresolved_legacy_renderer_events'])==2
    rows.append({'id':pack,'modelSha256':sha(folder/'model.glb'),'sourceExportSha256':sha(exports[0]),
                 'unchangedAuthoredChannels':curves,'actions':[a['id'] for a in manifest['actions']],
                 'halo':halo,'legacyRendererEvents':doc.get('extras',{}).get('BA_unresolved_legacy_renderer_events',[])})
unchanged=[]
with zipfile.ZipFile(R/'release/BA-Desktop-Pet-0.1.17-win-x64.zip') as old:
    for name in old.namelist():
        if not name.startswith('resources/characters/') or name.endswith('/'):continue
        relative=name.removeprefix('resources/characters/')
        assert old.read(name)==(R/'characters'/relative).read_bytes(),relative
        unchanged.append(relative)
assert len(list((R/'characters').glob('*/character.json')))==84
report={'version':'0.1.18','added':rows,'previousVersion':'0.1.17','unchangedPreviousFiles':unchanged}
(R/'test-results/wave7-resources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified',len(rows),'packs and',len(unchanged),'unchanged previous files')
