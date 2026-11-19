"""Verify packaged files and resource parity before publishing the portable ZIP."""
import hashlib, json, pathlib, shutil, sys, zipfile

root = pathlib.Path(__file__).resolve().parents[1]
version = json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
folder = root/'release'/('v'+version)
archive_path = folder/f'BA-Desktop-Pet-{version}-win-x64.zip'
unpacked = folder/'win-unpacked'
digest = lambda data: hashlib.sha256(data).hexdigest()
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    count = 0
    for entry in archive.infolist():
        if entry.is_dir(): continue
        relative = pathlib.PurePosixPath(entry.filename)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert digest(archive.read(entry)) == digest((unpacked/entry.filename).read_bytes()), entry.filename
        count += 1
for source in (root/'characters').rglob('*'):
    if source.is_file():
        assert source.read_bytes() == (unpacked/'resources/characters'/source.relative_to(root/'characters')).read_bytes(), source
report = {'version':version,'bytes':archive_path.stat().st_size,'sha256':digest(archive_path.read_bytes()),'zipCrc':True,'matchedFiles':count,'characterResourcesMatch':True,'soak30Minutes':False}
if version == '0.1.16':
    records=[('roster','roster'),('faces','expressions'),('holdFinal','hold'),
             ('assets','assets'),('expressionSource','expression-source'),('mouthUV','mouth-uv'),
             ('costumeCoverage','costume-coverage'),('transitionsPackaged','transitions-packaged'),
             ('furnitureAssets','furniture-assets'),('furnitureRuntime','furniture-runtime'),
             ('furnitureRun','furniture-runtime-run'),('furnitureMaterials','furniture-alpha-audit'),
             ('furnitureCoverage','furniture-coverage'),('delta','release-delta')]
elif version in ('0.1.14','0.1.15'):
    records = [('furnitureAssets','furniture-assets'),('furnitureRuntime','furniture-runtime'),
               ('furnitureRun','furniture-runtime-run'),('furnitureControls','furniture-controls'),('furnitureMaterials','furniture-alpha-audit'),
               ('furnitureCoverage','furniture-coverage'),('wardrobeParity','furniture-wardrobe-parity'),
               ('holdFinal','hold'),('transitionsPackaged','transitions-packaged')]
elif version == '0.1.13':
    records = [('roster','roster'),('faces','expressions'),('holdFinal','hold'),
               ('assets','assets'),('expressionSource','expression-source'),
               ('propTransitions','prop-transitions'),('mouthUV','mouth-uv'),
               ('costumeCoverage','costume-coverage'),('transitionsPackaged','transitions-packaged')]
elif version == '0.1.12':
    records = [('roster','roster'),('faces','expressions'),('holdFinal','hold'),
               ('assets','assets'),('expressionSource','expression-source'),
               ('propTransitions','prop-transitions'),('mouthUV','mouth-uv'),
               ('transitionsPackaged','transitions-packaged')]
elif version == '0.1.11':
    with zipfile.ZipFile(root/'release/BA-Desktop-Pet-0.1.10-win-x64.zip') as previous:
        for source in (root/'characters').rglob('*'):
            if source.is_file():
                assert source.read_bytes() == previous.read('resources/characters/'+source.relative_to(root/'characters').as_posix()), source
    report['originalResourcesUnchangedFrom010'] = True
    records = [('propTransitions','prop-transitions'),('transitionsUi','transitions-ui'),('transitionsPackaged','transitions-packaged'),('gaze','gaze-tests'),('regressions','regression-010')]
else:
    records = [('roster','roster'),('faces','expressions'),('holdFinal','hold')]
    if version == '0.1.9': records += [('holdWave3','hold-wave3'),('features','features'),('gaze','gaze-tests')]
    else: records += [('regressions','regression-010'),('mariEuler','mari-euler-audit')]
for key, name in records:
    report[key] = json.loads((root/'test-results'/f'{name}.json').read_text(encoding='utf-8'))
if version == '0.1.16':
    added={'suzumi','suzumi_magical'}
    assert {r['character'] for r in report['roster']['results']} == added
    assert report['roster']['restart']
    assert all(r['drag'] and r['transparentHitTest'] and r['offline'] and set(r['actions'])=={'interact','walk','victory','reload','pickup'} for r in report['roster']['results'])
    for key in ['faces','holdFinal','mouthUV','transitionsPackaged']:
        assert {r['character'] for r in report[key]} == added,key
    assert all(len(r['samples'])==23 for r in report['holdFinal'])
    assert len(report['assets'])==len(report['expressionSource'])==57
    assert not report['costumeCoverage']['missing'] and not report['costumeCoverage']['unmappedInstalled']
    assert report['costumeCoverage']['installedPackCount']==57
    assert report['delta']['unchangedNormalModels']==55 and report['delta']['unchangedFurnitureModels']==63
    assert report['delta']['changedPreviousResources']==['hina_swimsuit/f4301_0.glb']
    assert len(report['furnitureAssets'])==report['furnitureCoverage']['interactions']==66
    assert not report['furnitureCoverage']['unadaptedMappedInteractions'] and not report['furnitureMaterials']['errors']
    assert {(r['character'],r['furniture']) for r in report['furnitureRuntime']}=={('hina_swimsuit','f4301_0'),('suzumi_magical','f210385_0'),('suzumi_magical','f210385_1')}
    assert report['furnitureRun']['complete'] and report['furnitureRun']['offline'] and report['furnitureRun']['count']==3
    for executable in [report['roster']['executable'],report['furnitureRun']['executable']]:
        assert pathlib.Path(executable).resolve()==(unpacked/'BA Desktop Pet.exe').resolve()
    water=next(w for w in report['furnitureMaterials']['waterMaterials'] if w['character']=='hina_swimsuit')
    assert water['sourceProperty']=='_BaseColor'
    assert all(abs(a-b)<1e-6 for a,b in zip(water['rgba'],[0,0.8226873874664307,1,0.545098066329956]))
    for entry in json.loads((root/'package.json').read_text(encoding='utf-8'))['build']['extraFiles']:
        assert (root/entry['from']).read_bytes()==(unpacked/entry['to']).read_bytes(),entry
    report['furnitureRuntimeScope']='Three changed/new scenes; other 63 scenes byte-identical to tested 0.1.15 release.'
