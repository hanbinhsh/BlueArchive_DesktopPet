import json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets';inputs={}
for name in ['bedroom-dependencies','band-scene-dependencies']:
    for n in json.loads((W/(name+'.json')).read_text())['dependencies']:
        inputs[n]={'path':str(W/'selected'/n),'node_id':n,'target':('field-scenes-designlevel-field833-_mxload-prefabs-' in n or 'assets-_mx-minigame-dreammaker-_mxdependency-prefabs-' in n or 'minigame-dreammaker-_mxload-prefabs-' in n)}
request={'schema_version':0,'operation':'export_primary_content','inputs':list(inputs.values()),'output_directory':str(W/'scene-furniture-exported'),'concurrency':2}
req=W/'scene-furniture-request.json';req.write_text(json.dumps(request),encoding='utf8')
with (W/'scene-furniture-export.log').open('w',encoding='utf8') as log:
    subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),str(req),str(W/'scene-furniture-result.json')],stdout=log,stderr=subprocess.STDOUT,check=True)
print('Exported scene furniture',sum(x['target'] for x in inputs.values()))
