"""Prepare the eight reviewed appearances in staging, preserving original clips."""
import json, os, pathlib, runpy, sys
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
specs=json.loads((R/'scripts/roster-extras.json').read_text(encoding='utf8'))
profiles=json.loads((R/'scripts/extra-costume-profiles.json').read_text(encoding='utf8'))
selected=sys.argv[1:] or list(specs)
folders=[W/'selected',W/'costume-audit',W/'costume-variants']
files={p.name:p for folder in folders for p in folder.glob('*.bundle')}
env=UnityPy.load(*map(str,files.values()))
os.environ.update({
    'BA_ROSTER_SPECS':str(R/'scripts/roster-extras.json'),
    'BA_ROSTER_PROFILES':str(R/'scripts/extra-costume-profiles.json'),
    'BA_SOURCE_DIRS':json.dumps(list(map(str,folders))),
    'BA_CHARACTER_OUTPUT':str(W/'extra-costume-ready'),
})
for pack in selected:
    sys.argv=['prepare-roster.py',pack]
    runpy.run_path(str(R/'scripts/prepare-roster.py'),init_globals={'source_environment':env})
halo_specs={k:[profiles[k].get('prefabName',v[0]),v[1]] for k,v in specs.items()
            if (W/'extra-costume-ready'/k/'model.glb').exists()}
halo_file=W/'extra-costume-halo-specs.json'
halo_file.write_text(json.dumps(halo_specs,ensure_ascii=False),encoding='utf8')
os.environ['BA_ROSTER_SPECS']=str(halo_file)
os.environ['BA_HALO_REPORT']='test-results/extra-costume-halos.json'
runpy.run_path(str(R/'scripts/prepare-halo-follow.py'),init_globals={'source_environment':env})
print('Prepared staged packages:',selected)
