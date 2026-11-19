import pathlib,sys,json
p=pathlib.Path(__file__).with_name('prepare-furniture.py')
sys.argv=[str(p),'kokona','shun_swimsuit']
exec(compile(p.read_text(encoding='utf8').split('results=[];bychar={}')[0],str(p),'exec'))
report=[]
for profile in profiles:
    doc,data=exported(profile['icon'])
    originals={n:r for n,r,_ in renderers(prefab(profile['icon']))}
    report.append({'character':profile['character'],
      'candidates':[{'file':go.object_reader.assets_file.parent.name,'renderers':[n for n,r,v in renderers(go)]} for go in gameobjects[profile['icon']]],
      'source':{n:[m.read().m_Name for m in r.m_Materials] for n,r in originals.items()},
      'export':[{'node':n['name'],'materials':[doc['materials'][pr['material']]['name'] for pr in doc['meshes'][n['mesh']]['primitives']]} for n in doc['nodes'] if 'mesh' in n]})
(R/'test-results/wave7-furniture-diagnostic.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
