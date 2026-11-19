"""Export own body animations that support-unit controllers omit from the cafe."""
import json,os,re,subprocess,pathlib,UnityPy,sys
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
specs=json.loads((R/'scripts/roster-wave16.json').read_text(encoding='utf8'))
if sys.argv[1:]:specs={k:v for k,v in specs.items()if k in sys.argv[1:]}
profiles=json.loads((R/'scripts/wave16-profiles.json').read_text('utf8'))
inputs={};bindings={};excluded={}
for key,(prefix,_) in specs.items():
    request=json.loads((W/f'{key}-request.json').read_text(encoding='utf8'))
    for item in request['inputs']:inputs[item['path']]={**item,'target':False}
    files=[p for p in (W/'selected').glob('*.bundle') if prefix.lower()+'-' in p.name]
    env=UnityPy.load(*map(str,files));names=sorted({o.read().m_Name for o in env.objects if o.type.name=='AnimationClip' and o.read().m_Name.startswith(prefix+'_')})
    skip=lambda n:bool(re.search(r'(?:_Cam(?:$|_)|_Dron|_prop|_Soldier|_my_)',n,re.I))
    bindings[prefix]=[n for n in names if not skip(n)]
    bindings[profiles[key]['modelPrefix']]=bindings[prefix]
    excluded[prefix]=[n for n in names if skip(n)]
    targets=[p for p in files if f'character-{prefix.lower()}-' in p.name and '-prefabs-' in p.name]
    assert targets,key
    for p in targets:inputs[str(p)]['target']=True
request={'schema_version':0,'operation':'export_primary_content','inputs':list(inputs.values()),'output_directory':str(W/'exported/wave16-complete'),'concurrency':2}
req=W/'wave16-complete-request.json';req.write_text(json.dumps(request),encoding='utf8')
bind=W/'wave16-complete-bindings.json';bind.write_text(json.dumps(bindings),encoding='utf8')
scope_path=R/'test-results/wave16-body-clip-scope.json'
scope=json.loads(scope_path.read_text('utf8'))if scope_path.exists()else {'included':{},'sceneOrCameraTracks':{}}
scope['included'].update(bindings);scope['sceneOrCameraTracks'].update(excluded)
scope_path.write_text(json.dumps(scope,indent=2),encoding='utf8')
with (W/'wave16-complete-export.log').open('w',encoding='utf8') as log:
    result=subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),str(req),str(W/'wave16-complete-result.json')],env={**os.environ,'BA_FURNITURE_BINDINGS':str(bind),'BA_COMPLETE_PATH_CACHE':'1'},stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0
print('Exported own body clips for',len(bindings),'models')
