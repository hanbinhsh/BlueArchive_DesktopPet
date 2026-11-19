import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];archive=R/'release/BA-Desktop-Pet-0.2.3-source.zip';chosen=[]
for root in ['src','scripts','tests','docs']:chosen.extend(p for p in (R/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
chosen.extend(R/p for p in ['native/WindowWheel.cs','package.json','package-lock.json','tsconfig.json','.gitignore','README.md'])
reports=['wave12-selection.json','wave12-resources.json','wave12-preview.json','wave12-packaged-runtime.json','wave12-packaged-scroll.json','wave12-hold.json','wave12-transitions.json','wave12-expression-source.json','wave12-expressions.json','wave12-package.json','wave12-validation.json','wave12-acquisition.json','wave12-action-expansion.json','wave12-manifests.json','wave12-halo-geometry.json','wave12-framing.json','wave12-framing-runtime.json','wave12-speeds.json','menu-rotation.json','rotation-gestures.json','release-0.2.3.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(set(chosen)):z.write(p,'BA-Desktop-Pet-source/'+p.relative_to(R).as_posix())
 for name in reports:z.write(R/'test-results'/name,'BA-Desktop-Pet-source/validation/'+name)
 for name in ['wave12-typecheck.log','wave12-tests.log','wave12-mouth-tests.log','wave12-framing-dense.log']:z.write(R/'test-results'/name,'BA-Desktop-Pet-source/validation/'+name)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for p in chosen:assert z.read('BA-Desktop-Pet-source/'+p.relative_to(R).as_posix())==p.read_bytes()
with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report={'file':archive.name,'bytes':archive.stat().st_size,'sha256':digest,'modelAssets':'Copy resources/characters from the matching portable package; see docs/BUILD.md.'}
(R/'test-results/wave12-source-package.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
