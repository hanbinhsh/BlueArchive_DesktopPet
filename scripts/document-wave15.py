"""Document only installed resources and explicitly recorded exclusions."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results';read=lambda p:json.loads(p.read_text('utf8'))
specs=read(R/'scripts/roster-wave15.json');cs={k:read(R/'characters'/k/'character.json')for k in specs};census=read(T/'wave15-census.json')
def prepend(file,heading,body):
 p=R/file;s=p.read_text('utf8')
 if heading not in s:p.write_text(heading+'\n\n'+body+'\n\n'+s,'utf8')
names='绘里、丽奈、庚、渚、椿、晴、千明、芹娜、亚津子、皋月'
actions=sum(len(c['actions'])for c in cs.values());furniture=sum(len(c.get('furniture',[]))for c in cs.values())
table='| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k,(prefix,name)in specs.items():table+=f"| {name} | {prefix} | {len(cs[k]['actions'])} | {len(cs[k].get('furniture',[]))} |\n"
body=f'随机新增10位学生：{names}，共17套外观、{actions}个普通动作、{furniture}项家具互动。\n\n当前{census["outfits"]}套外观、{census["actions"]:,}个普通动作、{census["furniture"]}项家具。按2026-11-17保存的日服已实装名单，已加入88/149位学生，尚未加入61位；普拉娜NPC另列。来源及验证见[新增角色说明](docs/ROSTER-015.md)，未加入名单见[角色覆盖表](docs/ROSTER-COVERAGE.md)。'
prepend('README.md','## 0.2.21 随机新增十位学生',body)
p=R/'README.md';s=p.read_text('utf8');start=s.index('当前版本：');end=s.index('\n\n',start)
s=s[:start]+f'当前版本：**0.2.21**。合计{census["outfits"]}套外观、{census["actions"]:,}个普通动作、{census["furniture"]}项家具。保留0.2.20的全部676个原有资源（包括一花手机修复）。新增内容见[ROSTER-015](docs/ROSTER-015.md)。'+s[end:]
s=s.replace('`release/v0.2.20/win-unpacked/BA Desktop Pet.exe`','`release/v0.2.21/win-unpacked/BA Desktop Pet.exe`');p.write_text(s,'utf8')
prepend('docs/ASSETS.md','## 0.2.21 十位学生增量','使用官方JP r96原始模型、贴图、骨骼、动画与事件，按需提取与校验。旧676项资源保持逐文件一致，来源和转换记录见[ROSTER-015](ROSTER-015.md)。')
prepend('docs/COSTUMES.md','## 0.2.21 新增17套外观',table+'\n覆盖这十位在保存名单中的已实装外观，不据此宣称其他所有角色服装已完整。')
furnames=[f['name']for c in cs.values()for f in c.get('furniture',[])]
prepend('docs/FURNITURE.md',f'## 0.2.21 新增{furniture}项互动','、'.join(furnames)+'。官方时间线、角色内嵌粒子和默认视角另行检查，详见[ROSTER-015](ROSTER-015.md)。')
prepend('docs/RANDOM-ROSTER.md','## 0.2.21 再随机十位',body.replace('docs/',''))
framing=read(T/'wave15-framing.json');excluded=[dict(character=r['character'],**a)for r in framing for a in r['actions']if a['status']=='requires-scene']
lines=['# 0.2.21 随机新增十位学生','',body.replace('docs/',''),'',table,'## 来源和转换','','抽取种子、候选池、已安装名单与保存于2026-11-17的中英文[SchaleDB数据](https://schaledb.com/data/en/students.json)哈希见wave15-selection.json；按学生身份合并服装，家具搭档不计入独立学生人数。原模型来自官方JP r96缓存补丁目录，定向提取的大小和CRC见wave15-acquisition.json。没有使用同人重建模型或生成图替代原始资源。','','绘里的共享动画在精简预制体先转换时缺少完整Avatar路径，已使用原始Avatar路径表重新绑定，恢复39段原始body动画；新增真实通道检查，元数据名称不足以判为成功。芹娜的医疗包补齐原始共享网格、材质与贴图。亚津子常服原本有面罩且不使用嘴图集，保留源设置。眉眼、口型、光环按原骨骼及事件处理。','','芹娜TSS_Interaction01依赖搭档／技能场景，不能作为单人普通动作，按既有规则明确排除。普通动作逐段采样121个时刻，排除以下需要场景或超出独立桌宠合理取景的片段：','']
for a in excluded:lines.append(f"- {a['character']} / {a.get('sourceName',a['id'])}：{a.get('reason','需要独立场景或取景范围过大')}。")
lines+=['','14项家具保留原时间线、启用轨道及材质，另查常驻和角色内嵌特效，避免只取外部ControlTrack。视角从实际四向画面选择，以角色与家具内容可见为准。全部GLB和贴图本地存储，可离线加载。','','## 验收范围','','保留旧676项资源逐文件一致；运行文件变更另以成品记录为准。采样和视觉检查不等同于游戏光照、后处理、音效及完整技能舞台的逐像素复现。','','最终成品测试与稳定性结果完成后补入。只交付可运行文件夹，不生成ZIP。']
(R/'docs/ROSTER-015.md').write_text('\n'.join(lines)+'\n','utf8')
print('Documented',len(cs),'outfits',actions,'actions',furniture,'furniture')
