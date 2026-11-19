from pathlib import Path
from PIL import Image,ImageDraw
import json
T=Path('test-results');data=json.loads((T/'ichika041-runtime.json').read_text('utf8'))
for row in data['results']:
 for action in row['actions'][:3]:
  canvas=Image.new('RGB',(1200,600),(31,38,47));draw=ImageDraw.Draw(canvas)
  for i,frame in enumerate(action['frames']):
   im=Image.open(T/frame['file']).convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((195,270));x=i%6*200;y=i//6*300;canvas.paste(im,(x+(200-im.width)//2,y+24),im);draw.text((x+2,y+2),f"{row['character']} {action['id']} {frame['time']:.2f}s",fill='white')
  canvas.save(T/f"ichika041-{row['character']}-{action['id']}-contact.jpg",quality=95)
