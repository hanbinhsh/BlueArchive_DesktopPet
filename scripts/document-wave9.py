import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf8'))
specs=read('scripts/roster-wave9.json')
cs={p.parent.name:json.loads(p.read_text(encoding='utf8')) for p in (R/'characters').glob('*/character.json')}
assert len(cs)==110
total=sum(len(c['actions']) for c in cs.values());added=sum(len(cs[k]['actions']) for k in specs)
def prepend(file,title,body):
    p=R/file;s=p.read_text(encoding='utf8')
    if '## 0.1.20' in s:return
    first,rest=s.split('\n',1);p.write_text(first+'\n\n'+title+'\n\n'+body.strip()+'\n'+rest,encoding='utf8')
prepend('README.md','## 0.1.20 初音未来与随机角色',f'''新增初音未来，以及随机抽取的茜（原版／兔女郎／制服）、三森（原版／泳装）、御伽、佐天泪子、萌绘（原版／泳装）。共新增 6 位角色、10 套外观、{added} 个菜单动作；当前合计 **47 位角色、110 个外观／形态、{total:,} 个可选动作**，原有 79 组家具互动保留。

原版模型、贴图、眼眉、口型及动画随程序提供，可离线使用。初音未来原模型没有光环；初音未来与佐天泪子未提供独立提起片段，拖动时保持各自待机。新增角色的技能舞台、演唱、音效与专属家具未移植。通过「角色与动作」搜索姓名并切换外观。''')
p=R/'README.md';p.write_text(p.read_text(encoding='utf8').replace('解压 `release/BA-Desktop-Pet-0.1.19-win-x64.zip`','解压 `release/BA-Desktop-Pet-0.1.20-win-x64.zip`'),encoding='utf8')
prepend('docs/ASSETS.md','## 0.1.20 来源补充','''新增 10 包均使用官方 JP r96 patch 33 的原版资源。原包和 bundle 已按目录提供的大小与 CRC 校验；三森、萌绘泳装所需的原版光环依赖一起打包。没有使用同人重建或借用其他角色的动画。

支援角色的一些自身动画未被咖啡厅控制器引用，转换时通过明确的原始片段名单补充绑定；相机、无人机、士兵和专用道具片段排除。御伽有 4 个原始事件引用不存在的第 11 个渲染器；本版保留原始事件记录，仅忽略这些无目标的事件，不将它们错误映射到脸部或其他网格。证据：`wave9-otogi-bindings.json`、`wave9-body-clip-scope.json`。''')
selection=read('test-results/wave9-selection.json')
body=f'''本轮从尚未收录的日服已实装角色组中随机抽取 5 位：茜、三森、御伽、佐天泪子、萌绘；初音未来为指定角色。抽样不重复，不把同一角色的不同服装当作不同抽选名额。随机种子为 `{selection['seed']}`，候选池和来源摘要保存在 `test-results/wave9-selection.json`。

按 2026-10-24 保存的学生数据，以上六位共 10 套；与保存的[角色模型页面](https://zh.bluearchive.wiki/wiki/角色模型)条目逐一对应。当前全部已收录角色为 47 位、110 包、{total:,} 个菜单动作。本段为 0.1.20 增量，后文保留 0.1.19 当时的核对范围。

| 新增外观 | 菜单动作数 |
| --- | --- |
'''
for key in specs:body+=f"| {cs[key]['name']} | {len(cs[key]['actions'])} |\n"
body+='\n初音未来没有原版光环；初音未来及佐天泪子没有独立提起动画。技能舞台、音效和演唱未移植；以下片段若需原场景或不能在桌宠取景内正常展示，不作为可用动作开放。\n\n| 外观 | 未开放片段 | 原因 |\n| --- | --- | --- |\n'
for row in read('test-results/action-expansion.json'):
    if row['character'] in specs:
        for item in row.get('unavailable',[]):body+=f"| {cs[row['character']]['name']} | {item.get('clip','—')} | {item['reason']} |\n"
for row in read('test-results/expanded-framing.json'):
    if row['character'] in specs:
        for a in row['actions']:
            if a['status']=='requires-scene':body+=f"| {cs[row['character']]['name']} | {a.get('sourceName',a['id'])} | {a.get('reason','场景位移或范围超出桌宠可用取景')} |\n"
prepend('docs/MODEL-AUDIT.md','## 0.1.20 指定与随机角色增量',body)
prepend('docs/FURNITURE.md','## 0.1.20 保留情况','当前 110 个外观包保留原有 79 组家具互动。本版增加 10 套角色外观，没有增加它们的专属家具；菜单中的角色动作不代表对应场景已完整移植。')
print('Documentation updated:',len(cs),'packs;',total,'actions;',added,'new actions')
