"""Create labelled QA contact sheets from the existing regression captures."""
from PIL import Image,ImageDraw
from pathlib import Path
import json,sys
prefix=sys.argv[1] if len(sys.argv)>1 else 'sweep032g'
rows=json.loads(Path(sys.argv[2] if len(sys.argv)>2 else 'test-results/sweep032g-rows.json').read_text('utf8'))
ready=[r for r in rows if Path(f'test-results/{prefix}-{r["character"]}-{r["id"]}-0.9.png').exists()]
for start in range(0,len(ready),8):
    group=ready[start:start+8];sheet=Image.new('RGB',(1250,240*len(group)),(31,38,47));draw=ImageDraw.Draw(sheet)
    for y,row in enumerate(group):
        for x,fraction in enumerate([.1,.3,.5,.7,.9]):
            path=Path(f'test-results/{prefix}-{row["character"]}-{row["id"]}-{fraction}.png')
            im=Image.open(path).convert('RGBA');im.thumbnail((245,210))
            sheet.paste(im,(x*250+(250-im.width)//2,y*240+25),im)
            draw.text((x*250+3,y*240+3),f'{row["character"]} {row["id"]} {fraction}',fill='white')
    sheet.save(f'test-results/{prefix}-contact-{start//8:02d}.jpg')
print('Contact rows:',len(ready))
