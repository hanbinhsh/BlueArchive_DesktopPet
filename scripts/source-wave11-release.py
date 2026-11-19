import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];archive=R/'release/BA-Desktop-Pet-0.2.2-source.zip'
chosen=[]
for root in ['src','scripts','tests','docs']:
    chosen.extend(p for p in (R/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
chosen.extend(R/p for p in ['native/WindowWheel.cs','package.json','package-lock.json','tsconfig.json','.gitignore','README.md'])
reports=['wave11-selection.json','wave11-resources.json','wave11-preview.json','wave11-library.json','wave11-packaged-runtime.json','wave11-packaged-scroll.json','wave11-hold.json','wave11-transitions.json','wave11-expression-source.json','wave11-expressions.json','wave11-package.json','wave11-validation.json','wave11-acquisition.json','wave11-action-expansion.json','wave11-controls-suite.json','wave11-concurrent-hold-rumi-trace.json','wave11-interrupted-hasumi-track-trace.json','wave11-manifests.json','wave11-hasumi-mouth-source.json','wave11-halo-geometry.json','release-0.2.2.json']
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(chosen)):z.write(p,'BA-Desktop-Pet-source/'+p.relative_to(R).as_posix())
    for name in reports:z.write(R/'test-results'/name,'BA-Desktop-Pet-source/validation/'+name)
    for name in ['wave11-typecheck.log','wave11-tests.log','wave11-mouth-tests.log','wave11-concurrent-controls.log','wave11-second-controls.log']:z.write(R/'test-results'/name,'BA-Desktop-Pet-source/validation/'+name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report={'file':archive.name,'bytes':archive.stat().st_size,'sha256':digest,'modelAssets':'Copy resources/characters from the matching portable package; see docs/BUILD.md.'}
(R/'test-results/wave11-source-package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
