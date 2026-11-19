"""Review all final scene views without hiding their relative on-screen sizes."""
from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]/'test-results'
rows=json.loads((root/'furniture-runtime.json').read_text())
for start in range(0,len(rows),16):
    sheet=Image.new('RGB',(1000,4*270),(45,48,52));draw=ImageDraw.Draw(sheet)
    for i,item in enumerate(rows[start:start+16]):
        character,scene=item['character'],item['furniture']
        file=root/f'furniture-{character}-{scene}-0.png'
        im=Image.open(file).convert('RGBA');im=ImageOps.contain(im,(250,250))
        x,y=(i%4)*250,(i//4)*270
        sheet.paste(im,(x,y+18),im);draw.text((x+2,y+2),f'{character} {scene}',fill='white')
    sheet.save(root/f'furniture-final-contact-{start//16}.jpg')
print('Final contact sheets',len(rows),'interactions')
