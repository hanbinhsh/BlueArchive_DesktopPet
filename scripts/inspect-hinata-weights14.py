from pathlib import Path
import json,UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
files=[p for p in Path('.assets/selected').glob('*.bundle')if'hinata_original-'in p.name];env=UnityPy.load(*map(str,files));rows=[]
for o in env.objects:
 if o.type.name!='SkinnedMeshRenderer':continue
 r=o.read()
 if not r.m_Mesh.m_PathID:continue
 mesh=r.m_Mesh.read();h=MeshHandler(mesh);h.process()
 if h.m_BoneWeights is None:continue
 used={v for triangles in h.get_triangles()for t in triangles for v in t};bad=[{'vertex':i,'weights':w,'indices':h.m_BoneIndices[i],'used':i in used}for i,w in enumerate(h.m_BoneWeights)if len(w)>4 or abs(sum(w)-1)>=1e-4]
 rows.append(dict(node=r.m_GameObject.read().m_Name,mesh=mesh.m_Name,vertices=len(h.m_Vertices),used=len(used),bad=len(bad),badUsed=sum(x['used']for x in bad),examples=bad[:8]))
Path('test-results/hinata14-weight-source.json').write_text(json.dumps(rows,indent=2),'utf8');print(json.dumps(rows,indent=2))
