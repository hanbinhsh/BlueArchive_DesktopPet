from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results';S=R/'scripts'
p=(S/'wave14-furniture-preview.mjs').read_text('utf8').replace('size:360','size:600')
p=p.replace('window.petDiagnostics.measurePose=true;','window.petDiagnostics.measurePose=true;window.petDiagnostics.measureFace=true;')
(S/'phone042-preview.mjs').write_text(p,'utf8')
times=[0,.1,1,3,4.6,5.2,6,6.55,6.85,7.5,8.55,9.1,10.1,12.5,13.2,15.3,16.9]
rows=[dict(character='ichika',id='f10206_0',status='ready',times=times,yaw=0),dict(character='ichika',id='f10206_0',status='ready',times=[1,5.2,6.55,8.55,9.1,13.2],yaw=1.5707963267948966)]
rows.extend(dict(character='ichika',id='f10206_0',status='ready',times=[1,5.2,6.55,8.55,9.1,13.2],yaw=yaw)for yaw in [3.141592653589793,4.71238898038469])
(T/'phone042-rows.json').write_text(json.dumps(rows),'utf8')
