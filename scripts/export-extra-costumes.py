"""Export official additional outfits, explicitly binding their own scene clips."""
import json, os, pathlib, subprocess, zipfile, zlib
import UnityPy
R=pathlib.Path(__file__).resolve().parents[1];W=R/'.assets'
catalog=json.loads((W/'catalog.json').read_text(encoding='utf8'))
stage=W/'costume-variants';stage.mkdir(exist_ok=True)
# The field prefab has an empty Animator controller. Its own field clips live
# outside it; preserve the game-authored rig paths instead of borrowing Hina's
# student pickup or cafe animations.
evidence=[]
for pack in catalog['FullPatchPacks']:
    bundles=[b for b in pack['BundleFiles'] if 'field-cafe-characteranimation-field_player_np0009-' in b['Name']]
    if not bundles:continue
    with zipfile.ZipFile(W/'packs'/pack['PackName']) as archive:
        for b in bundles:
            raw=archive.read(b['Name'])
            assert len(raw)==b['Size'] and zlib.crc32(raw)==b['Crc']
            (stage/b['Name']).write_bytes(raw);evidence.append({'pack':pack['PackName'],'bundle':b})
inputs={p.name:p for folder in [W/'selected',W/'costume-audit',stage] for p in folder.glob('*.bundle')}
clip_files=[p for p in inputs.values() if 'animationclips' in p.name and
            any(k in p.name for k in ['np0267','np0268','field-characters','field-cafe-characteranimation-field_player_np0009'])]
env=UnityPy.load(*map(str,clip_files))
bindings={'NP0267':set(),'NP0268':set(),'Field_Player_NP0009':set()}
for obj in env.objects:
    if obj.type.name!='AnimationClip':continue
    name=obj.read().m_Name
    for prefix in bindings:
        if name.startswith(prefix+'_'):bindings[prefix].add(name)
assert all(bindings.values()),bindings
bindings={k:sorted(v) for k,v in bindings.items()}
manifest=W/'extra-costume-bindings.json';manifest.write_text(json.dumps(bindings,indent=2),encoding='utf8')
names=['ch0187','toki_cnc_mg_boss','ch0334_scenario','ch0335_scenario_01','ch0263_scenario01','np0267','np0268']
targets={name for name in inputs if name.startswith('field-player-_mxload-prefabs-') or
         any(name.startswith('character-'+prefix+'-_mxload-prefabs-') for prefix in names)}
assert len(targets)>=8
request={'schema_version':0,'operation':'export_primary_content',
         'inputs':[{'path':str(p),'node_id':name,'target':name in targets} for name,p in inputs.items()],
         'output_directory':str(W/'exported/extra-costumes'),'concurrency':2}
file=W/'extra-costumes-request.json';file.write_text(json.dumps(request),encoding='utf8')
environment={**os.environ,'BA_FURNITURE_BINDINGS':str(manifest)}
with (W/'extra-costumes-export.log').open('w',encoding='utf8') as log:
    result=subprocess.run([str(R/'.cache/dotnet/dotnet.exe'),str(W/'euler-exporter/AssetRipperExporter.dll'),
                           str(file),str(W/'extra-costumes-result.json')],env=environment,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,result.returncode
(W/'extra-costumes-binding-evidence.json').write_text(json.dumps({'bindings':bindings,'additionalBundles':evidence},indent=2),encoding='utf8')
print('Exported:',len(targets),'prefab bundles. Explicit original clips:',{k:len(v) for k,v in bindings.items()})
