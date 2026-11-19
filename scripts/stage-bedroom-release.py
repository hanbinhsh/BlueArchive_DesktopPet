"""Record the verified bedroom repair without rewriting historical notes."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
manifests=[json.loads(p.read_text(encoding='utf8')) for p in (R/'characters').glob('*/character.json')]
counts={'packs':len(manifests),'actions':sum(len(m['actions']) for m in manifests),'furniture':sum(len(m.get('furniture',[])) for m in manifests)}
assert counts=={'packs':110,'actions':2693,'furniture':86},counts
assert not [(m['id'],a['clip']) for m in manifests for a in m['actions'] if re.search(r'Cafe_Prop|Cafe_Interact|TSS_Interact',a['clip'],re.I)]
notes={
'README.md':'''## 0.1.22 日奈睡衣家具修复

补齐日奈睡衣的原版卧室床、窗边沙发及七组同步动作。原先单独显示的七个“咖啡厅 · Prop”动作已移入 **家具互动**，选择日奈睡衣后即可播放。床提供坐卧、安睡、翻身、坐姿；沙发提供坐下、休息、起身。

夏的乐队场景形态“伸懒腰”已对照重新导出的官方片段，前倾弯腰属于原始动作，按用户要求保持不变。当前为 **47 位角色、110 套外观／形态、2,693 个普通动作、86 组家具互动**；动作总数没有减少，七项改为带家具播放。
''',
'docs/FURNITURE.md':'''## 0.1.22 卧室场景修复

新增日奈睡衣的两件官方场景家具、七组互动，当前共 86 组，覆盖 61 个外观包。进入“日奈 · 睡衣”→“家具互动”，可选卧室床的坐卧、安睡、翻身、坐姿，以及窗边沙发的坐下、休息、起身。原来普通动作菜单中对应的七项已移到这里，避免脱离家具悬空播放。

资源来自官方 JP r96 patch 33 的 `Field833/Zone01` 场景。人物与家具按原始 Timeline 的 clip-in、时长及速度同步；床的枕头、被子和沙发抱枕使用原始骨骼。原场景用于固定视角，桌宠中补上家具薄面背面显示，并分别设置适合床与沙发的默认朝向。没有把整间卧室搬入桌面，也未加入场景淡入淡出。
''',
'docs/ASSETS.md':'''## 0.1.22 原版卧室家具来源

日奈睡衣新增 `field_833_zone01` 中的 `Prop_Field_833_Zone01_Bed_Mesh`、`Prop_Field_833_Zone01_Windowsofa_Mesh`，来源为既有官方 JP r96 patch 33 资源目录。所需依赖按 bundle 获取，新增纹理由 `FullPatch_029.zip` 校验大小和 CRC 后提取。床四段 Day00–Day03、沙发 Start/Ing/End 与角色 `Field_Player_NP0009_Cafe_Prop_Field_833_Zone01_*` 按官方时间轴组合，嵌入 GLB，可离线加载。

每个 GLB 的 `BA_furniture.sourceTimeline` 记录原时间轴；完整绑定与 clip-in 记录见源码目录 `test-results/bedroom-composition.json`，导出和转换脚本为 `export-bedroom-prefab.py`、`prepare-bedroom-interactions.py`。本版没有改变任何原有角色 `model.glb`。
''',
'docs/MODEL-AUDIT.md':'''## 0.1.22 场景动作与缺失家具核对（2026-10-25）

- 夏的乐队场景形态：从官方 `CH0221_NonWeapon_Stretching` 重新导出 10.9 秒片段并与现有模型对照，均出现明显前倾弯腰。按用户说明保留原版姿态，不安装试验导出的替代文件。正式 `natsu_band_relax` 文件与 0.1.21 完全一致。
- 日奈睡衣：七项 `Cafe_Prop_Field_833` 片段确实依赖卧室家具，补齐原版床与窗边沙发，并移至家具互动。原始片段仍保留在角色 GLB 中，不删除动画。
- 扫描全部 110 个包的 2,700 个原菜单动作，扩展检索家具、床椅、非武装及场景命名，共筛出 56 项。七项为本次日奈修复；其余 49 项是夏的两项原动作、日奈五项基本场景动作，以及爱丽丝／凯伊／时四个剧情装备包的 42 项站立、移动、战斗片段。没有找到另一组明确按家具名称绑定、却仍作为普通动作开放的候选。
- 普通动作导入增加 `Cafe_Prop` 拦截，与已有 `Cafe_Interact`、`TSS_Interact` 一样要求通过家具组合适配。修复后普通菜单中这三类未组合片段为零。
- 这是命名与绑定元数据排查，并针对日奈／夏做画面复核；没有逐一重新观看所有角色、所有技能效果，不能据此声称全部场景和家具均已移植。

证据：`scene-audit-before.json`、`natsu-original-check.json`、`natsu-scene-repair.json`、`scene-action-candidates.json`、`bedroom-composition.json`、`bedroom-fixed-contact.jpg`。
'''
}
for name,note in notes.items():
    p=R/name;s=p.read_text(encoding='utf8')
    if '## 0.1.22 ' in s:continue
    first,rest=s.split('\n',1)
    if name!='README.md':first=first.replace('0.1.20','0.1.22')
    s=first+'\n\n'+note+'\n'+rest
    if name=='README.md':s=s.replace('BA-Desktop-Pet-0.1.21-win-x64.zip','BA-Desktop-Pet-0.1.22-win-x64.zip')
    p.write_text(s,encoding='utf8')
(R/'test-results/bedroom-menu-audit.json').write_text(json.dumps({**counts,'explicitUnpairedFurnitureActions':0,'ordinaryActionsMovedToFurniture':7,'fullVisualAudit':False},indent=2),encoding='utf8')
print(counts)
