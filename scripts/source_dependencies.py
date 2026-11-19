"""Resolve missing Unity CABs only from verified archives already cached locally."""
import json,pathlib,re,zipfile

def load_cached_dependency(env,error):
    if 'unity default resources' in str(error):
        path=pathlib.Path('.assets/jp/windows/.state/runtime/1.73.459696/Package/Extracted/assets/bin/Data/unity default resources')
        if path.exists():env.load_file(str(path));return
    match=re.search(r'cab-[a-f0-9]+',str(error))
    if not match:raise error
    index=json.loads(pathlib.Path('.assets/cab-index.json').read_text('utf8'))['cabs']
    # CAB names can survive a patch while their object tables change. Prefer
    # the active catalog's verified archive over a cross-version local cache.
    if match[0] in index:
        pack,name=index[match[0]]
        target=pathlib.Path('.assets/selected')/name
        archive=pathlib.Path('.assets/packs')/pack
        if target.exists() or archive.exists():
            if not target.exists():
                with zipfile.ZipFile(archive) as source:target.write_bytes(source.read(name))
            env.load_file(str(target));return
    local=pathlib.Path('.assets/local-cab-index.json')
    if local.exists():
        candidate=json.loads(local.read_text())['cabs'].get(match[0])
        if candidate:env.load_file(candidate);return
    if match[0] not in index:raise error
    pack,name=index[match[0]]
    target=pathlib.Path('.assets/selected')/name
    if not target.exists():
        with zipfile.ZipFile(pathlib.Path('.assets/packs')/pack) as archive:target.write_bytes(archive.read(name))
    env.load_file(str(target))

def resolve_cached(env,operation):
    for _ in range(32):
        try:return operation()
        except FileNotFoundError as error:load_cached_dependency(env,error)
    raise RuntimeError('Dependency resolution exceeded 32 cached CABs')
