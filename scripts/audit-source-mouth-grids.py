"""Compare all installed mouth grids with cached original material properties."""
import pathlib,json,UnityPy,re
from glb import load
root=pathlib.Path('characters');packs=[json.loads(p.read_text('utf8')) for p in root.glob('*/character.json')]
names={}
for c in packs:
 if not c.get('mouth'):continue
 d,_=load(root/c['id']/c['model'])
 names[c['id']]=list(dict.fromkeys(m['name'] for m in d['materials'] if re.search('eyemout[hn]',m['name'],re.I)))
prefixes={n.lower().rsplit('_',1)[0] for ns in names.values() for n in ns}
prefixes|={p.split('_')[0] for p in prefixes if re.match('(?:ch|np)[0-9]',p)}
files=list({p.name:p for folder in ['selected','costume-audit','costume-variants','r97/selected'] for p in pathlib.Path('.assets',folder).glob('*.bundle') if (any(s in p.name for s in ['-materials-','-material-']) and (p.name.startswith('prolog') or any(s+'-' in p.name for s in prefixes))) or (p.name.startswith('prologdepengroup-assets-_mx-characters-') and any(s+'-' in p.name for s in prefixes))}.values())
files+=list(pathlib.Path('.assets/selected').glob('assets-_mx-field-characters-*-materials-*.bundle'))
env=UnityPy.load(*map(str,files));mats={}
for o in env.objects:
 if o.type.name!='Material':continue
 m=o.read();slots=dict(m.m_SavedProperties.m_TexEnvs)
 if '_MouthTileTex' not in slots or not slots['_MouthTileTex'].m_Texture.m_PathID:continue
 floats=dict(m.m_SavedProperties.m_Floats);mats[m.m_Name.lower()]=[round(floats.get('_MouthTileCols',8)),round(floats.get('_MouthTileRows',8))]
report=[]
for c in packs:
 s=c.get('mouth')
 if not s:continue
 name=s['material'].removesuffix('_Mouth')+'_EyeMouth';original=mats.get(name.lower())
 if original is None:
  alternatives=[(n,mats[n.lower()]) for n in names[c['id']] if n.lower() in mats]
  grids={tuple(v) for n,v in alternatives}
  if len(grids)==1:original=list(next(iter(grids)));name=' / '.join(n for n,v in alternatives)
 report.append({'character':c['id'],'material':name,'installed':[s.get('columns',8),s.get('rows',8)],'original':original})
pathlib.Path('test-results/source-mouth-grids.json').write_text(json.dumps(report,indent=2))
print('Verified',sum(r['original'] is not None for r in report),'of',len(report))
print('Differences',[r for r in report if r['original'] and r['original']!=r['installed']])
print('Unresolved',[r['character'] for r in report if not r['original']])
