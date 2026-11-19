import json,pathlib,struct
R=pathlib.Path(__file__).resolve().parents[1]
def header(p):
    with p.open('rb') as f:h=f.read(20);return json.loads(f.read(struct.unpack_from('<I',h,12)[0]))
specs=json.loads((R/'scripts/roster-wave16.json').read_text(encoding='utf8'))
p=R/'test-results/action-source-index.json';index=json.loads(p.read_text(encoding='utf8'))
for key in specs:
    c=json.loads((R/'.assets/wave16-ready'/key/'character.json').read_text(encoding='utf8'))
    base=header(R/'.assets/wave16-ready'/key/'model.glb');names={n.get('name','') for n in base['nodes']};rows=[]
    for folder in [key,'wave16-complete']:
        for source in (R/'.assets/exported'/folder).rglob('*.glb'):
            if source.stat().st_size<20:continue
            d=header(source);anims=d.get('animations',[])
            if not any(a['name']==c['animations']['idle'] for a in anims):continue
            used={d['nodes'][ch['target']['node']].get('name','') for a in anims for ch in a['channels']}
            rows.append({'path':str(source.relative_to(R)),'animations':len(anims),'missingNodes':sorted(used-names),'root':d['nodes'][d['scenes'][0]['nodes'][0]]['name']})
    rows.sort(key=lambda x:(len(x['missingNodes']),-x['animations']));assert rows,key
    index[key]=rows;print(key,rows[0],flush=True)
p.write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf8')
