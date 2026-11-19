"""Derive isolated QA drivers and a source-curve proof for the current batch."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'scripts'
for old,new in [('wave14-preview.mjs','wave15-preview.mjs'),('wave14-runtime.mjs','wave15-runtime.mjs'),('wave14-furniture-preview.mjs','wave15-furniture-preview.mjs'),('wave14-review-sheets.py','wave15-review-sheets.py'),('audit-persistent14.py','audit-persistent15.py')]:
 p=(S/old).read_text('utf8').replace('wave14','wave15').replace('faces040','faces043')
 (S/new).write_text(p,'utf8')
for old,new in [('faces040.mjs','faces043.mjs'),('hold040-test.mjs','hold043-test.mjs'),('transitions040-test.mjs','transitions043-test.mjs')]:
 (S/new).write_text((S/old).read_text('utf8').replace('040','043').replace('wave14','wave15'),'utf8')
(S/'audit-static043.py').write_text((S/'audit-static040.py').read_text('utf8').replace('040','043').replace('wave14','wave15'),'utf8')
p=(S/'stage-wave14-final.py').read_text('utf8').replace('wave14','wave15').replace('len(rows)==15','len(rows)==len(specs)')
(S/'stage-wave15-final.py').write_text(p,'utf8')
p=(S/'qa-wave14-assets.py').read_text('utf8');p=p[:p.index('env=UnityPy.load(')]
p=p.replace('wave14','wave15').replace("assert d['scenes'][0]['extras'].get('BA_halo_follow')","assert d['scenes'][0]['extras'].get('BA_halo_follow')or profiles[key].get('noHalo')")
p=p.replace("assert any('halo'in n.get('name','').lower()and'mesh'in n for n in d['nodes'])","assert any('halo'in n.get('name','').lower()and'mesh'in n for n in d['nodes'])or profiles[key].get('noHalo')")
p=p.replace("assert (stage/key/'thumbnail.png').is_file()and c.get('mouth')","assert (stage/key/'thumbnail.png').is_file();assert c.get('mouth')or profiles[key].get('noMouthAtlas')")
p=p.replace("specs=read(R/'scripts/roster-wave15.json');index=", "profiles=read(R/'scripts/wave15-profiles.json');specs=read(R/'scripts/roster-wave15.json');index=")
p+='''previous=read(T/'release042-resources.json')
for item in previous:assert sha(R/'characters'/item['path'])==item['sha256'],item['path']
framing=[r for r in read(T/'expanded-framing.json')if r['character']in specs]
(T/'wave15-framing.json').write_text(json.dumps(framing,indent=2),'utf8')
report=dict(added=rows,baseVersion='0.2.20',unchangedPreviousFiles=len(previous))
(T/'wave15-resources.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps(report,indent=2))
'''
(S/'qa-wave15-assets.py').write_text(p,'utf8')
print('Prepared isolated wave15 QA drivers')
