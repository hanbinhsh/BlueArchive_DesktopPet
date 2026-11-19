import json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R/'.assets';deps=json.loads((W/'bedroom-dependencies.json').read_text())
target='assets-_mx-field-scenes-_mxdependency-prefabs-2025-07-02_assets_all_2828894490.bundle'
assert target in deps['dependencies']
inputs=[{'path':str(W/'selected'/n),'node_id':n,'target':n==target} for n in deps['dependencies']]
timelines=json.loads((W/'bedroom-timelines.json').read_text());bindings={}
for t in timelines:
    for tr in t['tracks']:
        if tr['binding'] and any(s in tr['binding'] for s in ['Bed_Mesh','Windowsofa_Mesh']):bindings.setdefault(tr['binding'].split('/')[-1],set()).update(c['name'] for c in tr['clips'])
bind=W/'bedroom-animation-bindings.json';bind.write_text(json.dumps({k:sorted(v) for k,v in bindings.items()}))
request={'schema_version':0,'operation':'export_primary_content','inputs':inputs,'output_directory':str(W/'bedroom-exported'),'concurrency':1}
req=W/'bedroom-request.json';req.write_text(json.dumps(request),encoding='utf8')
with (W/'bedroom-export.log').open('w',encoding='utf8') as log:
    subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'scene-filter-exporter/AssetRipperExporter.dll'),str(req),str(W/'bedroom-result.json')],env={**os.environ,'BA_EXPORT_NAME_FILTER':'field_833_zone01','BA_FURNITURE_BINDINGS':str(bind)},stdout=log,stderr=subprocess.STDOUT,check=True)
print('Exported named bedroom prefab')
