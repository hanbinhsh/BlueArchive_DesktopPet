"""Install only the fifteen new packs and record the actual student census."""
from pathlib import Path
import json,math,shutil,hashlib
R=Path(__file__).resolve().parents[1];T=R/'test-results';stage=R/'.assets/wave14-final'
read=lambda p:json.loads(p.read_text('utf8'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
specs=read(R/'scripts/roster-wave14.json');selection=read(T/'wave14-selection.json')
assert len(specs)==15 and len(selection['selected'])==10
assert not any((R/'characters'/key).exists()for key in specs),'Batch is already installed; do not apply view offsets twice'
assert all(not r['omitted']for r in read(T/'wave14-fx-adaptation.json'))
assert not read(T/'wave14-persistent-audit.json')['unexplained']
settings=read(R/'scripts/furniture-character-view-yaw.json')
# Offsets are selected from the captured four-view comparison. Kaho looks
# toward the goods cabinet, so its contents remain visible in her default view.
offsets={'anna':{'f211316_0':1},'tomoe':{},'tomoe_qipao':{},'hinata':{'f2103_0':1.5,'f207314_1':.1},'hinata_swimsuit':{},'misaka_mikoto':{'f210322_0':.5},'kirino':{'f211304_0':1.5},'kirino_swimsuit':{},'ichika':{'f10206_0':1.5},'ichika_swimsuit':{'f210376_1':1.5},'ritsu':{'f210383_0':1},'mashiro_swimsuit':{'f4200_0':.5},'kaho':{'f209302_0':1.5}}
views=[]
for key in specs:
 cp=stage/key/'character.json';c=read(cp)
 for f in c.get('furniture',[]):
  previous=f['yaw'];f['yaw']=(previous+math.pi*offsets.get(key,{}).get(f['id'],0))%(math.pi*2);settings.setdefault(key,{})[f['id']]=f['yaw']/math.pi
  views.append(dict(character=key,id=f['id'],oldYaw=previous,yaw=f['yaw']))
 write(cp,c)
 target=R/'characters'/key;assert not target.exists(),f'Already installed {key}; do not apply view offsets twice'
 shutil.copytree(stage/key,target)
write(R/'scripts/furniture-character-view-yaw.json',settings);write(T/'wave14-view-selection.json',views)
allcs={p.parent.name:read(p)for p in(R/'characters').glob('*/character.json')};assert len(allcs)==169
en=read(R/'.assets/students-wave14-en.json');cn=read(R/'.assets/students-wave14-cn.json');groups={}
for student in en.values():
 if student['IsReleased'][0]:groups.setdefault(student['PersonalName'],[]).append(student)
installed={n for n,students in groups.items()if any(s['PathName']in allcs for s in students)};remaining=sorted(set(groups)-installed)
assert installed-set(selection['installedBefore'])==set(selection['selected'])and len(installed)==78 and len(remaining)==71 and len(groups)==149
census=dict(date=selection['date'],sources=selection['sources'],scope=selection['scope'],playableTotal=len(groups),installedPlayable=len(installed),remainingPlayable=len(remaining),additionalInstalledNpcs=['plana'],installed=sorted(installed),remaining=[dict(name=n,chineseName=cn[str(groups[n][0]['Id'])]['Name'],outfits=[dict(id=s['Id'],path=s['PathName'],name=cn[str(s['Id'])]['Name'])for s in groups[n]])for n in remaining],outfits=len(allcs),actions=sum(len(c.get('actions',[]))for c in allcs.values()),furniture=sum(len(c.get('furniture',[]))for c in allcs.values()))
write(T/'wave14-census.json',census)
lines=['# 角色加入情况（2026-11-17）','','以本次保存的[SchaleDB日服已实装学生数据](https://schaledb.com/data/en/students.json)为名单，按 PersonalName 合并服装、战斗形态和同一学生的变体。只有具有独立可选角色包的学生计为已加入；家具里的搭档不计。普拉娜属于额外NPC，单列。','',f'已加入 **{len(installed)} / {len(groups)} 位可操作学生**，还未加入 **{len(remaining)} 位**。加上普拉娜，程序有79位角色分组、169套外观。此数目不是“还缺71套服装”；已加入角色的服装数单独记录。','','本次新增：安娜、巴、日向、御坂美琴、桐乃、一花、律、真白、志美子、果穗，共15套外观。抽取种子、候选池、已安装名单与来源哈希见validation/wave14-selection.json；实际安装后复核见wave14-census.json。预检未定位到完整资源前缀的Reijo、Rana没有参加本次抽取，仍包含在未加入名单内，不据此判断未来无法适配。','','## 尚未加入的71位','','| 角色 | 数据标识 | 已实装外观数 |','| --- | --- | --- |']
for row in census['remaining']:lines.append(f"| {row['chineseName']} | {row['name']} | {len(row['outfits'])} |")
(R/'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines)+'\n','utf8')
for name in ['package.json','package-lock.json']:
 p=R/name;v=read(p);v['version']='0.2.19'
 if name=='package-lock.json':v['packages']['']['version']='0.2.19'
 else:
  for file in ['ROSTER-014.md','ROSTER-COVERAGE.md']:
   entry=dict(**{'from':'docs/'+file,'to':file})
   if entry not in v['build']['extraFiles']:v['build']['extraFiles'].append(entry)
 write(p,v)
print(json.dumps({k:v for k,v in census.items()if k not in ['sources','installed','remaining']},ensure_ascii=False,indent=2))
