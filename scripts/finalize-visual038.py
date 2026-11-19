"""Record the contact sheets actually reviewed, checking the source frame counts."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'test-results'
counts={'full':(145,725,29),'reported':(44,440,44),'boundary':(20,159,20),'faces':(16,144,8)}
result={'version':'0.2.17','scope':{},'unresolvedObservedDefects':[],
        'limitations':'Key-time samples, not every frame of every animation; game postprocessing/private RNG are not reproduced pixel-for-pixel.'}
for tag,(cases,frames,sheets) in counts.items():
    rows=json.loads((T/f'{tag}038-runtime.json').read_text('utf8'))
    if tag=='faces':
        assert rows['complete']
        rows=rows['results']
    assert len(rows)==cases,(tag,len(rows))
    assert len(list(T.glob(f'{tag}038-*.png')))==frames,tag
    paths=[f'{tag}038-contact-{i:02}.jpg' for i in range(sheets)]
    assert all((T/p).is_file() for p in paths)
    result['scope'][tag]={'cases':cases,'frames':frames,'contactSheetsReviewed':paths}
result['frames']=sum(c[1] for c in counts.values());result['contactSheetsReviewed']=sum(c[2] for c in counts.values())
(T/'visual038-review.json').write_text(json.dumps(result,indent=2),'utf8')
print(result['frames'],result['contactSheetsReviewed'])
