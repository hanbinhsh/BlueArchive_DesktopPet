"""Bind only the character's own original clips to its exported prefab."""
import json,os,subprocess,pathlib
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
request=json.loads((W/'hatsune_miku-request.json').read_text(encoding='utf8'))
for item in request['inputs']:item['target']='character-ch9999-' in pathlib.Path(item['path']).name and '-prefabs-' in pathlib.Path(item['path']).name
assert sum(x['target'] for x in request['inputs'])==1
request['output_directory']=str(W/'exported/hatsune_miku-complete');request['concurrency']=1
req=W/'wave9-miku-complete-request.json';req.write_text(json.dumps(request),encoding='utf8')
bindings=W/'wave9-extra-bindings.json';bindings.write_text(json.dumps({'CH9999':['CH9999_Cafe_Idle','CH9999_Cafe_Reaction','CH9999_Cafe_Walk','CH9999_Tactical_Start','CH9999_Exs','CH9999_Exs_Cutin','CH9999_Vital_Retreat']}),encoding='utf8')
env={**os.environ,'BA_FURNITURE_BINDINGS':str(bindings)}
with (W/'wave9-miku-complete-export.log').open('w',encoding='utf8') as log:
    result=subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),str(req),str(W/'wave9-miku-complete-result.json')],env=env,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0
print('Explicit own-clip export completed')
