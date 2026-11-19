"""Find complete source exports matching each installed rig without changing it."""
import json,pathlib,struct,os
R=pathlib.Path(__file__).resolve().parents[1]
def header(p):
    with p.open('rb') as f:
        h=f.read(20);return json.loads(f.read(struct.unpack_from('<I',h,12)[0]))
packs={p.parent.name:(p,header(p.parent/'model.glb'),json.loads(p.read_text(encoding='utf8'))) for root in [R/'characters',R/os.environ.get('BA_ACTION_BASE','.assets/wave8-ready')] for p in root.glob('*/character.json')}
by_idle={}
for key,(_,d,c) in packs.items():by_idle.setdefault(c['animations']['idle'],[]).append(key)
found={k:[] for k in packs}
for p in (R/'.assets/exported').rglob('*.glb'):
    try:d=header(p)
    except Exception:continue
    if not d.get('skins') or not d.get('meshes'):continue
    animations={a['name']:a for a in d.get('animations',[])}
    for clip in animations.keys() & by_idle.keys():
        for key in by_idle[clip]:
            names=[n.get('name','') for n in packs[key][1]['nodes']]
            used={d['nodes'][ch['target']['node']].get('name','') for a in animations.values() for ch in a['channels'] if 'node' in ch['target']}
            missing=sorted(used-set(names))
            found[key].append({'path':str(p.relative_to(R)),'animations':len(animations),'missingNodes':missing,'root':d['nodes'][d['scenes'][0]['nodes'][0]].get('name')})
for k,v in found.items():v.sort(key=lambda x:(len(x['missingNodes']),-x['animations']))
(R/'test-results/action-source-index.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding='utf8')
for k,v in found.items():print(k,v[0] if v else 'NO MATCH')