if version == '0.1.15':
    report['furnitureRepairs']=json.loads((root/'test-results/furniture-repairs.json').read_text(encoding='utf8'))
    assert report['furnitureRepairs']['regressionsPassed'] and report['furnitureRepairs']['ready']==64
    for relative,sha in report['furnitureRepairs']['resources'].items():
        assert digest((unpacked/'resources/characters'/relative).read_bytes())==sha
if version in ('0.1.14','0.1.15'):
    manifests = [json.loads(p.read_text(encoding='utf-8')) for p in (root/'characters').glob('*/character.json')]
    expected = {(c['id'], f['id']) for c in manifests for f in c.get('furniture', [])}
    assert expected == {(r['character'], r['id']) for r in report['furnitureAssets']}
    assert expected == {(r['character'], r['furniture']) for r in report['furnitureRuntime']}
    assert report['furnitureRun']['complete'] and report['furnitureRun']['offline']
    assert report['furnitureRun']['count'] == len(expected) == 64
    for key in ['furnitureRun', 'furnitureControls']:
        assert pathlib.Path(report[key]['executable']).resolve() == (unpacked/'BA Desktop Pet.exe').resolve(), key
    assert all(v is True for k,v in report['furnitureControls'].items() if k != 'executable')
    assert len(report['wardrobeParity']) == len(manifests) == 55
    assert not report['furnitureCoverage']['unadaptedMappedInteractions']
    assert not report['furnitureMaterials']['errors']
    assert {r['character'] for r in report['transitionsPackaged']} == {'kisaki','hoshino','momoi'}
    assert {r['character'] for r in report['holdFinal']} == {'kisaki','hoshino','momoi'}
    assert all(len(r['samples']) == 23 for r in report['holdFinal'])
    for entry in json.loads((root/'package.json').read_text(encoding='utf-8'))['build']['extraFiles']:
        assert (root/entry['from']).read_bytes() == (unpacked/entry['to']).read_bytes(), entry
elif version == '0.1.13':
    added = set(json.loads((root/'scripts/roster-wave5.json').read_text(encoding='utf-8')))
    assert {r['character'] for r in report['roster']['results']} == added
    assert report['roster']['restart'] and 'v0.1.13' in report['roster']['executable']
    for key in ['faces','holdFinal','mouthUV']:
        assert {r['character'] for r in report[key]} == added, key
    assert all(len(r['samples']) == 23 for r in report['holdFinal'])
    assert len(report['assets']) == len(report['expressionSource']) == len(report['propTransitions']) == 55
    assert not report['costumeCoverage']['missing'] and not report['costumeCoverage']['unmappedInstalled']
    assert {r['character'] for r in report['transitionsPackaged']} == {'hoshino_battle','shiroko_terror','aru_dress'}
    with zipfile.ZipFile(root/'release/BA-Desktop-Pet-0.1.12-win-x64.zip') as previous:
        for source in (root/'characters').rglob('*'):
            if not source.is_file() or source.parent.name in added or source.name == 'README.md': continue
            assert source.read_bytes() == previous.read('resources/characters/'+source.relative_to(root/'characters').as_posix()), source
    report['previous45PacksUnchanged'] = True
elif version == '0.1.12':
    report['testNotes'] = ['Kei first sustained-hold run returned to idle unexpectedly; the initial run did not record input events. A repeat with input tracing passed all 23 samples in pickup, and packaged transition tests also passed. Initial interruption cause remains unconfirmed.']
    added = set(json.loads((root/'scripts/roster-wave4.json').read_text(encoding='utf-8')))
    face_targets = added | {'hikari','reisa','nozomi','reisa_magical'}
    assert {r['character'] for r in report['roster']['results']} == added
    assert report['roster']['restart']
    assert {r['character'] for r in report['faces']} == face_targets
    assert {r['character'] for r in report['mouthUV']} == face_targets
    assert {r['character'] for r in report['holdFinal']} == added
    assert all(len(r['samples']) == 23 for r in report['holdFinal'])
    assert len(report['assets']) == len(report['expressionSource']) == len(report['propTransitions']) == 45
    assert {r['character'] for r in report['transitionsPackaged']} == {'hikari','reisa','kei','toki','kisaki'}
(root/'test-results'/f'release-{version}.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
shutil.copy2(archive_path,root/'release'/archive_path.name)
print(json.dumps({k:v for k,v in report.items() if k not in dict(records)},indent=2))
