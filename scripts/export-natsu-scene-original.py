import json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets'
request=json.loads((W/'natsu_band_relax-request.json').read_text(encoding='utf8'))
for item in request['inputs']:item['target']='character-ch0221_nonweapon-' in Path(item['path']).name and '-prefabs-' in Path(item['path']).name
assert any(x['target'] for x in request['inputs'])
request['output_directory']=str(W/'exported/natsu-scene-original');request['concurrency']=1
req=W/'natsu-scene-original-request.json';req.write_text(json.dumps(request),encoding='utf8')
bindings=W/'natsu-scene-original-bindings.json';bindings.write_text(json.dumps({'CH0221_NonWeapon':['CH0221_NonWeapon_'+s for s in ['Idle','Stretching','Study','Drum','DessertTable']]}),encoding='utf8')
with (W/'natsu-scene-original-export.log').open('w',encoding='utf8') as log:
    subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),str(req),str(W/'natsu-scene-original-result.json')],env={**os.environ,'BA_FURNITURE_BINDINGS':str(bindings)},stdout=log,stderr=subprocess.STDOUT,check=True)
print('Exported original Natsu scene clips')
