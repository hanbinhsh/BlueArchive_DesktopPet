"""Limit 0.1.16 resource changes to the requested water fix and Suzumi packs."""
import hashlib,json,pathlib,zipfile
R=pathlib.Path(__file__).resolve().parents[1]
added={'suzumi','suzumi_magical'}
changed=[];normal=0;furniture=0
with zipfile.ZipFile(R/'release/BA-Desktop-Pet-0.1.15-win-x64.zip') as old:
    prior={n for n in old.namelist() if n.startswith('resources/characters/') and not n.endswith('/')}
    for name in prior:
        relative=name.removeprefix('resources/characters/')
        source=R/'characters'/relative
        assert source.is_file(),relative
        if source.read_bytes()!=old.read(name):changed.append(relative)
        elif source.name=='model.glb':normal+=1
        elif source.suffix=='.glb':furniture+=1
    assert changed==['hina_swimsuit/f4301_0.glb'],changed
    for source in (R/'characters').rglob('*'):
        if not source.is_file():continue
        relative=source.relative_to(R/'characters').as_posix()
        if 'resources/characters/'+relative not in prior:assert relative.split('/')[0] in added,relative
    assert normal==55 and furniture==63,(normal,furniture)
report={'baseVersion':'0.1.15','unchangedNormalModels':normal,'unchangedFurnitureModels':furniture,'changedPreviousResources':changed,'addedPacks':sorted(added)}
(R/'test-results/release-delta.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
