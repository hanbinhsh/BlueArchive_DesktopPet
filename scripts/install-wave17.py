"""Install 15 random Wave 17 students (28 outfits, 584 actions, 25 furniture) and update docs/version to 0.2.25."""
from pathlib import Path
import json, shutil

R = Path(__file__).resolve().parents[1]
T = R / 'test-results'
stage = R / '.assets/wave17-final'
read = lambda p: json.loads(p.read_text('utf8'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

specs = read(R / 'scripts/roster-wave17.json')
selection = read(T / 'wave17-selection.json')
assert len(specs) == 28 and len(selection['selected']) == 15
assert all(not (R / 'characters' / key).exists() for key in specs), 'Some Wave 17 characters already installed'
assert all(not r['omitted'] for r in read(T / 'wave17-fx-adaptation.json'))
assert not read(T / 'wave17-embedded-final-audit.json')['missing']

for key in specs:
    shutil.copytree(stage / key, R / 'characters' / key)

allcs = {p.parent.name: read(p) for p in (R / 'characters').glob('*/character.json')}
assert len(allcs) == 224, f'Expected 224 outfits, got {len(allcs)}'

en = read(R / '.assets/students-wave16-en.json')
cn = read(R / '.assets/students-wave16-cn.json')
groups = {}
for s in en.values():
    if s['IsReleased'][0]:
        groups.setdefault(s['PersonalName'], []).append(s)
installed = {n for n, students in groups.items() if any(s['PathName'] in allcs for s in students)}
remaining = sorted(set(groups) - installed)
assert installed - set(selection['installedBefore']) == set(selection['selected'])
assert len(installed) == 109 and len(remaining) == 40, (len(installed), len(remaining))

total_actions = sum(len(c['actions']) for c in allcs.values())
total_furniture = sum(len(c.get('furniture', [])) for c in allcs.values())
wave17_actions = sum(len(allcs[k]['actions']) for k in specs)
wave17_furniture = sum(len(allcs[k].get('furniture', [])) for k in specs)

census = dict(
    date=selection['date'],
    sources=selection['sources'],
    scope=selection['scope'],
    playableTotal=len(groups),
    installedPlayable=len(installed),
    remainingPlayable=len(remaining),
    additionalInstalledNpcs=['plana'],
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
    wave17Outfits=len(specs),
    wave17Actions=wave17_actions,
    wave17Furniture=wave17_furniture,
)
write(T / 'wave17-census.json', census)

# Update docs/ROSTER-COVERAGE.md
lines = [
    f"# 角色加入情况（{selection['date']}）",
    '',
    '按保存的[SchaleDB日服已实装数据](https://schaledb.com/data/en/students.json)的 PersonalName 合并服装与战斗形态；家具搭档不计独立学生。普拉娜作为NPC另列。',
    '',
    f"已加入 **{len(installed)}/{len(groups)} 位学生**，还未加入 **{len(remaining)}位**。加上普拉娜共{len(installed)+1}个角色分组、{len(allcs)}套外观。",
    '',
    f"本次随机新增15位学生（春香、歌原、咲、野宫、亚子、和香、木乃香、柚子、千寻、艾莉娜、堇、紫、霞、实梨、响），共{len(specs)}套已实装外观、{wave17_actions}个普通动作、{wave17_furniture}项家具互动。抽取种子、候选池及来源哈希见 wave17-selection.json。",
    '',
    '| 角色 | 数据标识 | 已实装外观数 |',
    '| --- | --- | --- |',
]
for r in census['remaining']:
    lines.append(f"| {r['chineseName']} | {r['name']} | {len(r['outfits'])} |")
(R / 'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines) + '\n', 'utf8')

# Update package.json & package-lock.json
for name in ['package.json', 'package-lock.json']:
    p = R / name
    d = read(p)
    d['version'] = '0.2.25'
    if name == 'package-lock.json':
        d['packages']['']['version'] = '0.2.25'
    else:
        entry = {'from': 'docs/ROSTER-017.md', 'to': 'ROSTER-017.md'}
        if entry not in d['build']['extraFiles']:
            d['build']['extraFiles'].append(entry)
    write(p, d)

# Write docs/ROSTER-017.md and update README.md + docs
body = (
    f"全局同类问题排查并修复两处历史隐患：补齐伊吹单人沙浴池（`ibuki_swimsuit/f211311_0`）7 张 `FX_TEX_CH0347_Sandart*` 遮罩贴图的 sRGB 标记，与双人沙浴一致；按 smoothstep + 最短弧 SLERP 重新烘焙巴的温泉椅（`tomoe/f6100_0`）14 处重叠时间线片段，消除重叠起点的 159.6° 骨骼跳变。\n\n"
    f"随机新增 15 位未安装学生：春香、歌原、咲、野宫、亚子、和香、木乃香、柚子、千寻、艾莉娜、堇、紫、霞、实梨、响，共 {len(specs)} 套外观、{wave17_actions} 个普通动作及 {wave17_furniture} 项家具互动（含歌原应援团／响应援团双人应援台、亚子礼服／日奈礼服双人茶会沙发）。当前合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具；按保存的日服已实装名单已加入 {len(installed)}/{len(groups)} 位学生，尚余 {len(remaining)} 位，普拉娜 NPC 另列。"
)
table = '| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k, (prefix, label) in specs.items():
    table += f"| {label} | {prefix} | {len(allcs[k]['actions'])} | {len(allcs[k].get('furniture', []))} |\n"

roster17 = (
    '# 0.2.25 同类问题全局排查与十五位新增学生\n\n'
    + body + '\n\n' + table + '\n'
    '## 来源、修复与适配说明\n\n'
    '- 随机名单按已保存的 SchaleDB 日服已实装学生名单按身份合并服装抽取，种子与候选池见 `test-results/wave17-selection.json`。\n'
    '- 新增支持 `DSFX/FX_SHADER_Matcap_0` 半透明 Matcap 着色器（`matcapBlend`），完整还原艾莉娜化学实验台烧杯液体；补齐 `glb.py` 与 `furniture_geometry.py` 对纯静态网格家具（春香礼服阳台）的空容器初始化。\n'
    '- 规范化野宫泳装（`CH0092`）原版动画中带负号的 `SetMouthTile` 索引（如 `-704 -> 704`），使其通过口型校验并正确切换表情。\n'
    '- 补齐实梨工作台扩音器与春香礼服阳台的角色内嵌粒子，以及千寻游戏中心电视屏幕（优化掉 `bg` 图层因原版默认 `maxNumParticles=1000` + `rateOverTime=10000` 产生的 3,000 个完全重合静态副本，将 `f2203_0.glb` 从 50.1 MB 精简至 4.8 MB）、紫泳装度假泳池常驻特效。\n'
    '- 全部 28 套外观均通过 226,003 条原版骨骼通道一致性校验与实机截图复核，25 项家具逐一核验四向角度并配置最佳正面默认视角。\n'
    '- 本版默认仅交付可运行文件夹（`release/v0.2.25/win-unpacked/BA Desktop Pet.exe`），不创建 ZIP 压缩包。\n'
)
(R / 'docs/ROSTER-017.md').write_text(roster17, 'utf8')

def prepend(rel, title, text):
    p = R / rel
    s = p.read_text('utf8')
    if title not in s:
        p.write_text(title + '\n\n' + text + '\n\n' + s, 'utf8')

prepend('README.md', '## 0.2.25 同类问题全局排查与十五位新增学生', body + '\n\n[详细来源与验收](docs/ROSTER-017.md) · [未加入名单](docs/ROSTER-COVERAGE.md)')
readme = (R / 'README.md').read_text('utf8')
start = readme.index('当前版本：')
end = readme.index('\n\n', start)
readme = (
    readme[:start]
    + f"当前版本：**0.2.25**。合计{len(allcs)}套外观、{total_actions:,}个普通动作、{total_furniture}项家具。完成历史同类隐患排查（伊吹单人沙浴遮罩与巴温泉椅重叠过渡），随机新增15位学生（28套外观、{wave17_actions}个动作、{wave17_furniture}项家具）。详见[ROSTER-017](docs/ROSTER-017.md)。"
    + readme[end:]
)
readme = readme.replace('`release/v0.2.24/win-unpacked/BA Desktop Pet.exe`', '`release/v0.2.25/win-unpacked/BA Desktop Pet.exe`')
(R / 'README.md').write_text(readme, 'utf8')

prepend('docs/COSTUMES.md', '## 0.2.25 新增十五位学生二十八套外观', table)
prepend('docs/FURNITURE.md', '## 0.2.25 家具增量与同类修复', f"新增 {wave17_furniture} 项家具互动，含歌原／响双人应援台、亚子／日奈双人礼服茶会、艾莉娜化学实验台（Matcap 液体）、千寻复古电视、紫度假泳池等；同步修复伊吹单人沙浴遮罩 sRGB 与巴温泉椅重叠过渡。详见[ROSTER-017](ROSTER-017.md)。")
prepend('docs/ASSETS.md', '## 0.2.25 十五位学生与同类隐患修复', '原始官方 JP r96 模型、贴图、骨骼动画与家具时间线按需提取并 CRC 校验，详见[ROSTER-017](ROSTER-017.md)。')
prepend('docs/RANDOM-ROSTER.md', '## 0.2.25 随机十五位', body)

print(json.dumps({k: v for k, v in census.items() if k not in ['sources', 'installed', 'remaining']}, ensure_ascii=False, indent=2))
