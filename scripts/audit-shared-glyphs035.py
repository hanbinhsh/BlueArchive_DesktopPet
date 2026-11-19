"""Schedule observed source glyphs at their actual lifetime, not arbitrary frames."""
import pathlib,json,struct,shutil
root=pathlib.Path('.assets/fx035-glyph-test');root.mkdir(exist_ok=True);stage=pathlib.Path('.assets/fx035-stage');rows=[];audit=[]
wanted={'FX_MAT_Img_Lamp_Light_01','FX_MAT_Sweat_Img_01','FX_MAT_Emoticon_Balloon_02'}
for cp in pathlib.Path('characters').glob('*/character.json'):
 folder=stage/cp.parent.name if (stage/cp.parent.name).exists() else cp.parent
 c=json.loads((folder/'character.json').read_text('utf8'));seen=set()
 for f in c.get('furniture',[]):
  if f['model'] in seen:continue
  seen.add(f['model'])
  with (folder/f['model']).open('rb') as h:head=h.read(20);d=json.loads(h.read(struct.unpack_from('<I',head,12)[0]))
  times=set();names=set()
  for m in d['materials']:
   p=m.get('extras',{}).get('BA_cafeParticle',{})
   if p.get('material',{}).get('name') not in wanted:continue
   control=p['control'];life=p['particle']['InitialModule']['startLifetime']['scalar'];delay=p['delay']['scalar'];time=control['start']+((p['burst']+delay+min(life*.5,.5))/p.get('simulationSpeed',1)-control['clipIn'])/control['speed']
   if 0<=time<f['duration'] and time<control['start']+control['duration']:times.add(round(time,4));names.add(p['material']['name'])
  if times:rows.append({'character':cp.parent.name,'id':f['id'],'status':'ready','times':sorted(times)});audit.append({'character':cp.parent.name,'id':f['id'],'materials':sorted(names),'samples':len(times)})
 if any(r['character']==cp.parent.name for r in rows):shutil.copytree(folder,root/cp.parent.name,dirs_exist_ok=True)
pathlib.Path('test-results/glyph035-preview.json').write_text(json.dumps(rows,indent=2),'utf8');pathlib.Path('test-results/glyph035-audit.json').write_text(json.dumps(audit,indent=2),'utf8');print('glyph scenes',len(rows),'samples',sum(r['samples'] for r in audit))
