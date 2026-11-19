"""Read source GLB headers for the relevant wiki entries; no execution of page code."""
import concurrent.futures, hashlib, json, pathlib, struct, urllib.parse
import httpx
R=pathlib.Path(__file__).resolve().parents[1];out=R/'.assets/wiki-model-headers';out.mkdir(exist_ok=True)
rows=json.loads((R/'test-results/wiki-model-scope.json').read_text(encoding='utf8'))
def fetch(item):
    character,model=item;url=model['src'];filename=urllib.parse.unquote(url.rsplit('/',1)[1]);target=out/(filename+'.json')
    if not target.exists():
        for attempt in range(3):
            try:
                with httpx.stream('GET',url,timeout=90,follow_redirects=True) as response:
                    response.raise_for_status();data=bytearray();size=None
                    for chunk in response.iter_bytes(65536):
                        data.extend(chunk)
                        if len(data)>=20:
                            assert data[:4]==b'glTF';size=20+struct.unpack_from('<I',data,12)[0]
                            if len(data)>=size:break
                    doc=json.loads(data[20:size]);target.write_text(json.dumps(doc,separators=(',',':')),encoding='utf8')
                break
            except Exception:
                if attempt==2:raise
    doc=json.loads(target.read_text(encoding='utf8'))
    result={'character':character,'label':model['name'],'filename':filename,'url':url,
            'headerSha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'root':[doc['nodes'][n].get('name') for n in doc['scenes'][0]['nodes']],
            'animations':[a.get('name') for a in doc.get('animations',[])],
            'meshes':[m.get('name') for m in doc.get('meshes',[])]}
    print(filename,len(result['animations']),flush=True);return result
items=[(r['localCharacter'],m) for r in rows for m in r['models']]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(fetch,items))
(R/'test-results/wiki-model-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
