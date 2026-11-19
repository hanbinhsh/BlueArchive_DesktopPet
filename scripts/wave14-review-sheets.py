"""Build contact sheets for ten new students without modifying screenshots."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,math,sys
T=Path('test-results');R=Path('.assets/wave14-final');specs=json.loads(Path('scripts/roster-wave14.json').read_text('utf8'))
mode=sys.argv[1]
if mode=='angles':
 rows=[dict(character=k,id=f['id'],status='ready',times=[min(5,f['duration']/3)],yaw=yaw)for k in specs for f in json.loads((R/k/'character.json').read_text('utf8')).get('furniture',[])for yaw in [0,math.pi/2,math.pi,math.pi*1.5]]
 (T/'wave14-angles-rows.json').write_text(json.dumps(rows),'utf8')
elif mode=='angle-sheets':
 rows=json.loads((T/'wave14-angles-rows.json').read_text('utf8'))
 for page,start in enumerate(range(0,len(rows),16)):
  group=rows[start:start+16];canvas=Image.new('RGB',(1200,math.ceil(len(group)/4)*300),(31,38,47));draw=ImageDraw.Draw(canvas)
  for i,row in enumerate(group):
   files=[p for p in T.glob(f'wave14-angles-{row["character"]}-{row["id"]}-*.png')if abs((float(p.stem.split('-yaw')[1])if'-yaw'in p.stem else 0)-row['yaw'])<1e-8];assert len(files)==1
   im=Image.open(files[0]).convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((294,270));x=i%4*300;y=i//4*300;canvas.paste(im,(x+(300-im.width)//2,y+28),im);draw.text((x+2,y+2),f'{row["character"]} {row["id"]} yaw+{row["yaw"]:.2f}',fill='white')
  canvas.save(T/f'wave14-angle-options-{page:02}.jpg',quality=94)
elif mode=='faces':
 for page,k in enumerate(specs):
  paths=list(T.glob(f'faces040-{k}-*.png'));canvas=Image.new('RGB',(900,900),(31,38,47));draw=ImageDraw.Draw(canvas)
  for a,action in enumerate(['idle','interact','pickup']):
   for j,fraction in enumerate([0,.33,.66]):
    p=T/f'faces040-{k}-{action}-{fraction}.png'
    if not p.exists():continue
    im=Image.open(p).convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((294,270));x=j*300;y=a*300;canvas.paste(im,(x+(300-im.width)//2,y+25),im);draw.text((x+2,y+2),f'{k} {action} {fraction}',fill='white')
  canvas.save(T/f'faces040-contact-{page:02}.jpg',quality=94)
