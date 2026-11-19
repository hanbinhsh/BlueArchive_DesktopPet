"""Isolated visual audit; these files are not distributable character packs.

Reuse the production material/skin conversion, retaining only an authored
idle clip. No pickup or cafe interaction is synthesized for scenario models.
"""
import json, os, pathlib, sys, traceback
import UnityPy

R = pathlib.Path(__file__).resolve().parents[1]
W = R / '.assets'
sys.path.insert(0, str(R/'scripts'))
specs = {
    'audit_toki': ['CH0187', '时 · 战斗模型核对'],
    'audit_shiroko': ['CH0263_Scenario01', '白子 Terror · 剧情核对'],
    'audit_toki_scenario': ['CH0333_Scenario', '时临战 · 剧情核对'],
    'audit_aris_carrier': ['CH0334_Carrier', '爱丽丝临战 · Carrier 核对'],
    'audit_aris_scenario': ['CH0334_Scenario', '爱丽丝临战 · 剧情核对'],
    'audit_kei_carrier': ['CH0335_Carrier', '凯伊 · Carrier 核对'],
    'audit_kei_carrier2': ['CH0335_Carrier2', '凯伊 · Carrier2 核对'],
    'audit_kei_scenario1': ['CH0335_Scenario_01', '凯伊 · 剧情 01 核对'],
    'audit_kei_scenario2': ['CH0335_Scenario_02', '凯伊 · 剧情 02 核对'],
    'audit_toki_boss': ['Toki_CNC_MG_Boss', '时 · Boss 核对'],
    'audit_hina_static': ['Player_NP0009', '日奈 · 睡衣（源模型静态核对）'],
}
file = W/'costume-variant-specs.json'
file.write_text(json.dumps(specs, ensure_ascii=False), encoding='utf8')
os.environ['BA_ROSTER_SPECS'] = str(file)
os.environ['BA_CHARACTER_OUTPUT'] = str(W/'costume-variant-preview')
inputs = {p.name:p for folder in [W/'selected',W/'costume-audit',W/'costume-variants']
          for p in folder.glob('*.bundle')}
audit_env = UnityPy.load(*map(str, inputs.values()))
source = (R/'scripts/prepare-roster.py').read_text(encoding='utf8')
source = source.replace("profile = profiles.get(pack, {})", "profile = {'exportDirectory':'costume-variants','prefabName':'Field_Player_NP0009' if pack=='audit_hina_static' else prefix}")
source = source.replace("env = globals().get('source_environment') or UnityPy.load(*map(str, source_files.values()))", "env = audit_env")
source = source.replace("assert {'idle','interact','pickup'} <= {a['id'] for a in actions}", "assert {'idle','interact'} <= {a['id'] for a in actions}")
source = source.replace("ignore_missing=pack == 'toki' or profile.get('ignoreMissingVisibility',False)", "ignore_missing=True")
source = source.replace("if mouth_material: manifest", "manifest['auditOnly'] = True\nif mouth_material: manifest")
source = source.replace("if go == model_prefix and", "if go == ('Field_Player_NP0009' if pack == 'audit_hina_static' else model_prefix) and")
static_source = source[:source.index("clips = doc['scenes'")] + """
nodes = {node['name']:i for i,node in enumerate(doc['nodes'])}
doc['scenes'][0].setdefault('extras', {})['BA_pet_visibility'] = {
    'defaults':{str(nodes[n]):v for n,v in initial_visibility.items() if n in nodes},
    'clips':{}}
target = pathlib.Path(os.environ['BA_CHARACTER_OUTPUT'])/pack
target.mkdir(exist_ok=True,parents=True)
save(target/'model.glb',doc,binary)
(target/'character.json').write_text(json.dumps({
    'id':pack,'name':label,'model':'model.glb','auditOnly':True,
    'note':'Static source-model inspection; no desktop-pet animation mapping.'
},ensure_ascii=False,indent=2),encoding='utf8')
"""
start = source.index("choices = [('idle'")
end = source.index("doc['animations'] =", start)
source = source[:start] + """
preferred = {
    'audit_toki':'CH0187_Normal_Idle01',
    'audit_shiroko':'CH0263_Cafe_Idle',
    'audit_toki_boss':'Toki_CNC_MG_Boss_Normal_Idle',
}
name = preferred.get(pack, prefix + ('_Idle' if 'Carrier' in prefix else '_Normal_Idle'))
clip = next(c for c in clips if c['name'] == name)
assert any(a['name'] == clip['track'] and a.get('channels') for a in doc['animations'])
actions = [{'id':'idle','label':'源待机核对','clip':clip['track']}]
events = {clip['track']: mouth_events(clip, default_tile)}
""" + source[end:]
results = []
selected = sys.argv[1:] or specs
for pack in selected:
    sys.argv = ['prepare-roster.py', pack]
    try:
        exec(compile(static_source if pack == 'audit_hina_static' else source, str(R/'scripts/prepare-roster.py'), 'exec'),
             {'__file__':str(R/'scripts/prepare-roster.py'), 'audit_env':audit_env})
        results.append({'id':pack,'success':True})
    except Exception as exc:
        traceback.print_exc()
        results.append({'id':pack,'success':False,'error':str(exc)})
(R/'test-results/costume-variant-preparation.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print(json.dumps(results))
