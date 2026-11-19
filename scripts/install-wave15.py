"""Install only the verified wave15 increment; preserve all previous resources."""
from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).resolve().parents[1];T=R/'test-results';stage=R/'.assets/wave15-final'
read=lambda p:json.loads(p.read_text('utf8'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
specs=read(R/'scripts/roster-wave15.json');selection=read(T/'wave15-selection.json')
assert len(specs)==17 and len(selection['selected'])==10
assert all(not(R/'characters'/key).exists()for key in specs),'Already installed; do not overwrite'
assert all(not r['omitted']for r in read(T/'wave15-fx-adaptation.json'))
assert not read(T/'wave15-persistent-audit.json')['unexplained']
assert not read(T/'wave15-embedded-final-audit.json')['missing']
previous=read(T/'release042-resources.json')
assert all(sha(R/'characters'/row['path'])==row['sha256']for row in previous)
views=read(T/'wave15-view-selection.json');settings=read(R/'scripts/furniture-character-view-yaw.json')
for row in views:settings.setdefault(row['character'],{})[row['id']]=row['yaw']/3.141592653589793
for key in specs:shutil.copytree(stage/key,R/'characters'/key)
write(R/'scripts/furniture-character-view-yaw.json',settings)
allcs={p.parent.name:read(p)for p in(R/'characters').glob('*/character.json')};assert len(allcs)==186
en=read(R/'.assets/students-wave15-en.json');cn=read(R/'.assets/students-wave15-cn.json');groups={}
for s in en.values():
 if s['IsReleased'][0]:groups.setdefault(s['PersonalName'],[]).append(s)
installed={n for n,students in groups.items()if any(s['PathName']in allcs for s in students)};remaining=sorted(set(groups)-installed)
assert installed-set(selection['installedBefore'])==set(selection['selected'])and len(installed)==88 and len(remaining)==61 and len(groups)==149
census=dict(date=selection['date'],sources=selection['sources'],scope=selection['scope'],playableTotal=len(groups),installedPlayable=len(installed),remainingPlayable=len(remaining),additionalInstalledNpcs=['plana'],installed=sorted(installed),remaining=[dict(name=n,chineseName=cn[str(groups[n][0]['Id'])]['Name'],outfits=[dict(id=s['Id'],path=s['PathName'],name=cn[str(s['Id'])]['Name'])for s in groups[n]])for n in remaining],outfits=len(allcs),actions=sum(len(c.get('actions',[]))for c in allcs.values()),furniture=sum(len(c.get('furniture',[]))for c in allcs.values()))
write(T/'wave15-census.json',census)
names='绘里、丽奈、庚、渚、椿、晴、千明、芹娜、亚津子、皋月'
lines=['# 角色加入情况（2026-11-17）','','以本次保存的[SchaleDB日服已实装学生数据](https://schaledb.com/data/en/students.json)为名单，按 PersonalName 合并服装、战斗形态和同一学生的变体。只有具有独立可选角色包的学生计为已加入；家具里的搭档不计。普拉娜属于额外NPC，单列。','',f'已加入 **{len(installed)} / {len(groups)} 位可操作学生**，还未加入 **{len(remaining)} 位**。加上普拉娜，程序有89位角色分组、186套外观。服装缺项与学生人数分开统计。','',f'本次新增：{names}，共17套外观。固定抽取与来源见wave15-selection.json，实际安装复核见wave15-census.json。预检未定位完整资源前缀的Reijo、Rana仍计入未加入名单，不据此判断以后无法适配。','','## 尚未加入的61位','','| 角色 | 数据标识 | 已实装外观数 |','| --- | --- | --- |']
for row in census['remaining']:lines.append(f"| {row['chineseName']} | {row['name']} | {len(row['outfits'])} |")
(R/'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines)+'\n','utf8')
for name in ['package.json','package-lock.json']:
 p=R/name;v=read(p);v['version']='0.2.21'
 if name=='package-lock.json':v['packages']['']['version']='0.2.21'
 else:
  entry={'from':'docs/ROSTER-015.md','to':'ROSTER-015.md'}
  if entry not in v['build']['extraFiles']:v['build']['extraFiles'].append(entry)
 write(p,v)
print(json.dumps({k:v for k,v in census.items()if k not in ['sources','installed','remaining']},ensure_ascii=False,indent=2))
