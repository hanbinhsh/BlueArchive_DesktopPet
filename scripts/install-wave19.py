"""Install 16 random Wave 19 students (26 outfits) and update docs/version to 0.2.28."""
from pathlib import Path
import json, shutil

R = Path(__file__).resolve().parents[1]
T = R / 'test-results'
stage = R / '.assets/wave19-final'
read = lambda p: json.loads(p.read_text('utf8'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

specs = read(R / 'scripts/roster-wave19.json')
selection = read(T / 'wave19-selection.json')
assert len(specs) == 26 and len(selection['selected']) == 16

for key in specs:
    dst = R / 'characters' / key
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(stage / key, dst)

allcs = {p.parent.name: read(p) for p in (R / 'characters').glob('*/character.json')}
assert len(allcs) == 260, f'Expected 260 outfits, got {len(allcs)}'

en = read(R / '.assets/students-wave16-en.json')
cn = read(R / '.assets/students-wave16-cn.json')
groups = {}
for s in en.values():
    if s['IsReleased'][0]:
        groups.setdefault(s['PersonalName'], []).append(s)

installed_descs = {k: v['source']['description'] for k, v in allcs.items()}
installed = {
    s['PersonalName'] for values in groups.values() for s in values
    if s['PathName'] in allcs or any(
        f" {s['DevName']};" in d or f" {s['DevName']}_Original;" in d for d in installed_descs.values()
    )
}
remaining = sorted(set(groups) - installed)
assert installed - set(selection['installedBefore']) == set(selection['selected'])
assert len(installed) == 130 and len(remaining) == 19, (len(installed), len(remaining))

total_actions = sum(len(c['actions']) for c in allcs.values())
total_furniture = sum(len(c.get('furniture', [])) for c in allcs.values())
wave19_actions = sum(len(allcs[k]['actions']) for k in specs)
wave19_furniture = sum(len(allcs[k].get('furniture', [])) for k in specs)

census = dict(
    date=selection['date'],
    sources=selection['sources'],
    scope=selection['scope'],
    playableTotal=len(groups),
    installedPlayable=len(installed),
    remainingPlayable=len(remaining),
    additionalInstalledSpecial=['plana', 'yukino', 'np0283'],
    installed=sorted(installed),
    remaining=[
        dict(
            name=n,
            chineseName=cn[str(groups[n][0]['Id'])]['Name'],
            outfits=[dict(id=s['Id'], path=s['PathName'], name=cn[str(s['Id'])]['Name']) for s in groups[n]],
        )
        for n in remaining
    ],
    outfits=len(allcs),
    actions=total_actions,
    furniture=total_furniture,
    wave19Outfits=len(specs),
    wave19Actions=wave19_actions,
    wave19Furniture=wave19_furniture,
)
write(T / 'wave19-census.json', census)

cn_names = '、'.join(c['chineseName'] for c in selection['characters'])

# Update docs/ROSTER-COVERAGE.md
lines = [
    f"# 角色加入情况（{selection['date']}）",
    '',
    '按保存的[SchaleDB日服已实装数据](https://schaledb.com/data/en/students.json)的 PersonalName 合并服装与战斗形态（已按原始模型前缀排除已以 `shun_swimsuit_small` 安装的 `Shunling` 重复项）；家具搭档不计独立学生。普拉娜（NPC）、雪乃（`CH0171_Enemy`）与妮可 · 探索（`NP0283`）另列。',
    '',
    f"已加入 **{len(installed)}/{len(groups)} 位日服已实装学生**，还未加入 **{len(remaining)} 位**。加上普拉娜、雪乃与妮可 · 探索共 {len(installed)+3} 个角色分组、{len(allcs)} 套外观。",
    '',
    f"本次随机新增 16 位学生（{cn_names}），共 {len(specs)} 套已实装外观、{wave19_actions} 个普通动作、{wave19_furniture} 项家具互动。抽取种子、候选池及来源哈希见 wave19-selection.json。",
    '',
    '| 角色 | 数据标识 | 已实装外观数 |',
    '| --- | --- | --- |',
]
for r in census['remaining']:
    lines.append(f"| {r['chineseName']} | {r['name']} | {len(r['outfits'])} |")
(R / 'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines) + '\n', 'utf8')

# Update package.json & package-lock.json to 0.2.28
for name in ['package.json', 'package-lock.json']:
    p = R / name
    d = read(p)
    d['version'] = '0.2.28'
    if name == 'package-lock.json':
        d['packages']['']['version'] = '0.2.28'
    else:
        entry = {'from': 'docs/ROSTER-019.md', 'to': 'ROSTER-019.md'}
        if entry not in d['build']['extraFiles']:
            d['build']['extraFiles'].append(entry)
    write(p, d)

body = (
    f"随机新增 16 位未安装学生：{cn_names}，共 {len(specs)} 套外观、{wave19_actions} 个普通动作及 {wave19_furniture} 项咖啡厅家具互动（含晴奈新年／淳子新年双人新年美食套装桌、惠温泉柏木浴缸、明日奈兔女郎银蓝吧台椅与制服千禧年书桌、妮可作战桌等）。当前合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具；按保存的日服已实装名单已加入 {len(installed)}/{len(groups)} 位学生，尚余 {len(remaining)} 位，普拉娜、雪乃与妮可 · 探索另列。"
)

table = '| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k, (prefix, label) in specs.items():
    table += f"| {label} | {prefix} | {len(allcs[k]['actions'])} | {len(allcs[k].get('furniture', []))} |\n"

roster19 = (
    '# 0.2.28 随机新增十六位学生\n\n'
    + body + '\n\n' + table + '\n'
    '## 来源、修复与适配说明\n\n'
    '- 随机 16 位学生按保存的 SchaleDB 日服已实装学生名单按身份合并服装抽取（已排除已由 `shun_swimsuit_small` 覆盖的 `CH0355_02` 重复项），种子与候选池见 `test-results/wave19-selection.json`。\n'
    '- 修正惠（`CH0088`）渲染器事件索引映射（`2 -> CH0088_Weapon`），避免咖啡厅待机／互动误隐光环而非火焰喷射器；修正妮可（`CH0172`）咖啡厅专用子网格事件映射（`4/5/6 -> CH0172_Hand01_Mesh / CH0172_Hand02_Mesh / my_event091_strategytable_prop_02`），防止光环被错误关闭。\n'
    '- 全部 26 套新外观均通过原版骨骼通道一致性校验与实机截图复核；全部 21 项新咖啡厅家具均补齐原版特效（含外置粒子与角色内嵌粒子），经四向实机截图人工复核并配置正面默认视角。\n'
    '- 本版默认仅交付可运行文件夹（`release/v0.2.28/win-unpacked/BA Desktop Pet.exe`），不创建 ZIP 压缩包。\n'
)
(R / 'docs/ROSTER-019.md').write_text(roster19, 'utf8')

def prepend(rel, title, text):
    p = R / rel
    s = p.read_text('utf8')
    if title not in s:
        p.write_text(title + '\n\n' + text + '\n\n' + s, 'utf8')

prepend('README.md', '## 0.2.28 随机新增十六位学生', body + '\n\n[详细来源与验收](docs/ROSTER-019.md) · [未加入名单](docs/ROSTER-COVERAGE.md)')
readme = (R / 'README.md').read_text('utf8')
if '当前版本：' in readme:
    start = readme.index('当前版本：')
    end = readme.index('\n\n', start)
    readme = (
        readme[:start]
        + f"当前版本：**0.2.28**。合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具。随机新增 16 位学生（26 套外观、{wave19_actions} 个动作、{wave19_furniture} 项家具）。详见[ROSTER-019](docs/ROSTER-019.md)。"
        + readme[end:]
    )
readme = readme.replace('`release/v0.2.27/win-unpacked/BA Desktop Pet.exe`', '`release/v0.2.28/win-unpacked/BA Desktop Pet.exe`')
(R / 'README.md').write_text(readme, 'utf8')

prepend('docs/COSTUMES.md', '## 0.2.28 新增十六位学生二十六套外观', table)
prepend('docs/FURNITURE.md', '## 0.2.28 十六位新学生家具增量', f"新增 {wave19_furniture} 项咖啡厅家具互动（含晴奈新年／淳子新年双人新年美食套装桌、惠温泉柏木浴缸、明日奈兔女郎吧台椅、妮可作战桌、绘梨香饰品展示架等）。详见[ROSTER-019](docs/ROSTER-019.md)。")
prepend('docs/ASSETS.md', '## 0.2.28 十六位新学生', '原始官方 JP r96 模型、贴图、骨骼动画与家具时间线按需提取并 CRC 校验，详见[ROSTER-019](docs/ROSTER-019.md)。')
prepend('docs/RANDOM-ROSTER.md', '## 0.2.28 随机十六位', body)

print(json.dumps({k: v for k, v in census.items() if k not in ['sources', 'installed', 'remaining']}, ensure_ascii=False, indent=2))
