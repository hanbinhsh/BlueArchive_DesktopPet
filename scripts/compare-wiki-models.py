"""Explicit mapping of every relevant entry in the user's reference page."""
import json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[1];root=R/'.assets/expanded-ready'
entries=json.loads((R/'test-results/wiki-model-inventory.json').read_text(encoding='utf8'))
special={'Arisu':'aris','Arisu (Battle)':'aris_battle','Arisu (Maid)':'aris_maid',
 'Arisu (Battle) (Carrier)':'aris_battle_carrier','Arisu (Battle) (Scenario)':'aris_battle_light',
 'Kei (Carrier 2)':'kei_carrier','Kei (Carrier)':'kei_story','Kei (Scenario 1)':'kei_story','Kei (Scenario 2)':'kei_combat_story',
 'Natsu (Band) (No Weapon)':'natsu_band_relax','Toki':'toki_combat','Toki (Cafe)':'toki','Toki (Battle) (Scenario)':'toki_battle_story',
 'Shiroko＊Terror':'shiroko_terror','Shun (Kid)':'shun_small','Shun (Swimsuit) (1)':'shun_swimsuit','Shun (Swimsuit) (2)':'shun_swimsuit_small',
 'Koyuki (Pajama)':'koyuki_pajamas','Yuuka (Pajama)':'yuuka_pajama','Yuuka (Sportswear)':'yuuka_track','Mari (Sportswear)':'mari_track',
 'Toki (Bunny Girl)':'toki_bunny','Shiroko (Riding)':'shiroko_cycling',
 'Maki (Camping)':'maki_camp','Midori (Battle)':'midori_coat','Momoi (Battle)':'momoi_coat'}
rows=[]
for e in entries:
    title=e['filename'][:-4]
    if title in ['Kei (Prototype)','Mika (Cut-in)']:
        rows.append({**e,'pack':None,'status':'特殊资源，未作为可互动外观加入','reason':'原型测试模型，无动画' if title.startswith('Kei') else '原版服装的技能 Cut-in 专用模型，缺少桌宠待机与互动；不冒充新服装'})
        continue
    name=title.split(' (')[0];suffixes=re.findall(r'\(([^)]+)\)',title)
    key=special.get(title,name.lower()+''.join('_'+s.lower().replace(' ','') for s in suffixes))
    if not (root/key/'character.json').exists():
        rows.append({**e,'pack':key,'status':'未映射','reason':'需要核对名称'});continue
    c=json.loads((root/key/'character.json').read_text(encoding='utf8'))
    status='已加入';reason='独立外观或动作形态，可在角色与动作窗口选择'
    if title=='Kei (Carrier)':
        status='已加入';reason='服装归入白色剧情服，其独立 Idle 已作为“白色剧情服 · 携带待机”提供'
    rows.append({**e,'pack':key,'status':status,'reason':reason,'localName':c['name'],'availableActions':len(c['actions'])})
(R/'test-results/wiki-model-comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for x in rows:
    if x['status']!='已加入':print(x['filename'],x['status'],x['pack'])
print('Compared',len(rows),'models')
