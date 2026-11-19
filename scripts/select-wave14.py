"""Choose ten uninstalled students once, with a reproducible draw and exact census."""
from pathlib import Path
import json,secrets,random,hashlib,re,httpx
R=Path(__file__).resolve().parents[1];W=R/'.assets';T=R/'test-results';out=T/'wave14-selection.json'
if out.exists():print(out.read_text('utf8'));raise SystemExit
def read(p):return json.loads(p.read_text('utf8'))
sources={};data={}
for lang in ['en','cn']:
 url=f'https://schaledb.com/data/{lang}/students.json';response=httpx.get(url,timeout=90,follow_redirects=True);response.raise_for_status();(W/f'students-wave14-{lang}.json').write_bytes(response.content);data[lang]=response.json();sources[lang]={'url':url,'sha256':hashlib.sha256(response.content).hexdigest()}
groups={}
for s in data['en'].values():
 if s['IsReleased'][0]:groups.setdefault(s['PersonalName'],[]).append(s)
paths={p.parent.name for p in (R/'characters').glob('*/character.json')};installed={s['PersonalName']for values in groups.values()for s in values if s['PathName']in paths}
catalog=read(W/'catalog.json');names={b['Name']for pack in catalog['FullPatchPacks']for b in pack['BundleFiles']}
def prefix(s):
 candidates=[s['DevName'],s['DevName']+'_Original',s['PersonalName']+'_Original']
 return next((p for p in candidates if any(f'character-{p.lower()}-'in name and'-prefabs-'in name for name in names)),None)
missing={n:[{'id':s['Id'],'devName':s['DevName']}for s in values if not prefix(s)]for n,values in groups.items()if n not in installed};missing={n:v for n,v in missing.items()if v}
pool=sorted(set(groups)-installed-set(missing));seed=secrets.randbits(64);chosen=random.Random(seed).sample(pool,10);specs={};characters=[]
for name in chosen:
 outfits=[]
 for s in sorted(groups[name],key=lambda s:s['Id']):
  cn=data['cn'][str(s['Id'])];p=prefix(s);assert p
  label=cn['Name'];match=re.fullmatch(r'(.+?)[（(](.+)[）)]',label)
  label=(match[1]+' · '+match[2])if match else label+' · 原版'
  specs[s['PathName']]=[p,label]
  outfits.append(dict(id=s['Id'],name=s['Name'],chineseName=cn['Name'],personalName=cn.get('PersonalName'),path=s['PathName'],devName=s['DevName'],prefix=p))
 characters.append({'name':name,'chineseName':data['cn'][str(groups[name][0]['Id'])].get('PersonalName',name),'outfits':outfits})
remaining=sorted(set(groups)-installed-set(chosen))
result={'date':'2026-11-17','scope':'Released JP playable students grouped by PersonalName; alternate outfits and combat forms do not count as additional students. Plana is an installed NPC outside this denominator.','sources':sources,'seed':seed,'universe':sorted(groups),'installedBefore':sorted(installed),'pool':pool,'excludedFromDrawMissingSource':missing,'selected':chosen,'characters':characters,'remainingAfterAddition':remaining,'counts':{'totalPlayableStudents':len(groups),'installedPlayableBefore':len(installed),'added':10,'installedPlayableAfter':len(installed)+10,'remainingAfter':len(remaining),'additionalInstalledNpcs':1 if'plana'in paths else 0}}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8');(R/'scripts/roster-wave14.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'counts':result['counts'],'characters':characters,'excludedFromDrawMissingSource':missing},ensure_ascii=False,indent=2))
