"""Restore omitted source renderer flags without replacing geometry or scenes."""
from pathlib import Path
import json, shutil, hashlib
from glb import load, save
root=Path(__file__).resolve().parent.parent
source=json.loads((root/'.assets/cafe-fx/source.json').read_text('utf8'))
nodes={}
def visit(node):
    if node.get('renderer'):nodes[node['path']]=node
    for child in node['children']:visit(child)
for node in source['effects'].values():visit(node)
rows=json.loads((root/'test-results/fx030-installed.json').read_text('utf8'))
report=[]
for row in rows:
    relative=Path(row['character'])/row['model']
    file=root/'characters'/relative
    backup=root/'.assets/pre031'/relative
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copyfile(file,backup)
    doc,binary=load(backup);count=0
    for material in doc['materials']:
        spec=material.get('extras',{}).get('BA_cafeParticle')
        if not spec:continue
        original=nodes[spec['sourceName']]['renderer']
        for key in ['m_ApplyActiveColorSpace','m_VertexStreams','m_UseCustomVertexStreams']:
            spec['renderer'][key]=original[key]
        count+=1
    save(file,doc,binary)
    report.append({'character':row['character'],'model':row['model'],'particles':count,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(root/'test-results/particle-renderer031.json').write_text(json.dumps(report,indent=2),'utf8')
print('Updated',len(report),'models;',sum(r['particles'] for r in report),'particle renderers')
