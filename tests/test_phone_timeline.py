import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phone_timeline import phone_controls

class PhoneTimelineTests(unittest.TestCase):
 def test_repeated_idle_restarts_without_extending_into_other_action(self):
  name='Phone_01'
  metadata=[{'name':'idle','unity_curves':[{'path':'rig/'+name,'attribute':'m_IsActive','keys':[[0,1],[11.333334,0]]}]}]
  track={'clips':[{'name':'idle','start':t,'duration':11.333333333333334,'clipIn':0,'speed':1} for t in [0,27.66666666666667,39.00000000000002]]}
  rows=phone_controls(metadata,track,'group',[name])
  self.assertEqual(len(rows),3)
  self.assertEqual([r['start'] for r in rows],[s['start'] for s in track['clips']])
  self.assertTrue(all(r['existing'] and r['restartOnActivation'] and r['clipIn']==0 for r in rows))
  for r in rows:self.assertAlmostEqual(r['duration'],11.333333333333334)
 def test_delayed_enable_keeps_original_interval(self):
  metadata=[{'name':'action','unity_curves':[{'path':'Phone_02','attribute':'m_IsActive','keys':[[0,0],[2,1],[5,0]]}]}]
  track={'clips':[{'name':'action','start':10,'duration':8,'clipIn':0,'speed':1}]}
  rows=phone_controls(metadata,track,'group',['Phone_02'])
  self.assertEqual([(r['start'],r['duration']) for r in rows],[(12,3)])

if __name__=='__main__':unittest.main()
