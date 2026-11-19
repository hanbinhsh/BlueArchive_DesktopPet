"""Install six identities plus two specifically requested existing-resource repairs."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results';stage=R/'.assets/wave16-final'
read=lambda p:json.loads(p.read_text('utf8'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
specs=read(R/'scripts/roster-wave16.json');selection=read(T/'wave16-selection.json');old=read(T/'release043-resources.json')
assert len(specs)==10 and len(selection['selected'])==6
assert all(sha(R/'characters'/r['path'])==r['sha256']for r in old)
assert all(not(R/'characters'/key).exists()for key in specs)
assert all(r['status']=='ready'for r in read(T/'wave16-furniture-adaptation.json'))
assert all(not r['omitted']for r in read(T/'wave16-fx-adaptation.json')+read(T/'wave16-embedded-adaptation.json'))
assert not read(T/'wave16-embedded-final-audit.json')['missing']and not read(T/'wave16-persistent-audit.json')['unexplained']
for key in specs:shutil.copytree(stage/key,R/'characters'/key)
for name in ['model.glb','f210356_0.glb','thumbnail.png']:shutil.copy2(R/'.assets/repair044/chiaki'/name,R/'characters/chiaki'/name)
shutil.copy2(R/'.assets/repair044/atsuko_swimsuit/character.json',R/'characters/atsuko_swimsuit/character.json')
changed=[r['path'].replace('\\','/')for r in old if sha(R/'characters'/r['path'])!=r['sha256']]
assert set(changed)=={'chiaki/model.glb','chiaki/f210356_0.glb','chiaki/thumbnail.png','atsuko_swimsuit/character.json'},changed
write(T/'repairs044-resource-changes.json',dict(changed=changed,unchanged=len(old)-len(changed)))
settings=read(R/'scripts/furniture-character-view-yaw.json')
for row in read(T/'wave16-view-selection.json'):settings.setdefault(row['character'],{})[row['id']]=row['yaw']/3.141592653589793
settings.setdefault('atsuko_swimsuit',{})['f13204_0']=.5;write(R/'scripts/furniture-character-view-yaw.json',settings)
allcs={p.parent.name:read(p)for p in(R/'characters').glob('*/character.json')};assert len(allcs)==196
en=read(R/'.assets/students-wave16-en.json');cn=read(R/'.assets/students-wave16-cn.json');groups={}
for s in en.values():
 if s['IsReleased'][0]:groups.setdefault(s['PersonalName'],[]).append(s)
installed={n for n,students in groups.items()if any(s['PathName']in allcs for s in students)};remaining=sorted(set(groups)-installed)
assert installed-set(selection['installedBefore'])==set(selection['selected'])and len(installed)==94 and len(remaining)==55
census=dict(date=selection['date'],sources=selection['sources'],scope=selection['scope'],playableTotal=len(groups),installedPlayable=len(installed),remainingPlayable=len(remaining),additionalInstalledNpcs=['plana'],installed=sorted(installed),remaining=[dict(name=n,chineseName=cn[str(groups[n][0]['Id'])]['Name'],outfits=[dict(id=s['Id'],path=s['PathName'],name=cn[str(s['Id'])]['Name'])for s in groups[n]])for n in remaining],outfits=len(allcs),actions=sum(len(c['actions'])for c in allcs.values()),furniture=sum(len(c.get('furniture',[]))for c in allcs.values()))
write(T/'wave16-census.json',census)
lines=['# 角色加入情况（2026-11-17）','','按保存的[SchaleDB日服已实装数据](https://schaledb.com/data/en/students.json)的 PersonalName 合并服装与战斗形态；家具搭档不计独立学生。普拉娜作为NPC另列。','','已加入 **94/149 位学生**，还未加入 **55位**。加上普拉娜共95个角色分组、196套外观。','','本次随机新增时雨、朱莉、丽、伊吕波、好美、海香，共10套已实装外观。抽取种子、候选池及来源哈希见wave16-selection.json；未定位完整前缀的Reijo、Rana仍包含在未加入名单中。','','| 角色 | 数据标识 | 已实装外观数 |','| --- | --- | --- |']
for r in census['remaining']:lines.append(f"| {r['chineseName']} | {r['name']} | {len(r['outfits'])} |")
(R/'docs/ROSTER-COVERAGE.md').write_text('\n'.join(lines)+'\n','utf8')
for name in ['package.json','package-lock.json']:
 p=R/name;d=read(p);d['version']='0.2.22'
 if name=='package-lock.json':d['packages']['']['version']='0.2.22'
 else:
  entry={'from':'docs/ROSTER-016.md','to':'ROSTER-016.md'}
  if entry not in d['build']['extraFiles']:d['build']['extraFiles'].append(entry)
 write(p,d)
print(json.dumps({k:v for k,v in census.items()if k not in ['sources','installed','remaining']},ensure_ascii=False,indent=2))
