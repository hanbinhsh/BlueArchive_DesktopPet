import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from nested_fx import window_control

class NestedFXTests(unittest.TestCase):
 def test_outer_speed_clipin_and_clipped_child_preserve_elapsed_time(self):
  root=dict(start=10,duration=20,speed=2,clipIn=4)
  parent=dict(start=12,duration=8,speed=1,clipIn=.03)
  window=dict(start=5,duration=10,speed=.5,clipIn=.2)
  c=window_control(parent,root,window)
  self.assertEqual((c['start'],c['duration'],c['speed']),(12,3.5,1))
  self.assertAlmostEqual(c['clipIn'],1.7)
 def test_activation_uses_director_clock_not_previous_sibling_clock(self):
  root=dict(start=8,duration=30,speed=1,clipIn=0)
  a=window_control(root,root,dict(start=3,duration=20,speed=1,clipIn=.03))
  b=window_control(a,root,dict(start=5,duration=2,speed=1,clipIn=0))
  self.assertEqual((b['start'],b['duration'],b['clipIn']),(13,2,0))
  self.assertEqual(b['propertyClock'],root)
 def test_nonintersecting_window_has_no_geometry(self):
  root=dict(start=0,duration=3,speed=1,clipIn=0)
  self.assertIsNone(window_control(root,root,dict(start=4,duration=1,speed=1,clipIn=0)))

if __name__=='__main__':unittest.main()
