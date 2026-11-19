"""Stage original models for the fixed requested/random selection."""
import json,os,pathlib,runpy,sys,traceback
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
specs=json.loads((R/'scripts/roster-wave16.json').read_text(encoding='utf8'))
selected=sys.argv[1:] or list(specs)
folders=[W/'selected',W/'costume-audit',W/'costume-variants']
files={p.name:p for folder in folders for p in folder.glob('*.bundle')}
env=UnityPy.load(*map(str,files.values()))
os.environ.update(BA_ROSTER_SPECS=str(R/'scripts/roster-wave16.json'),BA_CHARACTER_OUTPUT=str(W/'wave16-ready'),BA_SOURCE_DIRS=json.dumps(list(map(str,folders))))
profiles=R/'scripts/wave16-profiles.json'
if profiles.exists():
    os.environ['BA_ROSTER_PROFILES']=str(profiles)
    os.environ['BA_ALLOW_NO_HALO']=json.dumps([k for k,v in json.loads(profiles.read_text('utf8')).items()if v.get('noHalo')])
results=[]
previous=json.loads((R/'test-results/wave16-preparation.json').read_text(encoding='utf8')) if (R/'test-results/wave16-preparation.json').exists() else []
previous_halos=json.loads((R/'test-results/wave16-halos.json').read_text(encoding='utf8')) if (R/'test-results/wave16-halos.json').exists() else {}
for pack in selected:
    try:
        print('Preparing',pack,flush=True)
        sys.argv=['prepare-roster.py',pack]
        runpy.run_path(str(R/'scripts/prepare-roster.py'),init_globals={'source_environment':env})
        results.append({'character':pack,'prepared':True})
    except Exception as error:
        traceback.print_exc();results.append({'character':pack,'prepared':False,'error':str(error)})
halo_specs={k:v for k,v in specs.items() if any(r['character']==k and r['prepared'] for r in results)}
halo_file=W/'wave16-halo-specs.json';halo_file.write_text(json.dumps(halo_specs,ensure_ascii=False),encoding='utf8')
os.environ['BA_ROSTER_SPECS']=str(halo_file);os.environ['BA_HALO_REPORT']='test-results/wave16-halos.json'
if halo_specs:runpy.run_path(str(R/'scripts/prepare-halo-follow.py'),init_globals={'source_environment':env})
previous_halos.update(json.loads((R/'test-results/wave16-halos.json').read_text(encoding='utf8')))
(R/'test-results/wave16-halos.json').write_text(json.dumps(previous_halos,ensure_ascii=False,indent=2),encoding='utf8')
results=[r for r in previous if r['character'] not in selected]+results
(R/'test-results/wave16-preparation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print('Prepared',sum(r['prepared'] for r in results),'/',len(results),flush=True)
if not all(r['prepared'] for r in results):sys.exit(1)
