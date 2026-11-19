"""Fetch just the verified shared-scene texture bundle needed by MX/Water."""
import ast,json,pathlib,sys
# Reuse the existing verified ZIP-range downloader without executing its
# racing/shared-FX selection or concurrent entry point.
path=pathlib.Path('scripts/fetch-racing-furniture.py');tree=ast.parse(path.read_text('utf8'))
keep=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or isinstance(n,ast.FunctionDef) and n.name=='acquire']
namespace={};exec(compile(ast.Module(body=keep,type_ignores=[]),str(path),'exec'),namespace)
work=pathlib.Path('.assets');name='assets-_mx-scenes-_mxcommon-_mxdependency-textures-2025-07-02_assets_all_3101134648.bundle'
namespace.update(WORK=work,BASE='https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/',selected=lambda n:n==name)
catalog=json.loads((work/'catalog.json').read_text('utf8'));pack=next(p for p in catalog['FullPatchPacks'] if any(b['Name']==name for b in p['BundleFiles']))
result=namespace['acquire'](pack);(work/'pool035-acquisition.json').write_text(json.dumps(result,indent=2),'utf8')
