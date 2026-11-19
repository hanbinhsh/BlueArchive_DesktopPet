import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for name in ['package.json','package-lock.json']:
    p=R/name;d=json.loads(p.read_text(encoding='utf8'));assert d['version']=='0.1.20'
    d['version']='0.1.21'
    if name=='package-lock.json':d['packages']['']['version']='0.1.21'
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
p=R/'README.md';s=p.read_text(encoding='utf8');first,rest=s.split('\n',1)
p.write_text(first+'\n\n## 0.1.21 动作面板滚动修复\n\n修复点击动作后右侧面板跳回顶部的问题。播放时保留现有动作按钮；收藏重排和状态更新保持滚动位置。角色与资源沿用 0.1.20 的 47 位角色、110 套外观及 2,700 个动作。\n'+rest.replace('BA-Desktop-Pet-0.1.20-win-x64.zip','BA-Desktop-Pet-0.1.21-win-x64.zip'),encoding='utf8')
print('Prepared 0.1.21 version and release notes')
