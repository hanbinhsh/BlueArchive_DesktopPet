"""Isolate the new outfits so furniture partners come from current installed packs."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];specs=json.loads((R/'scripts/roster-wave16.json').read_text('utf8'));root=R/'.assets/wave16-final';root.mkdir(exist_ok=True)
assert all(r['prepared']for r in json.loads((R/'test-results/wave16-preparation.json').read_text('utf8')))
for key in specs:shutil.copytree(R/'.assets/expanded-ready'/key,root/key,dirs_exist_ok=True)
rows=[r for r in json.loads((R/'test-results/action-expansion.json').read_text('utf8'))if r['character']in specs]
assert len(rows)==len(specs)
assert all(u['reason']=='Requires matching furniture or companion scene; use furniture interactions'for r in rows for u in r['unavailable'])
(R/'test-results/wave16-action-expansion.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8')
print('Isolated',len(specs),'packs;',sum(r['after']for r in rows),'original actions before framing')
