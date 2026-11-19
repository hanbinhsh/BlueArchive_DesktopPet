"""Verify the new source curves and keep every previous resource unchanged."""
import json,hashlib,pathlib
from glb import load,read_accessor
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
specs=read(R/'scripts/roster-wave12.json');index=read(R/'test-results/action-source-index.json');rows=[]
for key in specs:
    base=R/'characters'/key;c=read(base/'character.json');doc,data=load(base/c['model']);source=R/index[key][0]['path'];original,raw=load(source)
    candidates=[]
    for entry in index[key]:
        path=R/entry['path'];sd,sb=load(path)
        candidates.append((path,sd,sb,{x['track']:x for x in sd['scenes'][0]['extras']['BAAD_unity_animation']['clips']}))
    meta={x['track']:x for x in doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']}
    curves=0;clip_sources={}
    for action in c['actions']:
        name=action['clip']
        matches=[row for row in candidates if row[3].get(name)==meta[name] and any(a['name']==name for a in row[1].get('animations',[]))]
        assert matches,(key,name,'No matching original metadata')
        original_path,original,raw,_=matches[0];clip_sources[name]=str(original_path.relative_to(R))
        a=next(a for a in doc['animations'] if a['name']==name);b=next(a for a in original['animations'] if a['name']==name)
        assert len(a['channels'])==len(b['channels'])
        for ch,sc in zip(a['channels'],b['channels']):
            assert ch['target']['path']==sc['target']['path']
            assert doc['nodes'][ch['target']['node']]['name']==original['nodes'][sc['target']['node']]['name']
            x=a['samplers'][ch['sampler']];y=b['samplers'][sc['sampler']]
            assert x.get('interpolation')==y.get('interpolation')
            for prop in ['input','output']:assert read_accessor(doc,data,x[prop])==read_accessor(original,raw,y[prop]),(key,name,prop)
            curves+=1
    extras=doc['scenes'][0]['extras']
    if key=='hatsune_miku':assert 'BA_halo_follow' not in extras and not any('halo' in n.get('name','').lower() for n in doc['nodes'])
    else:
        assert 'BA_halo_follow' in extras
        assert any('halo' in n.get('name','').lower() and 'mesh' in n for n in doc['nodes']),key
    assert not any(x.get('uri') for x in doc.get('buffers',[])+doc.get('images',[]))
    assert (base/'thumbnail.png').is_file()
    rows.append({'id':key,'actions':len(c['actions']),'source':str(source.relative_to(R)),'sourceSha256':sha(source),'clipSources':clip_sources,'modelSha256':sha(base/'model.glb'),'unchangedAuthoredChannels':curves})
old=R/'release/v0.2.2/win-unpacked/resources/characters';unchanged=[]
for f in old.rglob('*'):
    if f.is_file():
        relative=f.relative_to(old);assert sha(f)==sha(R/'characters'/relative),relative
        unchanged.append(relative.as_posix())
assert len(list((R/'characters').glob('*/character.json')))==148
report={'version':'0.2.3','added':rows,'baseVersion':'0.2.2','unchangedPreviousFiles':unchanged}
(R/'test-results/wave12-resources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified',len(rows),'added packs;',sum(x['actions'] for x in rows),'actions;',len(unchanged),'unchanged old files')
