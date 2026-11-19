import json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1]
ids=list(json.loads((R/'scripts/roster-wave10.json').read_text(encoding='utf8')))
actions=['idle','interact','pickup','original_exs','original_formation_idle']
canvas=Image.new('RGB',(1200,len(ids)*240),'#36414c');draw=ImageDraw.Draw(canvas)
for row,key in enumerate(ids):
    for col,action in enumerate(actions):
        x,y=col*240,row*240
        draw.text((x+5,y+5),key,fill='white');draw.text((x+5,y+22),action,fill='white')
        p=R/f'test-results/expanded-{key}-{action}.png'
        if not p.exists():continue
        im=Image.open(p).convert('RGBA');im.thumbnail((235,202))
        canvas.paste(im,(x+(240-im.width)//2,y+37),im)
canvas.save(R/'test-results/wave10-runtime-contact.png')
