"""Extract only Serina's referenced original healing-pack resource group."""
from pathlib import Path
import json,zipfile,zlib
W=Path('.assets');catalog=json.loads((W/'catalog.json').read_text('utf8'));rows=[]
for pack in catalog['FullPatchPacks']:
 matches=[b for b in pack['BundleFiles']if '3dobject-serina_original_healpack-'in b['Name']]
 if not matches:continue
 with zipfile.ZipFile(W/'packs'/pack['PackName'])as source:
  for b in matches:
   raw=source.read(b['Name']);assert len(raw)==b['Size']and zlib.crc32(raw)==b['Crc'];(W/'selected'/b['Name']).write_bytes(raw);rows.append(dict(pack=pack['PackName'],bundle=b));print(b['Name'])
assert rows
Path('test-results/wave15-shared-dependencies.json').write_text(json.dumps(rows,indent=2),'utf8')
