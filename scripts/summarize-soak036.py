"""Summarize recorded process and renderer resource counts without inventing VRAM."""
from pathlib import Path
from collections import defaultdict
import json

root=Path(__file__).resolve().parent.parent
report=json.loads((root/'test-results/release036-soak.json').read_text('utf8'))
assert report['complete'] and report['elapsedSeconds']>=1800
groups=defaultdict(list)
for sample in report['samples']:
    groups[(sample['character'],sample['diagnostics']['scene'])].append(sample)
scenes=[]
for (character,scene),samples in sorted(groups.items()):
    resources={name:[s['diagnostics']['memory'][name] for s in samples]
               for name in ['geometries','textures']}
    scenes.append({'character':character,'scene':scene,'samples':len(samples),
        'cycles':sorted({s['cycle'] for s in samples}),
        'resources':{name:{'min':min(values),'max':max(values),'first':values[0],'last':values[-1]}
                     for name,values in resources.items()}})
gpu=[p['memoryMiB'] for s in report['samples'] for p in s['metrics'] if p['type']=='GPU']
output={'elapsedSeconds':report['elapsedSeconds'],'fps':report['fps'],
        'totalProcessWorkingSetMiB':report['memoryMiB'],
        'gpuProcessWorkingSetMiB':{'min':min(gpu),'max':max(gpu)},
        'note':'GPU process working set is system RAM, not measured VRAM. Geometry and texture values are live Three.js resource counts.',
        'scenes':scenes}
(root/'test-results/release036-resource-summary.json').write_text(json.dumps(output,indent=2),'utf8')
print(json.dumps({k:v for k,v in output.items() if k!='scenes'},indent=2))
