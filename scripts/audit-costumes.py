"""Compare installed packs with the freshly fetched released JP student roster."""
import argparse, hashlib, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--date',default='2026-10-18')
args=parser.parse_args()
snapshot = ROOT/f'.assets/students-audit-{args.date}.json'
students = json.loads(snapshot.read_text(encoding='utf-8'))
names = {
    'Junko':'纯子','Serika':'芹香','Iori':'依织','Mutsuki':'睦月',
    'Kisaki':'妃咲','Hina':'日奈','Hikari':'光','Nozomi':'望','Azusa':'梓',
    'Maki':'真纪','Koyuki':'小雪','Mari':'玛丽','Reisa':'玲纱','Miyako':'宫子',
    'Kayoko':'佳代子','Momoi':'小桃','Midori':'小绿','Aris':'爱丽丝','Kei':'凯伊',
    'Toki':'时','Hoshino':'星野','Shiroko':'白子','Aru':'爱露','Suzumi':'铃美',
    'Hifumi':'日富美','Shun':'瞬','Kokona':'心奈','Koharu':'小春','Miyu':'美游',
    'Seia':'圣娅','Kurumi':'胡桃','Natsu':'夏','Miyo':'美代','Izuna':'泉奈',
    'Yuuka':'优香','Yakumo':'八云','Mika':'未花','Chise':'千世','Kirara':'绮良','Ui':'忧',
    'Miku':'初音未来','Akane':'茜','Mimori':'三森','Otogi':'御伽','Ruiko':'佐天泪子','Moe':'萌绘',
}
aliases = {'koyuki_pajama':'koyuki_pajamas','toki_bunnygirl':'toki_bunny',
           'hoshino_battle_tank':'hoshino_battle','hoshino_battle_dealer':'hoshino_battle'}
installed = {p.parent.name:json.loads(p.read_text(encoding='utf-8'))
             for p in (ROOT/'characters').glob('*/character.json')}
rows = []
for personal_name, chinese_name in names.items():
    source = [s for s in students.values() if s.get('PersonalName') == personal_name and s['IsReleased'][0]]
    assert source, personal_name
    packs = sorted({aliases.get(s['PathName'],s['PathName']) for s in source})
    rows.append({'character':chinese_name,'sourceName':personal_name,
                 'officialRows':[{'id':s['Id'],'name':s['Name'],'devName':s['DevName'],'path':s['PathName']} for s in source],
                 'expectedPacks':packs,'installed':[p for p in packs if p in installed],
                 'missing':[p for p in packs if p not in installed]})
expected = {p for r in rows for p in r['expectedPacks']} | {'plana'}
extras_specs = json.loads((ROOT/'scripts/roster-extras.json').read_text(encoding='utf8'))
extras_specs.update({k:v for k,v in json.loads((ROOT/'scripts/roster-wave7.json').read_text(encoding='utf8')).items() if k not in expected})
extras_specs.update(json.loads((ROOT/'scripts/roster-variants-wave8.json').read_text(encoding='utf8')))
extras = {k:installed[k]['name'] for k in extras_specs if k in installed}
report = {'date':args.date,'source':'https://schaledb.com/data/en/students.json',
          'sourceSha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),
          'scope':'Released JP playable student outfits and Shiroko Terror; combat modes sharing the same cafe outfit count once. Plana is a separately verified NPC.',
          'catalog':'Official JP r96 patch 33','characters':rows,
          'planaInstalled':'plana' in installed,'expectedPackCount':len(expected),
          'installedPackCount':len(installed),'missing':sorted(expected-set(installed)),
          'additionalReviewedPacks':extras,
          'unmappedInstalled':sorted(set(installed)-expected-set(extras))}
(ROOT/'test-results/costume-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines = ['# 角色与服装核对表','',
         f'核对日期：{args.date}。本表只核对日服已实装、列入学生表的服装，另包含白子 Terror 形态和已有的普拉娜 NPC。“缺项：无”仅针对这个范围，不代表已收录所有剧情、NPC 或场景专用 3D 外观。扩大范围的核查见 [额外外观审计](COSTUME-EXTRAS.md)。',
         '', '名单由本次重新获取的 [SchaleDB 游戏数据](https://schaledb.com/data/en/students.json) 建立，模型与动画逐项对照官方 JP r96 patch 33 资源。SchaleDB 是社区整理数据，不冒称官方公告。',
         '', '| 角色 | 已加入服装／形态 | 缺项 |','| --- | --- | --- |']
for row in rows:
    labels = [installed[p]['name'].split(' · ',1)[-1] for p in row['installed']]
    lines.append(f"| {row['character']} | {'、'.join(labels) or '待适配'} | {'、'.join(row['missing']) or '无'} |")
lines += [f"| 普拉娜 | 原版（NPC） | {'无' if report['planaInstalled'] else '缺少 NPC 包'} |",'',
          '临战星野的攻击型／防御型是同一套衣服；两个预制体使用相同的 CH0258_01_Cafe_Idle、Cafe_Walk 和 Cafe_Reaction。桌宠使用攻击型预制体的原版咖啡厅与提起动作，不重复计数，也不声称提供战斗模式切换。',
          '', '白子 Terror 在游戏中是独立形态，此处单独提供一个角色包。普拉娜不在可招募学生表内，其原版 NPC 模型另行核验。',
          '', f"学生名单与普拉娜共 {len(expected)} 包；另已安装 {len(extras)} 个经核对的剧情／装备／光环外观包。总计 {len(names)+1} 位角色、{len(installed)} 包。学生名单范围缺项：{'、'.join(report['missing']) or '无'}。完整映射与名单摘要校验值见 `test-results/costume-coverage.json`。",
          '', '本表是上述日期和范围内的核对结果，不代表游戏未来不会新增服装，也不能据此排除学生表之外的原版模型。']
if extras:
    lines += ['', '## 已加入的额外外观', '', '| 名称 | 动作说明 |', '| --- | --- |']
    for key,name in extras.items():
        lines.append(f"| {name} | {installed[key].get('note','使用原版动画')} |")
(ROOT/'docs/COSTUMES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['date','expectedPackCount','installedPackCount','missing','unmappedInstalled']},ensure_ascii=False))
