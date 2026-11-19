"""Build the release audit from the captured resource evidence."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def prepend(p,title,text):
    f=R/p;s=f.read_text(encoding='utf8'); marker='## 0.1.19'
    if marker in s:return
    first,rest=s.split('\n',1);f.write_text(first+'\n\n'+title+'\n\n'+text.strip()+'\n'+rest,encoding='utf8')
manifests={p.parent.name:json.loads(p.read_text(encoding='utf8')) for p in (R/'characters').glob('*/character.json')}
rows=read('test-results/wiki-model-comparison.json')
text='''# 模型与动作核对（0.1.19）

核对范围为已收录的 41 位角色，资源目录共 100 个外观／形态包、2,487 个可选动作。数据取自 2026-10-23 保存的[角色模型页面](https://zh.bluearchive.wiki/wiki/角色模型)及其模型文件，与官方 JP r96 patch 33 导出资源逐项对照；不代表该日期之后的新增资源。

学生名单核对包含 86 个已实装学生／普拉娜包；另外 14 个为剧情、装备或其他形态，见服装核对表和额外外观说明。模型页面包含这些角色的 99 个条目（未列普拉娜），其中 97 个已对应到本地包或该包的动作；2 个特殊资源不作为独立桌宠。不同条目可能共用外观，所以页面条目数不等于桌宠包数。

## 本次新增

优香（原版、体操服、睡衣）、八云（原版）、未花（原版、泳装）、千世（原版、泳装）、绮良（原版）、忧（原版、泳装），共 6 位角色、11 套服装。

另增爱丽丝临战携带武器、凯伊携带道具、凯伊剧情战斗、时临战剧情战斗、夏乐队场景动作，共 5 个包；凯伊白色剧情服增加自己的携带待机。携带形态只有自身待机／走路时，点击播放走路，不借用其他模型的提起片段。

## 动作范围与来源

动作菜单按常用、编队与胜利、战斗、技能、移动、剧情分类；动作窗口支持名称及原始片段名搜索。2,487 是菜单条目总数，不是唯一动画文件数量。新增动作取自原版骨骼轨道和原版事件；旧版 459 个常用动作、原材质与贴图、79 组家具互动保持一致。随机待机仍只选择原先审核过的常用动作。

优香睡衣和夏乐队无武器模型的本地转换未输出可用骨骼轨道，因此从该页面固定版本的社区原版提取 GLB 恢复对应骨骼 TRS，逐节点核对绑定变换；继续使用官方模型、贴图、口型及显隐事件，没有引入社区额外 Mouth 网格。分别恢复 30 和 2 段轨道。文件地址与 SHA-256 写入各包 character.json 的 source 字段和测试报告。

这些动作不包含完整游戏场景、攻击目标、技能粒子、弹道或音效。需要其他模型、家具或缺失事件的片段没有强行挂到当前角色。夏的鼓家具仍在原有家具入口；场景版仅开放站立与伸懒腰。优香睡衣另有 5 段 Cut-in 因缺少对应原始事件元数据未开放。星野原版 Victory_End、泳装泉奈 Normal_Reload_Random 因场景位移／取景异常从菜单排除，原 GLB 轨道保留。不能将本次结果理解为原游戏所有场景及动作完整复现。

## 页面条目对照

| 角色 | 页面形态 | 本地对应 | 状态／说明 |
| --- | --- | --- | --- |
'''
for r in rows:
    key=r.get('pack');local=manifests.get(key,{}).get('name',key or '—')
    text+=f"| {r['character']} | {r['label']} | {local} | {r['status']}：{r['reason']} |\n"
text+='\n## 未开放片段记录\n\n下表来自实际转换报告，保留原始片段名与具体原因；场景家具动作可能已从家具入口单独提供。\n\n| 本地包 | 原始片段 | 原因 |\n| --- | --- | --- |\n'
for r in read('test-results/action-expansion.json'):
    for item in r.get('unavailable',[]):text+=f"| {r['character']} | {item.get('clip','—')} | {str(item.get('reason',item)).replace('|','/')} |\n"
(R/'docs/MODEL-AUDIT.md').write_text(text,encoding='utf8')
prepend('README.md','## 0.1.19 角色与动作扩充','''新增优香（原版／体操服／睡衣）、八云、未花（原版／泳装）、千世（原版／泳装）、绮良、忧（原版／泳装），以及爱丽丝、凯伊、时、夏的 5 个装备／场景形态。当前合计 **41 位角色、100 个外观／形态、2,487 个可选动作**；原有 79 组家具互动保留。

在「角色与动作」窗口按分类筛选或搜索动作，支持原始片段名；托盘动作菜单也按类别展开。扩展了战斗、技能、移动和剧情动作，但未复现技能粒子、音效和攻击目标。已按角色模型页面核对全部收录角色，97 个页面条目有本地对应，另有 2 个特殊资源不适合作为独立桌宠。来源、未开放动作与核对范围见 [模型与动作核对](docs/MODEL-AUDIT.md)。''')
p=R/'README.md';p.write_text(p.read_text(encoding='utf8').replace('解压 `release/BA-Desktop-Pet-0.1.17-win-x64.zip`','解压 `release/BA-Desktop-Pet-0.1.19-win-x64.zip`'),encoding='utf8')
prepend('docs/ASSETS.md','## 0.1.19 来源补充','''新增 16 个外观／形态包并扩充原版动作，官方资源版本 JP r96 patch 33。下载仅限所需资源包，文件大小与 CRC 已核验。

优香睡衣、夏乐队场景版的骨骼轨道恢复使用角色模型页面的社区原版提取文件，版本固定为 BlueArchiveModels 提交 `525ae0faeb0a89f54ef4023f3be3692dcb529e51`。官方模型、贴图、口型及显隐事件保留；未使用同人重建模型。包描述中包含动画参考 URL 与摘要。恢复报告分别为 `test-results/yuuka-pajama-reference-recovery.json` 和 `test-results/natsu-nonweapon-reference-recovery.json`。完整逐项来源与限制见 [模型与动作核对](MODEL-AUDIT.md)。''')
prepend('docs/COSTUME-EXTRAS.md','## 0.1.19 补充形态','''新增爱丽丝临战（携带武器）、凯伊原版（携带道具）、凯伊原版（剧情战斗）、时临战（剧情战斗）、夏乐队（场景动作）。另给已有凯伊白色剧情服补入原版携带待机，未重复创建相同服装。小桃、小绿白色外套仍对应模型页面的 Battle 形态。

页面中的凯伊 Prototype 无动画；未花 Cut-in 仅有技能演出，缺少独立桌宠待机。二者不列入可选角色，也不算已适配完成。完整对照见 [模型与动作核对](MODEL-AUDIT.md)。''')
prepend('docs/COSTUMES.md','## 0.1.19 核对范围补充','学生实装服装表之外，另核对了角色模型页面中的剧情、装备、场景与技能专用模型。详细对照及未适配项目见 [模型与动作核对](MODEL-AUDIT.md)。')
prepend('docs/FURNITURE.md','## 0.1.19 保留情况','当前 100 个角色外观／形态包继续提供原有 79 组家具互动（覆盖 60 个包）。本版未增加家具；普通动作菜单中的场景片段不代表已经适配对应家具。家具模型、配置和原版动画与 0.1.18 保持一致。')
package=read('package.json')
if not any(x['from']=='docs/MODEL-AUDIT.md' for x in package['build']['extraFiles']):package['build']['extraFiles'].append({'from':'docs/MODEL-AUDIT.md','to':'模型与动作核对.md'})
(R/'package.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Repair encoding from the earlier generated test, using source literals.
p=R/'scripts/wave8-panel-test.mjs';s=p.read_text(encoding='utf8');s=s.replace('����','常用');s=s.replace("await page.evaluate(()=>window.pet.menu());const event", "await page.evaluate(()=>window.pet.menu());await page.waitForTimeout(80);const event")
p.write_text(s,encoding='utf8')
print('Wave 8 audit and release documentation generated')
