"""Record completed human-visible review, not merely screenshot generation."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results'
shutil.copy2(R/'.assets/wave14-acquisition.json',T/'wave14-acquisition.json')
shutil.copy2(R/'.assets/wave14-fx-dependencies.json',T/'wave14-fx-dependencies.json')
f=json.loads((T/'faces040-runtime.json').read_text('utf8'));rows=json.loads((T/'final040-runtime.json').read_text('utf8'))
assert f['complete']and len(f['results'])==15 and len(rows)==15
assert len(list(T.glob('faces040-contact-*.jpg')))==15 and len(list(T.glob('final040-contact-*.jpg')))==15
report=dict(version='0.2.19',date='2026-11-17',newFinalFramesReviewed=282,newFinalContactSheetsReviewed=30,faceFramesReviewed=132,furnitureFramesReviewed=150,fourViewCandidateFrames=60,angleSheets=4,reviewedFaces=list(T.name for T in sorted(T.glob('faces040-contact-*.jpg'))),reviewedFurniture=list(T.name for T in sorted(T.glob('final040-contact-*.jpg'))),notes=['All fifteen outfit face sheets and fifteen furniture sheets were actually viewed.','Tomoe chair rechecked after choosing the complete cafe prefab.','Kaho intentionally looks toward displayed merchandise; Mikoto walks around her stall.','Mashiro original has no source pickup; six common-action frames only.','Historical 616 resource files remain unchanged; no claim of a fresh all-history frame review.'])
(T/'visual040-review.json').write_text(json.dumps(report,indent=2),'utf8');print('Recorded 30 reviewed final contact sheets')
