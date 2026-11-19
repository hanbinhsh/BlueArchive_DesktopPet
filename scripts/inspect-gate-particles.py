import pathlib,UnityPy,json
R=pathlib.Path('.');env=UnityPy.load(*[str(p) for p in pathlib.Path('.assets/selected').glob('*.bundle')]);found=[]
def visit(go,path=''):
 path=path+'/'+go.m_Name
 for cp in go.m_Component:
  o=cp.component.deref()
  if o.type.name=='Transform':
   for c in o.read().m_Children:visit(c.read().m_GameObject.read(),path)
  elif o.type.name in ['ParticleSystem','ParticleSystemRenderer']:
   row={'path':path,'type':o.type.name,'data':o.read_typetree()}
   if o.type.name=='ParticleSystemRenderer':
    row['materials']=[]
    for ptr in o.read().m_Materials:
     if ptr.m_PathID:
      m=ptr.read();row['materials'].append({'name':m.m_Name,'data':m.object_reader.read_typetree()});out=pathlib.Path('.assets/gate-fx');out.mkdir(exist_ok=True)
      for k,v in m.m_SavedProperties.m_TexEnvs:
       if v.m_Texture.m_PathID:v.m_Texture.read().image.save(out/(m.m_Name+k+'.png'))
   found.append(row)
for o in env.objects:
 if o.type.name=='GameObject':
  g=o.read()
  if g.m_Name=='my_event090_electronicgate' and any(c.component.deref().type.name=='PlayableDirector' for c in g.m_Component):visit(g)
pathlib.Path('test-results/gate-particle-source.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),'utf8');print([(r['path'],r['type']) for r in found])
