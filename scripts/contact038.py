"""Create readable contact sheets from real Electron screenshots."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
tag=sys.argv[1]if len(sys.argv)>1 else'full038'
root=Path('test-results');rows=json.loads((root/f'{tag}-runtime.json').read_text('utf8'))
inputs=json.loads((root/f'{tag}-rows.json').read_text('utf8'))
for row,original in zip(rows,inputs):row['yaw']=original.get('yaw',0)
pages=[]
if tag=='full038':
 for start in range(0,len(rows),5):pages.append(rows[start:start+5])
else:pages=[[r]for r in rows]
for page,group in enumerate(pages):
 files=[]
 for r in group:
  shots=[p for p in root.glob(f'{tag}-{r["character"]}-{r["id"]}-*.png')if abs((float(p.stem.split('-yaw')[1])if'-yaw'in p.stem else 0)-r['yaw'])<1e-8];shots.sort(key=lambda p:float(p.stem.split(r['id']+'-',1)[1].split('-yaw')[0]));files.append((r,shots))
 columns=5;line_count=sum((len(shots)+columns-1)//columns for r,shots in files)
 sheet=Image.new('RGB',(1500,line_count*300),(31,38,47));draw=ImageDraw.Draw(sheet);line=0
 for r,shots in files:
  for i,p in enumerate(shots):
   x=i%columns*300;y=(line+i//columns)*300
   im=Image.open(p).convert('RGBA');bounds=im.getbbox()
   if bounds:im=im.crop(bounds)
   im.thumbnail((296,270));sheet.paste(im,(x+(300-im.width)//2,y+28),im)
   draw.text((x+3,y+3),r['character']+' '+r['id'],fill='white');draw.text((x+3,y+15),p.stem.split(r['id']+'-',1)[1],fill='white')
  line+=(len(shots)+columns-1)//columns
 sheet.save(root/f'{tag}-contact-{page:02}.jpg',quality=93)
print(tag,'contact sheets',len(pages))
