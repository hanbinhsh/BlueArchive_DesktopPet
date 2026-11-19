"""Produce visual QA contact sheets from actual Electron screenshots."""
from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]/'test-results'
rows=sorted(re.match(r'view-(.+)-(f\d+_\d+)-0.png',p.name).groups() for p in root.glob('view-*-0.png'))
for start in range(0,len(rows),8):
    sheet=Image.new('RGB',(880,8*210),(45,48,52));draw=ImageDraw.Draw(sheet)
    for row,(character,scene) in enumerate(rows[start:start+8]):
        for col,angle in enumerate(['0','0.5','1','1.5']):
            file=root/f'view-{character}-{scene}-{angle}.png'
            if not file.exists():continue
            im=Image.open(file).convert('RGBA');im=im.crop(im.getbbox());im=ImageOps.contain(im,(215,185))
            sheet.paste(im,(220*col+(220-im.width)//2,row*210+20),im)
            draw.text((col*220+3,row*210+3),f'{character} {scene} / {angle}',fill='white')
    sheet.save(root/f'furniture-contact-{start//8}.jpg')
print('Contact sheets',len(rows),'scenes')
