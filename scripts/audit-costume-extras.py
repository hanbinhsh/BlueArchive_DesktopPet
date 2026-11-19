"""Record confirmed non-student variants separately from playable costume coverage.

Requires the source bundles obtained for the 2026-10-20 audit in
.assets/costume-audit and the two private NPC previews. Does not install packs.
"""
import hashlib, json, pathlib, re
import UnityPy

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / '.assets'
read = lambda p: json.loads(p.read_text(encoding='utf8'))
catalog = read(WORK/'catalog-audit-2026-10-20.json')
assert catalog == read(WORK/'catalog.json')
coverage = read(ROOT/'test-results/costume-coverage.json')
assert coverage['date'] == '2026-10-20'
assert not coverage['missing'] and coverage['expectedPackCount'] == 57
env = UnityPy.load(*map(str,(WORK/'costume-audit').glob('*.bundle')))
clips = {}
for obj in env.objects:
    if obj.type.name == 'AnimationClip':
        clip = obj.read_typetree()
        name = clip['m_Name']
        if name.startswith(('NP0267_','NP0268_')) or 'NP0009' in name:
            clips[name] = {
                'sourceFile':obj.assets_file.name,'pathId':obj.path_id,
                'loop':bool(clip.get('m_MuscleClip',{}).get('m_LoopTime'))
            }

