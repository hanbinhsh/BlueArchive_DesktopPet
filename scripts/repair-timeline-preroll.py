"""Patch only pre-roll samples of installed cafe timelines; keep IDs and curves."""
import json,pathlib,sys,os
from glb import load,read_accessor,append_accessor,save,compact
R=pathlib.Path(__file__).resolve().parents[1]
root=pathlib.Path(os.environ.get('BA_CHARACTER_OUTPUT',R/'.assets/repair-2026-10-29'))
report=[]
for profile in json.loads((R/'.assets/furniture-profiles.json').read_text('utf8')):
    start=min(c['start'] for c in profile['studentTrack']['clips'])
    file=root/profile['character']/'character.json'
    if start<1e-6 or not file.exists():continue
    manifest=json.loads(file.read_text('utf8'))
    furniture=next((f for f in manifest.get('furniture',[]) if f.get('sourceTimeline')==profile['icon'] and f.get('sourceStudentTrack')==profile['studentTrack']['name']),None)
    if not furniture:
        matches=[f for f in manifest.get('furniture',[]) if f['id'].startswith('f'+str(profile['furnitureId'])+'_')]
        if len(matches)==1:furniture=matches[0]
        else:continue
    doc,binary=load(file.parent/furniture['model'])
    body_nodes=len(load(file.parent/'model.glb')[0]['nodes']);count=0
    for animation in doc['animations']:
        for channel in animation['channels']:
            if channel['target']['node']>=body_nodes:continue
            sampler=animation['samplers'][channel['sampler']]
            assert sampler['interpolation']=='LINEAR'
            times=[v[0] for v in read_accessor(doc,binary,sampler['input'])]
            values=read_accessor(doc,binary,sampler['output'])
            first=min(range(len(times)),key=lambda i:abs(times[i]-start))
            assert abs(times[first]-start)<1e-6
            for i,t in enumerate(times):
                if t<start-1e-8:values[i]=values[first]
            sampler['output']=append_accessor(doc,binary,values,doc['accessors'][sampler['output']]['type']);count+=1
    save(file.parent/furniture['model'],doc,compact(doc,binary))
    report.append({'character':profile['character'],'id':furniture['id'],'preRoll':start,'channels':count})
(R/'test-results/timeline-preroll-1029.json').write_text(json.dumps(report,indent=2),'utf8')
print(report)
