"""Reuse the established end-to-end probes with isolated profiles for the added roles."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];S=R/'scripts';ids=list(json.loads((S/'roster-wave13.json').read_text('utf8')))
text=(S/'faces038.mjs').read_text('utf8').replace('faces038','faces039')
text=re.sub(r'const names=\[.*?\];','const names='+json.dumps(ids)+';',text)
(S/'faces039.mjs').write_text(text,'utf8')
text=(S/'wave12-runtime.mjs').read_text('utf8').replace('wave12','wave13').replace('expanded-runtime-profile','wave13-runtime-profile').replace('test-results/expanded-','test-results/wave13-')
(S/'wave13-runtime.mjs').write_text(text,'utf8')
(S/'transitions039-test.mjs').write_text((S/'transitions038-test.mjs').read_text('utf8').replace('038','039'),'utf8')
(S/'verify-release039.py').write_text((S/'verify-release038.py').read_text('utf8').replace('038','039').replace('0.2.17','0.2.18'),'utf8')
(S/'summarize-soak039.py').write_text((S/'summarize-soak038.py').read_text('utf8').replace('038','039'),'utf8')
