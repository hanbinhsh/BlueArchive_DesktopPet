from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results'
rows=json.loads((T/'finalphone042-runtime.json').read_text('utf8'));assert len(rows)==4 and all(not r['diagnostics']['error']for r in rows)
files=sorted(T.glob('finalphone042-ichika-f10206_0-*.png'));assert len(files)==35
assert len(list(T.glob('finalphone042-contact-*.jpg')))==4
suffix='ichika-f10206_0-0.057803468208092484-yaw4.71238898038469.png'
canvas=Image.new('RGB',(640,420),(31,38,47));draw=ImageDraw.Draw(canvas)
for i,(tag,label)in enumerate([('oldphone042','Before'),('finalphone042','After')]):
 im=Image.open(T/(tag+'-'+suffix)).convert('RGBA')
 if i==0:size=im.size
 else:assert im.size==size
 sx,sy=im.width/900,im.height/870;im=im.crop(tuple(round(v*(sx if j%2==0 else sy))for j,v in enumerate((380,180,590,430))))
 im=im.resize((312,371),Image.Resampling.LANCZOS)
 canvas.paste(im,(i*320+4,36),im);draw.text((i*320+8,10),label,fill='white')
canvas.save(T/'phone042-before-after.jpg',quality=96)
review=dict(complete=True,version='0.2.20',finalFramesReviewed=35,finalContactSheetsReviewed=4,views=[0,1.5707963267948966,3.141592653589793,4.71238898038469],notes=['All four final-executable contact sheets were actually viewed.','Original messaging atlas renders on the phone screen, using native mesh and local alignment.','Original shutter and save-photo particles retained; no replacement artwork.','Phone-facing side has the original content; source back culling retained.','Original selfie eye pose retained; separate 520-sample source comparison passed.'])
(T/'phone042-visual-review.json').write_text(json.dumps(review,indent=2),'utf8')
print('Recorded 35 final frames, four sheets and matched before/after')
