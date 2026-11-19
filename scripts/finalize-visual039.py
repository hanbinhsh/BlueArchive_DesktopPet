"""Retain the review scope without counting preliminary angle trials as final tests."""
import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'test-results'
assert len(list(T.glob('final039-*.png')))==50 and len(list(T.glob('faces039-*.png')))==36
assert len(list(T.glob('final039-contact-*.jpg')))==5 and len(list(T.glob('faces039-contact-*.jpg')))==2
assert json.loads((T/'wave13-packaged-runtime.json').read_text('utf8'))['complete']
record={'version':'0.2.18','newFinalFramesReviewed':86,'newFinalContactSheetsReviewed':7,'previousReview':'visual038-review.json','previousFramesReviewed':1468,'previousContactSheetsReviewed':101,'angleTrialsReviewed':20,'note':'Final seven contact sheets individually reviewed. Prior 599 resources and 15 runtime files are identical to the completed 0.2.17 audit. The first held-drag attempt was interrupted by extra input; the offscreen, nonfocusable rerun passed all four outfits.'}
(T/'visual039-review.json').write_text(json.dumps(record,indent=2),'utf8')
for n in ['wave13-acquisition.json','wave13-partner-acquisition.json']:shutil.copy2(R/'.assets'/n,T/n)
print('Recorded 86 final frames / 7 sheets, with separate historical evidence')
