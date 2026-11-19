"""Export resolved cafe timelines with the optional offline binding manifest."""
import json,pathlib,os,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
profiles=json.loads((W/'furniture-profiles.json').read_text(encoding='utf8'))
if sys.argv[1:]:profiles=[p for p in profiles if p['character'] in sys.argv[1:]]
index=json.loads((W/'furniture-index.json').read_text(encoding='utf8'))
roots={p['root'].lower().removeprefix('cafe_') for p in profiles}
targets={index['prefabs'][p['icon'].lower()]['bundle'] for p in profiles}
for p in (W/'selected').glob('character-*-_mxload-prefabs-*.bundle'):
    if any(p.name.startswith('character-'+r.removesuffix('_cafeonly')+'-') for r in roots):targets.add(p.name)
inputs=[{'path':str(p),'node_id':p.name,'target':p.name in targets} for p in (W/'selected').glob('*.bundle') if p.name in targets or any(k in p.name for k in ['-materials-','-textures-','-meshes-','-animationclips-','-animatorcontrollers-','-assets-'])]
request={'schema_version':0,'operation':'export_primary_content','inputs':inputs,'output_directory':str(W/'furniture-exported/all'),'concurrency':2}
(W/'furniture-all-request.json').write_text(json.dumps(request))
env={**os.environ,'BA_FURNITURE_BINDINGS':str(W/'furniture-bindings.json')}
with (W/'furniture-all-export.log').open('w',encoding='utf8') as log:
    subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),str(W/'furniture-all-request.json'),str(W/'furniture-all-result.json')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('Exported',len(targets),'target bundles',flush=True)
