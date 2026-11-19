"""Document the exact installed addition before packing the candidate."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];specs=json.loads((R/'scripts/roster-wave13.json').read_text('utf8'));cs={p.parent.name:json.loads(p.read_text('utf8'))for p in (R/'characters').glob('*/character.json')}
assert len(cs)==154
def prepend(file,heading,body):
 p=R/file;s=p.read_text('utf8')
 if heading in s:return
 p.write_text(heading+'\n\n'+body+'\n\n'+s,'utf8')
prepend('README.md','## 0.2.18 若藻与伊吹','新增若藻原版／泳装、伊吹原版／泳装，共4套外观、128个普通动作及5项家具互动，包含伊吹与伊吕波泳装的双人沙浴。当前154套外观、3,936个普通动作、150项家具。保留0.2.17鹤城泡沫、日奈水面顺序和美祢液体修复。新增来源及验证范围见 [ROSTER-013](docs/ROSTER-013.md)。')
p=R/'README.md';p.write_text(p.read_text('utf8').replace('release/BA-Desktop-Pet-0.2.17-win-x64.zip','release/BA-Desktop-Pet-0.2.18-win-x64.zip'),'utf8')
prepend('docs/ASSETS.md','## 0.2.18 若藻与伊吹（2026-11-17）','新增4套官方原始模型及其自带骨骼、原动作曲线、材质和光环。若藻常服原始预制体戴面具且不含口型图集；其余3套保留原始口型事件。另适配5项家具，双人沙浴的伊吕波作为场景搭档。原有599个资源保持0.2.17逐文件一致。来源与限制见[ROSTER-013](ROSTER-013.md)。')
body='本次指定若藻、伊吹，各含原版与泳装。按2026-11-17保存的学生数据，覆盖这两位角色的4项已实装外观；用户指定网页尚未列出伊吹泳装，采用官方CH0347原始模型。其他角色的皮肤目录不因本增量宣称重新完成全量核对。\n\n| 外观 | 普通动作 | 家具互动 |\n| --- | --- | --- |\n'
for k in specs:body+=f"| {cs[k]['name']} | {len(cs[k]['actions'])} | {len(cs[k].get('furniture',[]))} |\n"
prepend('docs/COSTUMES.md','## 0.2.18 指定角色增量',body)
prepend('docs/FURNITURE.md','## 0.2.18 五项新增互动','新增若藻情人节曲奇沙发、泳装复古音乐扩音器、伊吹一步一脚印书桌套装、伊吹泳装单人沙浴池和双人沙浴池。双人沙浴带原始伊吕波泳装场景搭档；完整时间线约55.83秒，保留原后半段休息。默认视角已按四方向对照选定。合计150项，来源及验收见[ROSTER-013](ROSTER-013.md)。')
print('Documented new outfits and furniture')
