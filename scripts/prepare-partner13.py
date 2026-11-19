"""Adapt Iroha only as the authored participant in Ibuki's two-person scene."""
import os,sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parents[1]
os.environ.update(BA_ROSTER_SPECS=str(R/'scripts/roster-partner13.json'),BA_CHARACTER_OUTPUT=str(R/'.assets/furniture-partners'),BA_HALO_REPORT='test-results/wave13-partner-halo.json')
os.environ.pop('BA_ROSTER_PROFILES',None)
sys.argv=['prepare-roster.py','iroha_swimsuit'];v=runpy.run_path(str(R/'scripts/prepare-roster.py'))
runpy.run_path(str(R/'scripts/prepare-halo-follow.py'),init_globals={'source_environment':v['env']})
