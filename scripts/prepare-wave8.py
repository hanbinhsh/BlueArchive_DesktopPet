"""Stage the six requested characters using verified original sources."""
import json, os, pathlib, runpy, sys, traceback
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
specs=json.loads((R/'scripts/roster-wave8.json').read_text(encoding='utf8'))
specs.update(json.loads((R/'scripts/roster-variants-wave8.json').read_text(encoding='utf8')))
selected=sys.argv[1:] or list(specs)
folders=[W/'selected',W/'costume-audit',W/'costume-variants']
files={p.name:p for folder in folders for p in folder.glob('*.bundle')}
env=UnityPy.load(*map(str,files.values()))
combined=W/'wave8-all-specs.json';combined.write_text(json.dumps(specs,ensure_ascii=False),encoding='utf8')
os.environ.update(BA_ROSTER_SPECS=str(combined),BA_CHARACTER_OUTPUT=str(W/'wave8-ready'),BA_SOURCE_DIRS=json.dumps(list(map(str,folders))))
profiles=R/'scripts/wave8-profiles.json'
if profiles.exists():os.environ['BA_ROSTER_PROFILES']=str(profiles)
results=[]
for pack in selected:
    try:
        sys.argv=['prepare-roster.py',pack]
        runpy.run_path(str(R/'scripts/prepare-roster.py'),init_globals={'source_environment':env})
        results.append({'character':pack,'prepared':True})
    except Exception as error:
        traceback.print_exc();results.append({'character':pack,'prepared':False,'error':str(error)})
halo_specs={k:v for k,v in specs.items() if any(r['character']==k and r['prepared'] for r in results)}
halo_file=W/'wave8-halo-specs.json';halo_file.write_text(json.dumps(halo_specs,ensure_ascii=False),encoding='utf8')
os.environ['BA_ROSTER_SPECS']=str(halo_file);os.environ['BA_HALO_REPORT']='test-results/wave8-halos.json'
if halo_specs:runpy.run_path(str(R/'scripts/prepare-halo-follow.py'),init_globals={'source_environment':env})
(R/'test-results/wave8-preparation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('Prepared',sum(r['prepared'] for r in results),'/',len(results),flush=True)
if not all(r['prepared'] for r in results):sys.exit(1)
