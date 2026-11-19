"""Extract just the missing original book material from a verified cached pack."""
from pathlib import Path
import json,zipfile,zlib
W=Path('.assets');cab='cab-a017bae79d399841adcc6a38da9c661b';index=json.loads((W/'cab-index.json').read_text('utf8'))['cabs'];pack,name=index[cab]
catalog=json.loads((W/'catalog.json').read_text('utf8'));meta=next(b for p in catalog['FullPatchPacks']for b in p['BundleFiles']if b['Name']==name)
acquired=[]
for p in catalog['FullPatchPacks']:
 selected=[b for b in p['BundleFiles']if'3dobject-shimiko_original_book-'in b['Name']]
 if not selected:continue
 with zipfile.ZipFile(W/'packs'/p['PackName'])as archive:
  for b in selected:
   raw=archive.read(b['Name']);assert len(raw)==b['Size']and zlib.crc32(raw)==b['Crc'];(W/'selected'/b['Name']).write_bytes(raw);acquired.append({'pack':p['PackName'],'bundle':b});print(b['Name'])
Path('test-results/shimiko14-book-dependency.json').write_text(json.dumps({'cab':cab,'acquired':acquired},indent=2),'utf8')
