"""Add only the four verified outfits, keeping the 0.2.17 payload intact."""
import json,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'test-results';specs=json.loads((R/'scripts/roster-wave13.json').read_text('utf8'))
proof=json.loads((T/'wave13-resources.json').read_text('utf8'));assert len(proof['unchangedPreviousFiles'])==599
assert all(r['status']=='ready'for r in json.loads((T/'wave13-furniture-adaptation.json').read_text('utf8')))
assert not json.loads((T/'wave13-persistent-audit.json').read_text('utf8'))['unexplained']
assert all(not r['omitted']for r in json.loads((T/'wave13-fx-adaptation.json').read_text('utf8')))
for key in specs:
 src=R/'.assets/expanded-ready'/key;target=R/'characters'/key
 assert (src/'thumbnail.png').is_file();shutil.copytree(src,target,dirs_exist_ok=True)
for name in ['package.json','package-lock.json']:
 p=R/name;v=json.loads(p.read_text('utf8'));v['version']='0.2.18'
 if'packages'in v:v['packages']['']['version']='0.2.18'
 if name=='package.json':
  for file in ['docs/ROSTER-013.md','docs/HISTORY-RECHECK-038.md']:
   if not any(x['from']==file for x in v['build']['extraFiles']):v['build']['extraFiles'].append({'from':file,'to':Path(file).name})
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
counts=[json.loads(p.read_text('utf8'))for p in (R/'characters').glob('*/character.json')]
print('Outfits',len(counts),'actions',sum(len(c['actions'])for c in counts),'furniture',sum(len(c.get('furniture',[]))for c in counts))
