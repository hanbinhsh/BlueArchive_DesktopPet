"""Install Wave 21 (8 remaining 3D playable JP students + momoi_battle & midori_battle = 16 outfits) and update docs/version to 0.2.30."""
from pathlib import Path
import json, shutil

R = Path(__file__).resolve().parents[1]
T = R / 'test-results'
stage = R / '.assets/wave21-final'
read = lambda p: json.loads(p.read_text('utf8'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', 'utf8')

specs = read(R / 'scripts/roster-wave21.json')
assert len(specs) == 16, f'Expected 16 Wave 21 outfits, got {len(specs)}'

for key in specs:
    dst = R / 'characters' / key
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(stage / key, dst)

allcs = {p.parent.name: read(p) for p in (R / 'characters').glob('*/character.json')}
assert len(allcs) == 297, f'Expected 297 outfits, got {len(allcs)}'

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
assert len(installed) == 148 and len(remaining) == 1, (len(installed), len(remaining), remaining)

total_actions = sum(len(c['actions']) for c in allcs.values())
total_furniture = sum(len(c.get('furniture', [])) for c in allcs.values())
wave21_actions = sum(len(allcs[k]['actions']) for k in specs)
wave21_furniture = sum(len(allcs[k].get('furniture', [])) for k in specs)

census = dict(
    date='2026-11-19',
    playableTotal=len(groups),
    installedPlayable=len(installed),
    remainingPlayable=len(remaining),
    remainingNote='Rana (CH0322) has only 2D Spine assets (ch0322_spr) and no 3D character model in JP r96.',
    additionalInstalledSpecial=['plana', 'yukino', 'np0283', 'momoi_battle', 'midori_battle'],
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
    wave21Outfits=len(specs),
    wave21Actions=wave21_actions,
    wave21Furniture=wave21_furniture,
)
write(T / 'wave21-census.json', census)

cn_names = '切里诺、吹雪、玛丽娜、满、名草、玲纱（礼服／玲女）、樱子、高音、桃井 · 临战、绿 · 临战'
cn_names = '切里诺、吹雪、玛丽娜、满、名草、玲女、樱子、高音、桃井 · 临战、绿 · 临战'

# Update docs/ROSTER-COVERAGE.md
lines = [
    '# 角色加入情况（2026-11-19）',
    '',
    '按保存的[SchaleDB日服已实装数据](https://schaledb.com/data/en/students.json)的 PersonalName 合并服装与战斗形态（已按原始模型前缀排除已以 `shun_swimsuit_small` 安装的 `Shunling` 重复项）；家具搭档不计独立学生。普拉娜（NPC）、雪乃（`CH0171_Enemy`）、妮可 · 探索（`NP0283`）、桃井 · 临战（`NP0267`）与绿 · 临战（`NP0268`）另列。',
    '',
    f"已加入 **{len(installed)}/{len(groups)} 位日服已实装学生**（当前 JP r96 客户端中拥有 3D 模型的已实装学生已 **100% 全部收录**），仅余 **{len(remaining)} 位**（拉娜 `CH0322` 在 JP r96 中仅含 2D Spine 立绘 `ch0322_spr`，尚无 3D 模型）。加上普拉娜、雪乃、妮可 · 探索以及桃井 · 临战、绿 · 临战共 {len(installed)+5} 个角色分组、{len(allcs)} 套外观。",
    '',
    f"本次新增 10 组角色（8 位剩余拥有 3D 模型的日服已实装学生：切里诺、吹雪、玛丽娜、满、名草、玲女、樱子、高音，外加千禧年临战双子：桃井 · 临战、绿 · 临战），共 {len(specs)} 套外观、{wave21_actions} 个普通动作、{wave21_furniture} 项家具互动。",
    '',
    '| 角色 | 数据标识 | 已实装外观数 | 备注 |',
    '| --- | --- | --- | --- |',
]
for r in census['remaining']:
    lines.append(f"| {r['chineseName']} | {r['name']} | {len(r['outfits'])} | JP r96 仅含 2D Spine，尚无 3D 模型 |")
(R / 'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines) + '\n', 'utf8')

# Update package.json & package-lock.json to 0.2.30
for name in ['package.json', 'package-lock.json']:
    p = R / name
    d = read(p)
    d['version'] = '0.2.30'
    if name == 'package-lock.json':
        d['packages']['']['version'] = '0.2.30'
    else:
        entry = {'from': 'docs/ROSTER-021.md', 'to': 'ROSTER-021.md'}
        if entry not in d['build']['extraFiles']:
            d['build']['extraFiles'].append(entry)
    write(p, d)

body = (
    f"集中修复六大类家具渲染、特效、镜面与视角问题，同时新增 10 位角色（{cn_names}），共 {len(specs)} 套外观、{wave21_actions} 个普通动作及 {wave21_furniture} 项咖啡厅家具互动（含偶像樱子三人／单人舞台、高音同人摊位、满忍术灯笼与礼服拉面桌、名草枪架与泳装饮料冰柜、吹雪甜甜圈长椅与泳装浮圈、玛丽娜旗袍／玲女木人桩等）。当前合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具；日服已实装且拥有 3D 模型的学生已达 {len(installed)}/{len(groups)}（仅拉娜 `CH0322` 在 JP r96 尚无 3D 模型），另含普拉娜、雪乃、妮可 · 探索、桃井 · 临战与绿 · 临战。"
)

table = '| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k, (prefix, label) in specs.items():
    table += f"| {label} | {prefix} | {len(allcs[k]['actions'])} | {len(allcs[k].get('furniture', []))} |\n"

roster21 = (
    '# 0.2.30 六项家具特效／镜面／视口裁切／视角修复 + 新增十位角色\n\n'
    + body + '\n\n' + table + '\n'
    '## 缺陷修复与同类排查\n\n'
    '- **美咲／纱织 落地窗（`my_cafe_01_b_wall_04`，`f1108_0`／`f1108_1`）**：从补丁包提取并挂回 `FX_My_Cafe_Wall_01` 窗外夜雨与玻璃暗蓝背景特效，将原本不透明发黄的射灯光锥 `FX_MAT_Wall_Stretch_Line_01` 改为柔和透明光束；同时补齐原版双人互动 **纱织 & 美咲（`MakeTrack_10041_10048`，`f1108_1`）**，两位角色入口均可直接切换单人／双人落地窗。\n'
    '- **心／琴音 潜水池（`f211314_0/1`）与桐乃 射击场（`f211304_0`）视口模板裁切**：在 `src/scene-view.ts` 与 `src/model-outline.ts` 新增 `BA_stencil` `equal` 模式与 `BA_clipStencil` 粒子／描边同步裁切，将全部 10 份同类开窗模板家具的内部通道与粒子严格限制在窗框内部，且潜水池改为正对屏幕视角（`yaw = π/2`）并裁切框外潜水管与角色越界部分；射击场子弹与火花不再穿透到框架外部。\n'
    '- **亚子 · 礼服 经典沙发桌子套装（`f15306_0/1`）与全量双人面对面家具视角复查**：修正亚子单人／双人沙发视角至正斜前方 3/4 朝向亚子面部（`yaw = π/4`），复核日奈 · 礼服等全部 22 项双人面对面家具均朝向当前所选角色面部。\n'
    '- **纱织 · 礼服 豪华全身镜（`saori_dress/f210366_0`）实时镜面反射**：新增 `src/mirror-surface.ts`（`PlanarMirror`），在镜框玻璃处接入实时离线渲染镜面，完整反射纱织 · 礼服正面动作与神情。\n'
    '- **静子 店铺（`shizuko/f203302_0`）与刨冰吧（`shizuko_swimsuit/f9302_0`）视角与粒子修复（含同类排查）**：将静子店铺与刨冰吧旋转 180° 改为正面朝向，并修正 `shizuko/f203302_0` 以及同类问题家具 `nodoka_onsen/f6201_0` 因同名父子节点挂错层级导致 Z-up 粒子掉落在地面上的问题；同时清理第 20 批误写的 `viewYaw` 字段并统一落盘为运行时读取的 `yaw`。\n'
    '- **月咏 龟背竹花盆（`tsukuyo/f4106_0`，`yaw = 1.95`）与月咏 · 礼服 简易更衣室（`tsukuyo_dress/f210389_0`，`yaw = π/4`）**：调整至正面观赏效果最佳的推荐视角。\n'
    '- **第十批收官（Wave 21）十位新角色**：收录最后 8 位拥有 3D 模型的日服已实装学生（切里诺、吹雪、玛丽娜、满、名草、玲女、樱子、高音，14 套外观）以及千禧年临战双子 `momoi_battle`（`NP0267`）与 `midori_battle`（`NP0268`）；补齐 `fubuki_swimsuit` 身体网格切换事件与 `sakurako_idol/f210354_1` 角色内置害羞粒子；全部 16 套外观与 14 项家具通过 167,902 条骨骼通道校验与四向实机截图复核。\n'
    '- 本版默认仅交付可运行文件夹（`release/v0.2.30/win-unpacked/BA Desktop Pet.exe`），不创建 ZIP 压缩包。\n'
)
(R / 'docs/ROSTER-021.md').write_text(roster21, 'utf8')

def prepend(rel, title, text):
    p = R / rel
    s = p.read_text('utf8')
    if title not in s:
        p.write_text(title + '\n\n' + text + '\n\n' + s, 'utf8')

prepend('README.md', '## 0.2.30 家具镜面／裁切／视角修复与新增十位角色', body + '\n\n[详细来源与验收](docs/ROSTER-021.md) · [未加入名单](docs/ROSTER-COVERAGE.md)')
readme = (R / 'README.md').read_text('utf8')
if '当前版本：' in readme:
    start = readme.index('当前版本：')
    end = readme.index('\n\n', start)
    readme = (
        readme[:start]
        + f"当前版本：**0.2.30**。合计 {len(allcs)} 套外观、{total_actions:,} 个普通动作、{total_furniture} 项家具。修复落地窗雨夜与双人互动、潜水池／射击场模板裁切、豪华全身镜实时镜面、亚子／静子／月咏视角与粒子错位等问题，并新增 10 位角色（16 套外观、{wave21_actions} 个动作、{wave21_furniture} 项家具）。详见[ROSTER-021](docs/ROSTER-021.md)。"
        + readme[end:]
    )
readme = readme.replace('`release/v0.2.29/win-unpacked/BA Desktop Pet.exe`', '`release/v0.2.30/win-unpacked/BA Desktop Pet.exe`')
(R / 'README.md').write_text(readme, 'utf8')

prepend('docs/COSTUMES.md', '## 0.2.30 新增十位角色十六套外观', table)
prepend('docs/FURNITURE.md', '## 0.2.30 家具修复与十位新角色家具增量', f"修复美咲／纱织落地窗雨夜光效并补齐双人互动、修复潜水池与射击场视口裁切、新增纱织礼服全身镜实时反射、修复亚子／静子／月咏视角与静子／和香粒子错位，并新增 {wave21_furniture} 项咖啡厅家具互动。详见[ROSTER-021](docs/ROSTER-021.md)。")
prepend('docs/ASSETS.md', '## 0.2.30 十位新角色', '原始官方 JP r96 模型、贴图、骨骼动画与家具时间线按需提取并 CRC 校验，详见[ROSTER-021](docs/ROSTER-021.md)。')
prepend('docs/RANDOM-ROSTER.md', '## 0.2.30 十位角色（收官 8 位 3D 已实装学生 + 临战双子）', body)

print(f'INSTALLED Wave 21! Total: {len(allcs)} outfits, {total_actions} actions, {total_furniture} furniture, {len(installed)}/{len(groups)} playable JP students.')
