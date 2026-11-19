"""Adapt the requested official roster in staging; report failures explicitly."""
import json, os, pathlib, runpy, sys, traceback
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
specs=json.loads((R/'scripts/roster-wave7.json').read_text(encoding='utf8'))
selected=sys.argv[1:] or list(specs)
env=UnityPy.load(*map(str,(W/'selected').glob('*.bundle')))
os.environ.update({'BA_ROSTER_SPECS':str(R/'scripts/roster-wave7.json'),
                   'BA_CHARACTER_OUTPUT':str(W/'wave7-ready')})
profiles=R/'scripts/wave7-profiles.json'
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
halo_file=W/'wave7-halo-specs.json';halo_file.write_text(json.dumps(halo_specs,ensure_ascii=False),encoding='utf8')
os.environ['BA_ROSTER_SPECS']=str(halo_file);os.environ['BA_HALO_REPORT']='test-results/wave7-halos.json'
if halo_specs:runpy.run_path(str(R/'scripts/prepare-halo-follow.py'),init_globals={'source_environment':env})
(R/'test-results/wave7-preparation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('Prepared',sum(r['prepared'] for r in results),'/',len(results),flush=True)
if not all(r['prepared'] for r in results):sys.exit(1)
