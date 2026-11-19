import pathlib,json,subprocess
R=pathlib.Path.cwd();W=R/'.assets';specs=json.load(open('scripts/roster-expansion.json',encoding='utf-8'))
for name in specs:
 p=W/f'{name}-request.json';r=json.loads(p.read_text());own={x['path'] for x in r['inputs']}
 r['inputs'] += [{'path':str(p),'node_id':p.name,'target':False} for p in (W/'selected').glob('*.bundle') if str(p) not in own and any(k in p.name for k in ['-materials-','-textures-','-meshes-'])]
 p.write_text(json.dumps(r))
 with (W/f'{name}-export.log').open('w') as log:
  result=subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'exporter/AssetRipperExporter.dll'),str(p),str(W/f'{name}-result.json')],stdout=log,stderr=subprocess.STDOUT)
 print(name,result.returncode,flush=True)
