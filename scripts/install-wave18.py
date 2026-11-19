"""Install Wave 18 (4 random students = 8 outfits), Yukino, NP0283, Toki 20-action fix, and 34 Field-Cafe split exploration furniture; update docs/version to 0.2.27."""
from pathlib import Path
import json, shutil

R = Path(__file__).resolve().parents[1]
T = R / 'test-results'
stage = R / '.assets/wave18-final'
read = lambda p: json.loads(p.read_text('utf8'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

specs_all = read(R / 'scripts/roster-wave18-all.json')
specs_w18 = read(R / 'scripts/roster-wave18.json')
selection = read(T / 'wave18-selection.json')
assert len(specs_w18) == 8 and len(selection['selected']) == 4
assert len(specs_all) == 10

# 1. Install 10 new outfits
for key in specs_all:
    dst = R / 'characters' / key
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(stage / key, dst)

# 2. Update toki (5 -> 25 actions) and hina / hina_dress / seia (Field-Cafe furniture)
for key in ['toki', 'hina', 'hina_dress', 'seia']:
    dst = R / 'characters' / key
    shutil.copytree(stage / key, dst, dirs_exist_ok=True)

allcs = {p.parent.name: read(p) for p in (R / 'characters').glob('*/character.json')}
assert len(allcs) == 234, f'Expected 234 outfits, got {len(allcs)}'

en = read(R / '.assets/students-wave16-en.json')
cn = read(R / '.assets/students-wave16-cn.json')
groups = {}
for s in en.values():
    if s['IsReleased'][0]:
        groups.setdefault(s['PersonalName'], []).append(s)
installed = {n for n, students in groups.items() if any(s['PathName'] in allcs for s in students)}
remaining = sorted(set(groups) - installed)
assert installed - set(selection['installedBefore']) == set(selection['selected'])
assert len(installed) == 113 and len(remaining) == 36, (len(installed), len(remaining))

total_actions = sum(len(c['actions']) for c in allcs.values())
total_furniture = sum(len(c.get('furniture', [])) for c in allcs.values())
new_outfit_actions = sum(len(allcs[k]['actions']) for k in specs_all)
toki_added_actions = len(allcs['toki']['actions']) - 5
assert toki_added_actions == 20, toki_added_actions
w18_cafe_furniture = sum(len(allcs[k].get('furniture', [])) for k in specs_w18)
field_cafe_furniture = sum(
    len([f for f in allcs[k].get('furniture', []) if f['id'].startswith('field_')])
    for k in ['hina', 'hina_dress', 'seia', 'np0283']
)
assert field_cafe_furniture == 34, field_cafe_furniture

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
    wave18NewOutfits=len(specs_all),
    wave18NewOutfitActions=new_outfit_actions,
    tokiRestoredActions=toki_added_actions,
    wave18CafeFurniture=w18_cafe_furniture,
    fieldCafeFurniture=field_cafe_furniture,
)
write(T / 'wave18-census.json', census)

# Update docs/ROSTER-COVERAGE.md
lines = [
    f"# 角色加入情况（{selection['date']}）",
    '',
    '按保存的[SchaleDB日服已实装数据](https://schaledb.com/data/en/students.json)的 PersonalName 合并服装与战斗形态；家具搭档不计独立学生。普拉娜（NPC）、雪乃（`CH0171_Enemy`）与妮可 · 探索（`NP0283`）另列。',
    '',
    f"已加入 **{len(installed)}/{len(groups)} 位日服已实装学生**，还未加入 **{len(remaining)} 位**。加上普拉娜、雪乃与妮可 · 探索共 {len(installed)+3} 个角色分组、{len(allcs)} 套外观。",
    '',
    f"本次更新随机新增 4 位日服已实装学生（莲华、真琴、诺亚、日鞠，8 套外观、8 项咖啡厅家具），并额外加入雪乃（`CH0171_Enemy`，23 项原版动作）与妮可 · 探索（`Field_Player_NP0283_NonWeapon`，6 项探索动作 + 6 项 Field_Ex2 拆分家具）；同时为已安装的日奈（原版 7 项、礼服 3 项）与圣娅（18 项）补齐全部 9 套（10 组）探索模式拆分家具与同步时间线（合计 34 项探索拆分家具），并修复时（`toki`）被旧战斗渲染器事件索引拦截的 20 段原版动作（5 -> 25）。抽取种子、候选池及来源哈希见 wave18-selection.json。",
    '',
    '| 角色 | 数据标识 | 已实装外观数 |',
    '| --- | --- | --- |',
]
for r in census['remaining']:
    lines.append(f"| {r['chineseName']} | {r['name']} | {len(r['outfits'])} |")
(R / 'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines) + '\n', 'utf8')

# Update package.json & package-lock.json to 0.2.27
for name in ['package.json', 'package-lock.json']:
    p = R / name
    d = read(p)
    d['version'] = '0.2.27'
    if name == 'package-lock.json':
        d['packages']['']['version'] = '0.2.27'
    else:
        entry = {'from': 'docs/ROSTER-018.md', 'to': 'ROSTER-018.md'}
        if entry not in d['build']['extraFiles']:
            d['build']['extraFiles'].append(entry)
    write(p, d)

body = (
    f"为已安装的日奈（原版：书架 Start/Ing/End、街角猫咪 Start/Ing/End、钢琴 Ing，共 7 项；礼服：宴会餐桌 Start/Ing/End，共 3 项）与圣娅（健身球、麦克风、储物柜、自动贩卖机①、自动贩卖机②、莉音机械犬，各 Start/Ing/End，共 18 项）补齐全部 9 套（10 组）探索模式拆分家具与同步时间线；新增 FOX 小队探索角色妮可 · 探索（`Field_Player_NP0283_NonWeapon`，6 项探索动作 + 街角猫咪／公园长椅 6 项拆分家具）与雪乃（`CH0171_Enemy`，23 项原版战斗／待机动作）；顺手修复时（`toki`）因旧版战斗切换渲染器事件索引（2/3）误截断的 20 段原版动作（5 -> 25，同时修正 `visibility.py` 避免被忽略事件在索引碰撞时关闭光环）。\n\n"
    f"随机新增 4 位未安装学生：莲华、真琴、诺亚、日鞠，共 8 套外观与 8 项咖啡厅家具互动（连同雪乃与妮可 · 探索共新增 10 套外观、{new_outfit_actions} 个新外观动作 + 时补齐 20 个动作、{w18_cafe_furniture} 项咖啡厅家具 + {field_cafe_furniture} 项探索拆分家具）。当前合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具；按保存的日服已实装名单已加入 {len(installed)}/{len(groups)} 位学生，尚余 {len(remaining)} 位，普拉娜、雪乃与妮可 · 探索另列。"
)

table = '| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k, (prefix, label) in specs_all.items():
    table += f"| {label} | {prefix} | {len(allcs[k]['actions'])} | {len(allcs[k].get('furniture', []))} |\n"
table += f"| 日奈 · 原版（补齐探索家具） | Hina_Original | {len(allcs['hina']['actions'])} | {len(allcs['hina'].get('furniture', []))} |\n"
table += f"| 日奈 · 礼服（补齐探索家具） | CH0230 | {len(allcs['hina_dress']['actions'])} | {len(allcs['hina_dress'].get('furniture', []))} |\n"
table += f"| 圣娅 · 原版（补齐探索家具） | CH0070 | {len(allcs['seia']['actions'])} | {len(allcs['seia'].get('furniture', []))} |\n"
table += f"| 时 · 原版（补齐 20 段动作） | CH0187_CafeOnly | {len(allcs['toki']['actions'])} | {len(allcs['toki'].get('furniture', []))} |\n"

roster18 = (
    '# 0.2.27 探索模式拆分家具补齐、雪乃／妮可探索、时动作修复与四位新增学生\n\n'
    + body + '\n\n' + table + '\n'
    '## 来源、修复与适配说明\n\n'
    '- 随机 4 位学生按保存的 SchaleDB 日服已实装学生名单按身份合并服装抽取，种子与候选池见 `test-results/wave18-selection.json`。\n'
    '- 探索模式拆分家具来自官方 `field-cafe-_mxload-prefabs-2025-07-02` / `2026-04-27` 独立预制体与 `field-cafe-_mxdependency-timelines-*` 原版时间线；按原版 `clipIn` 与 `duration` 精确切片，剥离虚拟相机镜头遮罩（`VC_Field_843_Zone01_Mic/FX_DM/Fade*`），并通过 `restore_geometry` 还原纯刚体网格（钢琴、公园长椅）。\n'
    '- 修正 `scripts/visibility.py` 中 `ignored_events` 的判定顺序，确保明确忽略的旧版战斗渲染器事件即使索引与光环节点重合也不会错误关闭光环；由此安全恢复 `toki` 全部 20 段原版动作（总计 25 段，0 遗漏）。\n'
    '- 修正日鞠原版（`CH0159`）渲染器事件索引映射（`3 -> CH0159_Blanket_Mesh`），避免编队提起时误隐光环而非腿毯；处理真琴泳装（`CH0344`）4×4 口型图集负偏移默认值与 `Clamp` 采样兼容，还原全部口型切换事件。\n'
    '- 补齐 8 项咖啡厅家具原版特效（含莲华古风料理台角色内嵌表情粒子）；10 套新外观与全部 20 组新家具均通过 90,472 条原版骨骼通道一致性校验与四向实机截图复核，并配置正面默认视角。\n'
    '- 本版默认仅交付可运行文件夹（`release/v0.2.27/win-unpacked/BA Desktop Pet.exe`），不创建 ZIP 压缩包。\n'
)
(R / 'docs/ROSTER-018.md').write_text(roster18, 'utf8')

def prepend(rel, title, text):
    p = R / rel
    s = p.read_text('utf8')
    if title not in s:
        p.write_text(title + '\n\n' + text + '\n\n' + s, 'utf8')

prepend('README.md', '## 0.2.27 探索模式拆分家具补齐、雪乃／妮可探索、时动作修复与四位新增学生', body + '\n\n[详细来源与验收](docs/ROSTER-018.md) · [未加入名单](docs/ROSTER-COVERAGE.md)')
readme = (R / 'README.md').read_text('utf8')
if '当前版本：' in readme:
    start = readme.index('当前版本：')
    end = readme.index('\n\n', start)
    readme = (
        readme[:start]
        + f"当前版本：**0.2.27**。合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具。补齐日奈（原版／礼服）与圣娅全部 9 套（10 组、28 项）探索拆分家具，新增雪乃、妮可 · 探索（含 6 项探索家具）及 4 位随机学生（莲华、真琴、诺亚、日鞠，8 套外观与 8 项家具），并修复时（`toki`）全部 20 段原版动作。详见[ROSTER-018](docs/ROSTER-018.md)。"
        + readme[end:]
    )
readme = readme.replace('`release/v0.2.26/win-unpacked/BA Desktop Pet.exe`', '`release/v0.2.27/win-unpacked/BA Desktop Pet.exe`')
readme = readme.replace('`release/v0.2.25/win-unpacked/BA Desktop Pet.exe`', '`release/v0.2.27/win-unpacked/BA Desktop Pet.exe`')
(R / 'README.md').write_text(readme, 'utf8')

prepend('docs/COSTUMES.md', '## 0.2.27 新增十套外观与探索／动作补齐', table)
prepend('docs/FURNITURE.md', '## 0.2.27 探索拆分家具与新家具增量', f"新增 {w18_cafe_furniture} 项咖啡厅家具（莲华、真琴、诺亚、日鞠及其换装）与 {field_cafe_furniture} 项探索模式拆分家具（日奈书架／猫咪／钢琴、日奈礼服宴会桌、圣娅健身球／麦克风／储物柜／双版本贩卖机／莉音机械犬、妮可探索猫咪／长椅）。详见[ROSTER-018](ROSTER-018.md)。")
prepend('docs/ASSETS.md', '## 0.2.27 探索家具、雪乃／妮可探索与四位新学生', '原始官方 JP r96 模型、贴图、骨骼动画、探索家具预制体与时间线按需提取并 CRC 校验，详见[ROSTER-018](ROSTER-018.md)。')
prepend('docs/RANDOM-ROSTER.md', '## 0.2.27 随机四位与探索／雪乃补齐', body)

print(json.dumps({k: v for k, v in census.items() if k not in ['sources', 'installed', 'remaining']}, ensure_ascii=False, indent=2))
