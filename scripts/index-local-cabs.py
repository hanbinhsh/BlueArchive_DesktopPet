"""Index cached bundle headers for targeted, repeatable dependency resolution."""
import pathlib,json,UnityPy
root=pathlib.Path('.assets');target=root/'local-cab-index.json'
index=json.loads(target.read_text()) if target.exists() else {'files':{},'cabs':{}}
for folder in ['selected','costume-audit','costume-variants','r97/selected']:
    for p in (root/folder).glob('*.bundle'):
        key=str(p);stamp=[p.stat().st_size,p.stat().st_mtime_ns]
        if index['files'].get(key)==stamp:continue
        env=UnityPy.load(str(p))
        for bundle in env.files.values():
            for cab in bundle.files:index['cabs'][cab.lower()]=key
        index['files'][key]=stamp
target.write_text(json.dumps(index,indent=2));print('Indexed',len(index['cabs']),'local CABs')
