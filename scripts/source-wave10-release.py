import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];archive=R/'release/BA-Desktop-Pet-0.2.1-source.zip'
chosen=[]
for root in ['src','scripts','tests','docs']:
    chosen.extend(p for p in (R/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
chosen.extend(R/p for p in ['native/WindowWheel.cs','package.json','package-lock.json','tsconfig.json','.gitignore','README.md'])
reports=['wave10-selection.json','wave10-resources.json','wave10-preview.json','wave10-runtime.json','wave10-packaged-runtime.json','wave10-library.json','wave10-packaged-scroll.json','wave10-hold.json','wave10-transitions.json','wave10-expression-source.json','wave10-expressions.json','wave10-package.json','release-0.2.1.json']
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(chosen)):z.write(p,'BA-Desktop-Pet-source/'+p.relative_to(R).as_posix())
    for name in reports:z.write(R/'test-results'/name,'BA-Desktop-Pet-source/validation/'+name)
    for name in ['wave10-typecheck.log','wave10-tests.log']:z.write(R/'test-results'/name,'BA-Desktop-Pet-source/validation/'+name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report={'file':archive.name,'bytes':archive.stat().st_size,'sha256':digest,'modelAssets':'Copy resources/characters from the matching portable package; see docs/BUILD.md.'}
(R/'test-results/wave10-source-package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
