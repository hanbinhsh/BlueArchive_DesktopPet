"""Create review sheets from the final executable's unmodified screenshots."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil
T=Path('test-results');ids=list(json.loads(Path('scripts/roster-wave13.json').read_text('utf8')))
shutil.copy2(T/'wave13-furniture-rows.json',T/'final039-rows.json')
for page in range(2):
 canvas=Image.new('RGB',(1500,900),(31,38,47));draw=ImageDraw.Draw(canvas)
 for n,key in enumerate(ids[page*2:page*2+2]):
  for a,action in enumerate(['idle','interact','pickup']):
   for j,fraction in enumerate([0,.33,.66]):
    im=Image.open(T/f'faces039-{key}-{action}-{fraction}.png').convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((242,265));x=(n*3+j)*250;y=a*300;canvas.paste(im,(x+(250-im.width)//2,y+25),im);draw.text((x+2,y+2),f'{key} {action} {fraction}',fill='white')
 canvas.save(T/f'faces039-contact-{page:02}.jpg',quality=94)
