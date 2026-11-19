import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from timeline_visibility import boolean_curves

class TimelineVisibility(unittest.TestCase):
 def test_repeated_idle_and_endpoint_rounding(self):
  metadata=[{'name':'idle','unity_curves':[{'path':'hand/phone','attribute':'m_IsActive','keys':[[0,1],[11.333334,0]]}]},{'name':'action','unity_curves':[{'path':'hand/phone','attribute':'m_IsActive','keys':[[0,0],[16.4,0]]}]}]
  def clip(name,start,duration):return dict(name=name,start=start,duration=duration,clipIn=0,speed=1)
  track={'clips':[clip('action',11.3333333333,16.3333333333),clip('idle',27.6666666666,11.3333333333),clip('idle',0,11.3333333333)]}
  self.assertEqual(boolean_curves(metadata,track)[0]['keys'],[[0,1],[11.3333333333,0],[27.6666666666,1]])
 def test_clip_in_and_speed(self):
  metadata=[{'name':'a','unity_curves':[{'path':'p','attribute':'m_Enabled','keys':[[0,0],[2,1],[4,0],[6,1]]}]}]
  track={'clips':[dict(name='a',start=10,duration=2,clipIn=2,speed=2)]}
  self.assertEqual(boolean_curves(metadata,track)[0]['keys'],[[10,1],[11,0]])
