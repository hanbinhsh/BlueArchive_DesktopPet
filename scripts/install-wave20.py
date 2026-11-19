"""Install 10 random Wave 20 students (21 outfits) and update docs/version to 0.2.29."""
from pathlib import Path
import json, math, shutil

R = Path(__file__).resolve().parents[1]
T = R / 'test-results'
stage = R / '.assets/wave20-final'
read = lambda p: json.loads(p.read_text('utf8'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

# Update tsukuyo_dress f210389_0 viewYaw to pi (unobstructed curved sliding curtain front)
td_path = stage / 'tsukuyo_dress/character.json'
td = read(td_path)
for f in td.get('furniture', []):
    if f['id'] == 'f210389_0':
        f['viewYaw'] = round(math.pi, 6)
write(td_path, td)
yaw_path = R / 'scripts/furniture-character-view-yaw.json'
yaw_map = read(yaw_path)
yaw_map.setdefault('tsukuyo_dress', {})['f210389_0'] = round(math.pi, 6)
write(yaw_path, dict(sorted(yaw_map.items())))

specs = read(R / 'scripts/roster-wave20.json')
selection = read(T / 'wave20-selection.json')
assert len(specs) == 21 and len(selection['selected']) == 10

for key in specs:
    dst = R / 'characters' / key
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(stage / key, dst)

allcs = {p.parent.name: read(p) for p in (R / 'characters').glob('*/character.json')}
assert len(allcs) == 281, f'Expected 281 outfits, got {len(allcs)}'

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
assert len(installed) == 140 and len(remaining) == 9, (len(installed), len(remaining))

total_actions = sum(len(c['actions']) for c in allcs.values())
total_furniture = sum(len(c.get('furniture', [])) for c in allcs.values())
wave20_actions = sum(len(allcs[k]['actions']) for k in specs)
wave20_furniture = sum(len(allcs[k].get('furniture', [])) for k in specs)

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
    wave20Outfits=len(specs),
    wave20Actions=wave20_actions,
    wave20Furniture=wave20_furniture,
)
write(T / 'wave20-census.json', census)

cn_names = '、'.join(c['chineseName'] for c in selection['characters'])

# Update docs/ROSTER-COVERAGE.md
lines = [
    f"# 角色加入情况（{selection['date']}）",
    '',
    '按保存的[SchaleDB日服已实装数据](https://schaledb.com/data/en/students.json)的 PersonalName 合并服装与战斗形态（已按原始模型前缀排除已以 `shun_swimsuit_small` 安装的 `Shunling` 重复项）；家具搭档不计独立学生。普拉娜（NPC）、雪乃（`CH0171_Enemy`）与妮可 · 探索（`NP0283`）另列。',
    '',
    f"已加入 **{len(installed)}/{len(groups)} 位日服已实装学生**，还未加入 **{len(remaining)} 位**。加上普拉娜、雪乃与妮可 · 探索共 {len(installed)+3} 个角色分组、{len(allcs)} 套外观。",
    '',
    f"本次随机新增 10 位学生（{cn_names}），共 {len(specs)} 套已实装外观、{wave20_actions} 个普通动作、{wave20_furniture} 项家具互动。抽取种子、候选池及来源哈希见 wave20-selection.json。",
    '',
    '| 角色 | 数据标识 | 已实装外观数 |',
    '| --- | --- | --- |',
]
for r in census['remaining']:
    lines.append(f"| {r['chineseName']} | {r['name']} | {len(r['outfits'])} |")
(R / 'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines) + '\n', 'utf8')

# Update package.json & package-lock.json to 0.2.29
for name in ['package.json', 'package-lock.json']:
    p = R / name
    d = read(p)
    d['version'] = '0.2.29'
    if name == 'package-lock.json':
        d['packages']['']['version'] = '0.2.29'
    else:
        entry = {'from': 'docs/ROSTER-020.md', 'to': 'ROSTER-020.md'}
        if entry not in d['build']['extraFiles']:
            d['build']['extraFiles'].append(entry)
    write(p, d)

body = (
    f"修复花江圣诞壁炉兔子／礼盒穿模掉出底部问题、修复惠的浴缸两只橡皮鸭水波缺失与随鸭子倾斜问题（并顺手补齐 4 件同类常驻家具粒子特效），同时随机新增 10 位未安装学生：{cn_names}，共 {len(specs)} 套外观、{wave20_actions} 个普通动作及 {wave20_furniture} 项咖啡厅家具互动（含心／琴音单人与双人潜水池、纱织泳装 DJ 表演主舞台、美咲泳装海滩躺椅和小桌子、月咏龟背竹白色花盆与礼服简易更衣室等）。当前合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具；按保存的日服已实装名单已加入 {len(installed)}/{len(groups)} 位学生，仅余 {len(remaining)} 位，普拉娜、雪乃与妮可 · 探索另列。"
)

table = '| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k, (prefix, label) in specs.items():
    table += f"| {label} | {prefix} | {len(allcs[k]['actions'])} | {len(allcs[k].get('furniture', []))} |\n"

roster20 = (
    '# 0.2.29 家具穿模与水波修复 + 随机新增十位学生\n\n'
    + body + '\n\n' + table + '\n'
    '## 缺陷修复与同类排查\n\n'
    '- **花江 · 圣诞 圣诞壁炉（`hanae_christmas/f207308_0`）**：原版动画在装盒与装袋结束阶段会将兔子与三只礼盒下移至地面 `Y < 0` 下方隐藏，在无地面遮挡的桌宠窗口中表现为穿过盒子与圣诞袋底部掉落；现为道具材质与独立克隆礼盒材质补齐 `BA_liquidReceiver` 地面裁切（含描边同步裁切）并钳制负缩放超调，同时补齐炉内常驻火焰粒子 `FX_my_event13_fireplace_FireLoop`。\n'
    '- **惠 温泉柏木浴缸（`megu/f6301_0`）**：为 `Duck01` 补齐原本常驻在预制体下、未挂入时间线控制轨的水平水波粒子 `FX_my_hotsprings_woodenbathtub_duck_01_Bubble` 并固定发射高度至水面；修正 `src/cafe-particles.ts` 中 `m_RenderAlignment === 1`（World）粒子在跟随父骨骼旋转或桌宠旋转时的姿态计算，使其始终平行于水面；同时为 `Duck02` 静态水波网格烘焙反旋转与水面高度，使两只鸭子下方的水波均严格与水面平行。\n'
    '- **同类常驻家具粒子与渲染事件排查**：排查并补齐 `kanna/f207313_0` 咖啡热气（`FX_my_event15_table_Smoke_01`）、`pina_guide/f210368_0` 电视光效（`FX_my_event078_videotelevision_TV_Loop_1`）与本批 `akari_newyear/f210334_0` 水桶水花（`FX_my_event065_ricecakemakingset_Water_Loop`）；修正 `tsukuyo`／`tsukuyo_dress` 渲染器事件索引映射；修正 `saori_dress` 在咖啡厅待机与豪华全身镜中隐藏战斗专用副武器（`Saori_Original_Handgun`／`CH0259_HandGrenade_Mesh`）以与 `CH0259_CafeOnly` 一致。\n'
    '- **随机十位新学生**：种子与候选池见 `test-results/wave20-selection.json`；全部 21 套新外观与 18 项新家具（含补齐 `misaki_swimsuit` 实际互动预制体 `my_event083_beachsunbed`）均通过骨骼通道一致性校验与四向实机截图复核。\n'
    '- 本版默认仅交付可运行文件夹（`release/v0.2.29/win-unpacked/BA Desktop Pet.exe`），不创建 ZIP 压缩包。\n'
)
(R / 'docs/ROSTER-020.md').write_text(roster20, 'utf8')

def prepend(rel, title, text):
    p = R / rel
    s = p.read_text('utf8')
    if title not in s:
        p.write_text(title + '\n\n' + text + '\n\n' + s, 'utf8')

prepend('README.md', '## 0.2.29 家具修复与随机新增十位学生', body + '\n\n[详细来源与验收](docs/ROSTER-020.md) · [未加入名单](docs/ROSTER-COVERAGE.md)')
readme = (R / 'README.md').read_text('utf8')
if '当前版本：' in readme:
    start = readme.index('当前版本：')
    end = readme.index('\n\n', start)
    readme = (
        readme[:start]
        + f"当前版本：**0.2.29**。合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具。修复圣诞壁炉与浴缸水波问题，并随机新增 10 位学生（21 套外观、{wave20_actions} 个动作、{wave20_furniture} 项家具）。详见[ROSTER-020](docs/ROSTER-020.md)。"
        + readme[end:]
    )
readme = readme.replace('`release/v0.2.28/win-unpacked/BA Desktop Pet.exe`', '`release/v0.2.29/win-unpacked/BA Desktop Pet.exe`')
(R / 'README.md').write_text(readme, 'utf8')

prepend('docs/COSTUMES.md', '## 0.2.29 新增十位学生二十一套外观', table)
prepend('docs/FURNITURE.md', '## 0.2.29 家具修复与十位新学生家具增量', f"修复花江圣诞壁炉道具穿模与惠的浴缸双鸭水平水波，补齐多件常驻家具粒子，并新增 {wave20_furniture} 项咖啡厅家具互动（含心／琴音双人潜水池、纱织泳装 DJ 舞台、美咲泳装海滩躺椅等）。详见[ROSTER-020](docs/ROSTER-020.md)。")
prepend('docs/ASSETS.md', '## 0.2.29 十位新学生', '原始官方 JP r96 模型、贴图、骨骼动画与家具时间线按需提取并 CRC 校验，详见[ROSTER-020](docs/ROSTER-020.md)。')
prepend('docs/RANDOM-ROSTER.md', '## 0.2.29 随机十位', body)

print(json.dumps({k: v for k, v in census.items() if k not in ['sources', 'installed', 'remaining']}, ensure_ascii=False, indent=2))
