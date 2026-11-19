from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results';read=lambda p:json.loads(p.read_text('utf8'))
specs=read(R/'scripts/roster-wave16.json');cs={k:read(R/'characters'/k/'character.json')for k in specs};c=read(T/'wave16-census.json')
def prepend(file,title,text):
 p=R/file;s=p.read_text('utf8')
 if title not in s:p.write_text(title+'\n\n'+text+'\n\n'+s,'utf8')
body='修正千明常服与公告板家具的两套脸部显示索引，避免睁眼和眯眼模型同时出现；原骨骼、口型事件、几何和动作曲线不变。泳装亚津子的喷泉默认视角向参考图调整45°，角色脸与相机位于花丛左侧。\n\n随机新增时雨、朱莉、丽、伊吕波、好美、海香，包含10套外观、243个普通动作及10项家具。当前196套外观、4,935个普通动作、189项家具；按保存的日服名单已加入94/149位学生，尚余55位，普拉娜NPC另列。'
prepend('README.md','## 0.2.22 眼部修复与六位新增学生',body+'\n\n[详细来源与验收](docs/ROSTER-016.md) · [未加入名单](docs/ROSTER-COVERAGE.md)')
p=R/'README.md';s=p.read_text('utf8');start=s.index('当前版本：');end=s.index('\n\n',start);s=s[:start]+'当前版本：**0.2.22**。合计196套外观、4,935个普通动作、189项家具。修复千明眼部显示，调整亚津子喷泉视角，新增六位学生。详见[ROSTER-016](docs/ROSTER-016.md)。'+s[end:];s=s.replace('`release/v0.2.21/win-unpacked/BA Desktop Pet.exe`','`release/v0.2.22/win-unpacked/BA Desktop Pet.exe`');p.write_text(s,'utf8')
table='| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k,(prefix,name)in specs.items():table+=f"| {name} | {prefix} | {len(cs[k]['actions'])} | {len(cs[k].get('furniture',[]))} |\n"
text='# 0.2.22 眼部修复、喷泉视角与六位新增学生\n\n'+body+'\n\n'+table+'''
## 修复与来源

千明原始CH0238动画用7/8切换Face01/Face02，当前预制体的这两项却位于6/7；旧转换错误地切到Face02及Halo，导致脸部叠加。现将原始事件索引解析到正确的命名脸部，修复47个普通片段和公告板场景，保留事件原时间／数值与全部骨骼动画。实际修复前后、9个面部时刻与15792条普通／402条家具通道检查见chiaki044-*和facesfix044-*。后续基础转换、动作扩展和家具合成都共用该映射。

喷泉仅调整默认水平角度为π/2，保留原相机、闪光、喷泉、水面及花丛。已保存的个人旋转不会被重置，可使用“恢复角度”查看新的默认视角。

随机名单按2026-11-17保存的中英文[SchaleDB数据](https://schaledb.com/data/en/students.json)，按学生身份合并服装，抽取种子、候选池与SHA256见wave16-selection.json。模型、骨骼、贴图、动画和家具时间线来自官方JP r96缓存资源，按需提取与CRC校验。家具搭档不计独立新增学生：泳装伊吕波的双人沙浴保留已加入的泳装伊吹。

温泉时雨的浴缸水面效果原本仅由静态网格组成，没有粒子系统作为模板；现为这些原网格建立不运动的单实例材质描述，保留原几何、UV和着色，并补回鸭子泡泡、脸部效果。樱花长椅的常驻水面与飘落效果按原预制体补回。沙浴中的pos是原生发射和渲染均关闭的空叶节点，已记录原CAB／对象ID，不伪造可见粒子。

时雨汗滴使用原0.35～0.85次/秒的随机发射范围。已用本地Unity2022.3无界面探针核验其积分发射行为，并对照[Emission模块文档](https://docs.unity3d.com/2022.3/Documentation/Manual/PartSysEmissionModule.html)。离线转换采用固定种子的60Hz采样，暂停／寻址时稳定重现；没有宣称逐位复刻Unity私有随机序列。原图集、方向、尺寸、颜色、寿命和随骨骼位置保留。

## 验收范围

普通动作逐段121时刻取景检查。需要搭档或完整技能场景、超出独立桌宠取景的片段明确排除，不用占位动画替代。已加入角色的本批10套外观覆盖保存名单中这六位的已实装外观，其他角色服装缺项另按覆盖表记录。

旧741文件中仅千明的2个GLB与缩略图、亚津子喷泉的描述JSON改变，其他737个保持0.2.21。没有修改程序的渲染／窗口／设置逻辑。最终成品验收完成后补入。本版仅交付可运行文件夹，不生成ZIP。
'''
(R/'docs/ROSTER-016.md').write_text(text,'utf8')
prepend('docs/COSTUMES.md','## 0.2.22 新增六位学生十套外观',table)
prepend('docs/FURNITURE.md','## 0.2.22 家具增量与修复','新增10项家具，包含水果吧、温泉浴缸、松饼桌、发球机、沙浴单人／双人、樱花长椅、杂志架、粉色电吉他和面具架。双人沙浴保留泳装伊吹；常驻水面／泡泡与角色内嵌效果另审计。千明脸部切换和亚津子喷泉角度同步修复，见[ROSTER-016](ROSTER-016.md)。')
prepend('docs/ASSETS.md','## 0.2.22 六位学生与资源修复','原始官方模型与事件，按需提取；修复千明事件索引，补齐静态水面与内嵌汗滴。详见[ROSTER-016](ROSTER-016.md)。')
prepend('docs/RANDOM-ROSTER.md','## 0.2.22 随机六位',body)
print('Documented',len(cs),'outfits',sum(len(x['actions'])for x in cs.values()),'actions')
