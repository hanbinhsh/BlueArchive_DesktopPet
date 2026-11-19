"""Create isolated wave15 tooling while preserving all completed release inputs."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'scripts'
names=['select-wave14.py','inspect-wave14-source.py','prepare-wave14.py','export-wave14-complete.py','index-wave14-sources.py','index-furniture-wave14.py','merge-furniture-wave14.py']
for name in names:
 target=S/name.replace('wave14','wave15');assert not target.exists(),target
 text=(S/name).read_text('utf8').replace('wave14','wave15')
 target.write_text(text,'utf8')
print('Created',len(names),'batch-specific scripts')
