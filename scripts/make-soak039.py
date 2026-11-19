import json
from pathlib import Path
def f(i,t):return {'kind':'furniture','id':i,'mode':'seconds','value':t,'gap':0}
cases=[('wakamo','f3108_0',24),('wakamo_swimsuit','f4201_0',32),('ibuki','f210330_0',58),('ibuki_swimsuit','f211311_0',58),('ibuki_swimsuit','f211311_1',58),('tsurugi_swimsuit','f4302_0',60),('hina_swimsuit','f4301_0',40),('mine','f207310_0',70),('eimi_swimsuit','f210327_0',50),('airi','f5205_0',30),('akane_uniform','f211302_0',30),('ui_swimsuit','f210313_0',44),('yakumo','f210387_0',72)]
Path('test-results/soak039-cases.json').write_text(json.dumps([{'character':c,'steps':[f(i,t)]}for c,i,t in cases],indent=2),'utf8')