confirmed = [
    {'character':'小桃','sourceId':'NP0267','appearance':'白色外套、粉色围领，无猫耳耳机',
     'status':'未加入 0.1.16','preview':'test-results/roster-npc0267_audit.png'},
    {'character':'小绿','sourceId':'NP0268','appearance':'白色外套、绿色围领，无猫耳耳机',
     'status':'未加入 0.1.16','preview':'test-results/roster-npc0268_audit.png'},
    {'character':'日奈','sourceId':'NP0009','appearance':'场景专用睡衣（粉色波点）',
     'status':'未加入 0.1.16','evidence':'.assets/hina-field-variants.json',
     'preview':'test-results/costume-audit_hina_static.png','previewId':'audit_hina_static'},
    {'character':'凯伊','sourceId':'CH0335_Scenario_01','appearance':'白色剧情服，无原版发箍及校服外套',
     'equivalentSource':'CH0335_Carrier','status':'未加入 0.1.16',
     'preview':'test-results/costume-audit_kei_carrier.png','previewId':'audit_kei_carrier'},
    {'character':'爱丽丝','sourceId':'CH0334_Carrier','appearance':'临战的外部装甲卸除形态',
     'relatedSource':'CH0334_Scenario','status':'未加入 0.1.16',
     'preview':'test-results/costume-audit_aris_carrier.png','previewId':'audit_aris_carrier'},
    {'character':'时','sourceId':'CH0187','appearance':'原版的轻装战斗形态（A 身体）',
     'status':'未加入 0.1.16','preview':'test-results/costume-audit_toki.png','previewId':'audit_toki'},
    {'character':'时','sourceId':'Toki_CNC_MG_Boss','appearance':'机械装甲形态（与 CH0187 共用 B 身体）',
     'status':'未加入 0.1.16','preview':'test-results/costume-audit_toki_boss.png','previewId':'audit_toki_boss'},
]
render = {r['id']:r for r in read(ROOT/'test-results/costume-variant-render.json')}
prepared = read(ROOT/'test-results/costume-variant-preparation.json')
assert len(prepared) == 11 and all(r['success'] for r in prepared)
assert len(render) == 16 and all(r['meshes'] > 0 and r['height'] > 0 for r in render.values())
for entry in confirmed:
    if entry['sourceId'] in ['NP0267','NP0268']:
        entry['sourceClips'] = [name for name in sorted(clips) if entry['sourceId'] in name]
    if entry.get('previewId'):
        entry['verifiedPreviewClip'] = render[entry['previewId']]['clip']
    if 'preview' in entry:
        path = ROOT/entry['preview']
        assert path.is_file()
        entry['previewSha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
installed_mapping = {'NP0267':'momoi_coat','NP0268':'midori_coat','NP0009':'hina_pajamas',
                     'CH0335_Scenario_01':'kei_story','CH0334_Carrier':'aris_battle_light',
                     'CH0187':'toki_combat','Toki_CNC_MG_Boss':'toki_armor'}
for entry in confirmed:
    entry['installedPack'] = installed_mapping[entry['sourceId']]
    if (ROOT/'characters'/entry['installedPack']/'character.json').exists():
        entry['status'] = '已加入 0.1.17'
assert {'NP0267_Idle','NP0267_Walk','NP0267_Interaction01','NP0267_Interaction02','NP0267_Interaction01_Idle',
        'NP0268_Idle','NP0268_Walk','NP0268_Interaction01'} <= set(clips)
assert any(x['name']=='Field_Player_NP0009' and
           any(r['node']=='NP0009_Body' for r in x.get('renderers',[]))
           for x in read(WORK/'hina-field-variants.json'))

inventory = read(ROOT/'test-results/costume-prefab-inventory.json')
assert len(inventory) == 24
geometry = read(ROOT/'test-results/costume-geometry-comparison.json')
assert len(geometry) == 11
def pair(base, variant):
    return next(r for r in geometry if r['baseline']==base and r['variant']==variant)
def body_same(row, base_node, variant_node):
    a=next(r for r in row['baselineRenderers'] if r['node']==base_node)
    b=next(r for r in row['variantRenderers'] if r['node']==variant_node)
    return a['mesh']['geometrySha256']==b['mesh']['geometrySha256'] and [
        m['propertiesSha256'] for m in a['materials']]==[m['propertiesSha256'] for m in b['materials']]
assert body_same(pair('CH0333','CH0333_Scenario'),'CH0333_Body','CH0333_Body')
assert body_same(pair('CH0263','CH0263_Scenario01'),'CH0263_Body','CH0263_Body')
assert body_same(pair('CH0335_Carrier','CH0335_Scenario_01'),'CH0335_Scenario_01_Body','CH0335_Scenario_01_Body')
assert body_same(pair('CH0187','Toki_CNC_MG_Boss'),'CH0187_B_Body','CH0187_B_Body')
technical_review = [
    {'source':'CH0333_Scenario','character':'时','classification':'与临战相同服装；身体网格及材质内容相同，动作／道具不同'},
    {'source':'CH0335_Carrier2 / CH0335_Scenario_02','character':'凯伊','classification':'与已装原版相同服装；动作、武器／道具不同'},
    {'source':'CH0335_Carrier / CH0335_Scenario_01','character':'凯伊','classification':'同一套缺失的白色剧情服，不重复计算两套'},
    {'source':'CH0334_Carrier / CH0334_Scenario','character':'爱丽丝','classification':'临战卸除外部装甲的表现，同类外观；手持武器与动作不同'},
    {'source':'CH0263_Scenario01','character':'白子 Terror','classification':'身体和衣服材质相同；光环不同，作为附件变体单列，不算新服装'},
    {'source':'CH0187 / Toki_CNC_MG_Boss','character':'时','classification':'A 轻装与 B 机械装甲不同；Boss 的 B 身体与 CH0187 的 B 身体相同，不额外重复计算'},
]
report = {
    'date':'2026-10-20','installationUpdate':'2026-10-21',
    'testedRelease':read(ROOT/'package.json')['version'],
    'catalog':{'milestone':catalog['Milestone'],'patch':catalog['PatchVersion'],
               'matchesPackagedSourceCatalog':True,
               'sha256':hashlib.sha256((WORK/'catalog-audit-2026-10-20.json').read_bytes()).hexdigest()},
    'playableCoverage':coverage,
    'reviewedAdditionalVariants':confirmed,
    'confirmedUninstalledVariants':[entry for entry in confirmed if entry['status'] != '已加入 0.1.17'],
    'haloVariantInstalled':(ROOT/'characters/shiroko_terror_story/character.json').is_file(),
    'sourceClips':clips,
    'sourcePrefabInventory':inventory,
    'technicalVariantReview':technical_review,
    'geometryComparison':'test-results/costume-geometry-comparison.json',
    'visualReview':'test-results/costume-variant-render.json',
    'sourceScan':{'bundles':len(read(ROOT/'test-results/costume-source-variants.json')['acquisition']),
                  'roots':len(read(ROOT/'test-results/costume-source-variants.json')['roots']),
                  'contentComparisonPairs':len(geometry),'renderedViews':len(render)},
    'allOfficialAppearancesComplete':False,
    'referenceVideo':'https://www.bilibili.com/video/BV14HkjBhEEC/',
    'referenceVerification':'Video fetch returned HTTP 412; matched private rendered NPC models to the cover screenshot supplied by the user.',
    'limits':[
        'NPC labels describe verified appearance, not an announced recruitable costume name.',
        'NP0267/NP0268 previews include only the exported Idle and Walk clips. Interaction clips were found in source bundles but not yet bound or validated in a deliverable pack.',
        'No Formation_Pickup clip for NP0267/NP0268 was found in the inspected character bundles.',
        'Enemy, carrier and scenario prefab names are inventoried as technical variants, not automatically counted as different clothes.',
        'Seven clothing/equipment appearances were confirmed by the audit; Shiroko Terror has an additional halo-only variant. Current installation status is recorded per entry.',
        'Ten named technical variants and the Hina static model were visually inspected, with five installed baselines.',
        'The scan matches known student IDs/names plus NP0009/NP0267/NP0268 and field prefabs; unrelated opaque NPC codes, skill-cut sets and 2D-only assets are not a proven exhaustive global appearance inventory.',
        'Historical audit previews are not installed packs. Their static/idle-only limitations do not describe the separately adapted 0.1.17 packages.'
    ]
}
output = ROOT/'test-results/costume-extras-2026-10-20.json'
output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Verified',coverage['installedPackCount'],'installed packs; remaining audited omissions:',
      len(report['confirmedUninstalledVariants']),'halo installed:',report['haloVariantInstalled'])
