"""Export selected alternate source prefabs for visual costume review only."""
import json,pathlib,re,subprocess,zipfile,zlib
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
catalog=json.loads((W/'catalog.json').read_text(encoding='utf8'))
names=['CH0187','CH0263_Scenario01','CH0333_Scenario','CH0334_Carrier','CH0334_Scenario',
       'CH0335_Carrier','CH0335_Carrier2','CH0335_Scenario_01','CH0335_Scenario_02','Toki_CNC_MG_Boss']
keys=['ch0187','ch0263','ch0333','ch0334','ch0335','toki_cnc_mg_boss','en0002']
stage=W/'costume-variants'
for pack in catalog['FullPatchPacks']:
    selected=[b for b in pack['BundleFiles'] if
              (any(re.search(r'-'+k+r'(?:_|-)',b['Name']) for k in keys) and
               any(k in b['Name'] for k in ['assets-_mx-characters-','assets-_mx-npcs-','character-','cafe-characteranimation-'])) or
              any(k in b['Name'] for k in ['assets-_mx-field-characters-','assets-_mx-field-animator-','assets-_mx-field-npcs-',
                                           'prologdepengroup-assets-_mx-shaders-_mxprolog-'])]
    if not selected:continue
    with zipfile.ZipFile(W/'packs'/pack['PackName']) as archive:
        for b in selected:
            data=archive.read(b['Name'])
            assert len(data)==b['Size'] and zlib.crc32(data)==b['Crc'],b['Name']
            (stage/b['Name']).write_bytes(data)
inputs={p.name:p for folder in [W/'selected',W/'costume-audit',stage] for p in folder.glob('*.bundle')}
targets={p.name for p in stage.glob('*.bundle') if
         any(p.name.startswith('character-'+name.lower()+'-_mxload-prefabs-') for name in names) or
         p.name.startswith('field-player-_mxload-prefabs-')}
assert len(targets)>=len(names)
request={'schema_version':0,'operation':'export_primary_content',
         'inputs':[{'path':str(p),'node_id':p.name,'target':p.name in targets} for p in inputs.values()],
         'output_directory':str(W/'exported/costume-variants'),'concurrency':2}
file=W/'costume-variants-request.json';file.write_text(json.dumps(request),encoding='utf8')
with (W/'costume-variants-export.log').open('w',encoding='utf8') as log:
    result=subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),
                           str(file),str(W/'costume-variants-result.json')],stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,result.returncode
print('Exported alternate prefab sources; inputs',len(inputs),'target bundles',len(targets))
