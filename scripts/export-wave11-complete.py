"""Export own body animations that support-unit controllers omit from the cafe."""
import json,os,re,subprocess,pathlib,UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
specs=json.loads((R/'scripts/roster-wave11.json').read_text(encoding='utf8'))
inputs={};bindings={};excluded={}
for key,(prefix,_) in specs.items():
    request=json.loads((W/f'{key}-request.json').read_text(encoding='utf8'))
    for item in request['inputs']:inputs[item['path']]={**item,'target':False}
    files=[p for p in (W/'selected').glob('*.bundle') if prefix.lower()+'-' in p.name]
    env=UnityPy.load(*map(str,files));names=sorted({o.read().m_Name for o in env.objects if o.type.name=='AnimationClip' and o.read().m_Name.startswith(prefix+'_')})
    skip=lambda n:bool(re.search(r'(?:_Cam(?:$|_)|_Dron|_prop|_Soldier|_my_)',n,re.I))
    bindings[prefix]=[n for n in names if not skip(n)]
    excluded[prefix]=[n for n in names if skip(n)]
    targets=[p for p in files if f'character-{prefix.lower()}-' in p.name and '-prefabs-' in p.name]
    assert targets,key
    for p in targets:inputs[str(p)]['target']=True
request={'schema_version':0,'operation':'export_primary_content','inputs':list(inputs.values()),'output_directory':str(W/'exported/wave11-complete'),'concurrency':2}
req=W/'wave11-complete-request.json';req.write_text(json.dumps(request),encoding='utf8')
bind=W/'wave11-complete-bindings.json';bind.write_text(json.dumps(bindings),encoding='utf8')
(R/'test-results/wave11-body-clip-scope.json').write_text(json.dumps({'included':bindings,'sceneOrCameraTracks':excluded},indent=2),encoding='utf8')
with (W/'wave11-complete-export.log').open('w',encoding='utf8') as log:
    result=subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),str(req),str(W/'wave11-complete-result.json')],env={**os.environ,'BA_FURNITURE_BINDINGS':str(bind)},stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0
print('Exported own body clips for',len(bindings),'models')
