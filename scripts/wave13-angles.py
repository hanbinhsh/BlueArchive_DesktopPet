from pathlib import Path
import json,math,sys
from PIL import Image,ImageDraw
T=Path('test-results');R=Path('.assets/expanded-ready');specs=json.loads(Path('scripts/roster-wave13.json').read_text('utf8'))
if '--sheet'not in sys.argv:
 rows=[{'character':k,'id':f['id'],'status':'ready','times':[5],'yaw':yaw}for k in specs for f in json.loads((R/k/'character.json').read_text('utf8')).get('furniture',[])for yaw in [0,math.pi/2,math.pi,math.pi*1.5]]
 (T/'wave13-angles-rows.json').write_text(json.dumps(rows),'utf8')
else:
 rows=json.loads((T/'wave13-angles-rows.json').read_text('utf8'));canvas=Image.new('RGB',(1200,1500),(31,38,47));draw=ImageDraw.Draw(canvas)
 for i,row in enumerate(rows):
  files=[p for p in T.glob(f'wave13-angles-{row["character"]}-{row["id"]}-*.png')if abs((float(p.stem.split('-yaw')[1])if'-yaw'in p.stem else 0)-row['yaw'])<1e-8]
  assert len(files)==1,(row,files)
  im=Image.open(files[0]).convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((294,270));x=i%4*300;y=i//4*300;canvas.paste(im,(x+(300-im.width)//2,y+28),im)
  draw.text((x+2,y+2),f'{row["character"]} {row["id"]} yaw+{row["yaw"]:.2f}',fill='white')
 canvas.save(T/'wave13-angle-options.jpg',quality=94)
