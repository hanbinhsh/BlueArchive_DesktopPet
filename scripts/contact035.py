"""Contact sheets from actual packaged regression screenshots (no image editing of assets)."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

root=Path('test-results')
rows=json.loads((root/'packaged035-runtime.json').read_text('utf8'))
for start in range(0,len(rows),10):
    batch=rows[start:start+10]
    sheet=Image.new('RGB',(1500,300*((len(batch)+1)//2)),(31,38,47));draw=ImageDraw.Draw(sheet)
    for n,row in enumerate(batch):
        files=list(root.glob(f'packaged035-{row["character"]}-{row["id"]}-*.png'))
        files.sort(key=lambda p:float(p.stem.rsplit('-',1)[-1]))
        assert len(files)==3,(row['character'],row['id'],len(files))
        for k,file in enumerate(files):
            x=(n%2*3+k)*250;y=n//2*300
            im=Image.open(file).convert('RGBA');box=im.getbbox()
            if box:im=im.crop(box)
            im.thumbnail((246,270));sheet.paste(im,(x+(250-im.width)//2,y+28),im)
            draw.text((x+3,y+3),f'{row["character"]} {file.stem.rsplit("-",1)[-1]}',fill='white')
            draw.text((x+3,y+14),row['id'],fill='white')
    sheet.save(root/f'packaged035-contact-{start//10:02}.jpg',quality=91)
print('Created', (len(rows)+9)//10,'full traversal contact sheets')
