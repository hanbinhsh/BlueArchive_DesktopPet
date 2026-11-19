"""Compose review sheets from the packaged application's screenshots."""
import json,math,sys
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parents[1];T=R/'test-results'
specs=json.loads((R/'scripts/roster-wave7.json').read_text(encoding='utf8'))
mode=sys.argv[1] if len(sys.argv)>1 else 'characters'
rows=[]
if mode=='characters':
    rows=[(key,T/f'verified-{key}-idle.png') for key in specs]
else:
    for key in specs:
        c=json.loads((R/f'characters/{key}/character.json').read_text(encoding='utf8'))
        for f in c.get('furniture',[]):
            for phase in ['0','phase0.5','phase0.97']:
                rows.append((f'{key}/{phase}',T/f"furniture-{key}-{f['id']}-{phase}.png"))
columns=5 if mode=='characters' else 3
perpage=20 if mode=='characters' else 15
for start in range(0,len(rows),perpage):
    page=rows[start:start+perpage];width=220 if mode=='characters' else 310
    sheet=Image.new('RGB',(columns*width,math.ceil(len(page)/columns)*270),(44,48,54));draw=ImageDraw.Draw(sheet)
    for i,(label,file) in enumerate(page):
        im=Image.open(file).convert('RGBA');assert im.getbbox(),file
        im=ImageOps.contain(im.crop(im.getbbox()),(width-10,238));x=i%columns*width;y=i//columns*270
        sheet.paste(im,(x+(width-im.width)//2,y+28),im);draw.text((x+4,y+4),label,fill='white')
    sheet.save(T/f'wave7-{mode}-review-{start//perpage}.png')
print(len(rows),'screenshots composed')
