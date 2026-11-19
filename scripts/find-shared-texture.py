import pathlib,zipfile,UnityPy,json,zlib,sys
W=pathlib.Path('.assets'); wanted=sys.argv[1].lower() if len(sys.argv)>1 else 'cab-f22b4e8c962584c59902466b8b07fbe7'
for p in (W/'packs').glob('*.zip'):
 with zipfile.ZipFile(p) as z:
  for name in z.namelist():
   if not name.endswith('.bundle'):continue
   raw=z.read(name); e=UnityPy.load(raw)
   if any(wanted==f.lower() for f in e.files[next(iter(e.files))].files):
    (W/'selected'/name).write_bytes(raw);print('FOUND',p.name,name,flush=True);raise SystemExit
print('Not in cached packs')
