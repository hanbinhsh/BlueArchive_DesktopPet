import pathlib,json,UnityPy,re,zipfile
from UnityPy.helpers.MeshHelper import MeshHandler
R=pathlib.Path('.');e=UnityPy.load(*[str(p) for p in (R/'.assets/selected').glob('*.bundle') if any(k in p.name for k in ['electronicgate','effectsfreezed','unitybuiltinshaders','ch0307','en0014_original'])]);out=[];dest=R/'.assets/gate-fx';dest.mkdir(exist_ok=True)
def visit(go,path):
 row={'name':go.m_Name,'path':path+'/'+go.m_Name,'active':go.m_IsActive};parts={c.component.deref().type.name:c.component.deref() for c in go.m_Component};t=parts['Transform'].read();row['position']=[t.m_LocalPosition.x,t.m_LocalPosition.y,t.m_LocalPosition.z];row['rotation']=[t.m_LocalRotation.x,t.m_LocalRotation.y,t.m_LocalRotation.z,t.m_LocalRotation.w];row['scale']=[t.m_LocalScale.x,t.m_LocalScale.y,t.m_LocalScale.z]
 if 'ParticleSystem' in parts:row['particle']=parts['ParticleSystem'].read_typetree()
 if 'ParticleSystemRenderer' in parts:
  r=parts['ParticleSystemRenderer'].read();row['renderer']=parts['ParticleSystemRenderer'].read_typetree();row['materials']=[]
  if r.m_Mesh.m_PathID:
   h=MeshHandler(r.m_Mesh.read());h.process();row['mesh']={'name':r.m_Mesh.read().m_Name,'positions':h.m_Vertices,'uv':h.m_UV0,'triangles':h.get_triangles()}
  for ptr in r.m_Materials:
   if not ptr.m_PathID:continue
   
   try:m=ptr.read()
   except FileNotFoundError as error:
    row.setdefault('missingMaterials',[]).append(str(error));print('MISSING_MATERIAL',go.m_Name,str(error),flush=True);continue
   v={'name':m.m_Name,'colors':{k:[x.r,x.g,x.b,x.a] for k,x in m.m_SavedProperties.m_Colors},'floats':dict(m.m_SavedProperties.m_Floats),'textures':[]}
   for k,tex in m.m_SavedProperties.m_TexEnvs:
    if not tex.m_Texture.m_PathID:continue
    
    try:texture=tex.m_Texture.read()
    except FileNotFoundError as error:
     print('MISSING_TEXTURE',m.m_Name,k,str(error),flush=True);v['textures'].append({'slot':k,'missing':str(error),'pathID':tex.m_Texture.m_PathID});continue
    file=m.m_Name+k+'.png';texture.image.save(dest/file);v['textures'].append({'slot':k,'file':file,'name':texture.m_Name,'scale':[tex.m_Scale.x,tex.m_Scale.y],'offset':[tex.m_Offset.x,tex.m_Offset.y]})
   row['materials'].append(v)
 row['children']=[visit(c.read().m_GameObject.read(),row['path']) for c in t.m_Children];return row
cab_index=json.loads((R/'.assets/cab-index.json').read_text('utf8'))['cabs']
for attempt in range(12):
 try:
  out=[]
  for o in list(e.objects):
   if o.type.name=='GameObject' and o.read().m_Name in ['FX_my_event090_electronicgate_HUD_01','FX_my_event090_electronicgate_idle_01']:out.append(visit(o.read(),''))
  break
 except FileNotFoundError as error:
  match=re.search(r'cab-[a-f0-9]+',str(error))
  if not match or match[0] not in cab_index:raise
  pack,name=cab_index[match[0]];raw=zipfile.ZipFile(R/'.assets/packs'/pack).read(name);target=R/'.assets/selected'/name;target.write_bytes(raw);e.load_file(str(target));print('Dependency',name,flush=True)
else:raise RuntimeError('Too many missing source dependencies')
(dest/'source.json').write_text(json.dumps(out,indent=2),'utf8');print('exported',len(out))
