import json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
specs=read(R/'scripts/roster-wave9.json')
assert len(read(R/'test-results/wave9-preparation.json'))==10
assert all(r['prepared'] for r in read(R/'test-results/wave9-preparation.json'))
for key in specs:
    src=R/'.assets/expanded-ready'/key;assert (src/'model.glb').is_file() and (src/'thumbnail.png').is_file()
    assert read(src/'character.json')['id']==key
    shutil.copytree(src,R/'characters'/key,dirs_exist_ok=True)
for filename in ['package.json','package-lock.json']:
    p=R/filename;data=read(p);data['version']='0.1.20'
    if 'packages' in data:data['packages']['']['version']='0.1.20'
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
shutil.copy2(R/'.assets/students-wave9-en-2026-10-24.json',R/'.assets/students-audit-2026-10-24.json')
print('Staged 0.1.20 with',len(list((R/'characters').glob('*/character.json'))),'packs')
