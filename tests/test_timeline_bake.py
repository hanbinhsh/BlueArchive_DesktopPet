"""Exercise the bake functions without loading the entire official asset corpus."""
import ast, pathlib, math, unittest, sys
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from glb import append_accessor,read_accessor
tree=ast.parse((R/'scripts/prepare-furniture.py').read_text('utf8'))
code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['bake','interpolate']],type_ignores=[])
namespace={'np':np,'math':math,'append_accessor':append_accessor,'read_accessor':read_accessor}
exec(compile(code,'prepare-furniture.py','exec'),namespace)

class TimelineTests(unittest.TestCase):
 def test_late_clip_holds_first_authored_pose_instead_of_bind_pose(self):
  source={'nodes':[{'name':'Body'}],'bufferViews':[],'accessors':[]};raw=bytearray()
  ti=append_accessor(source,raw,[(0,),(1,)],'SCALAR')
  vi=append_accessor(source,raw,[(0,0,0),(2,0,0)],'VEC3')
  source['animations']=[{'name':'lie','samplers':[{'input':ti,'output':vi,'interpolation':'LINEAR'}],'channels':[{'sampler':0,'target':{'node':0,'path':'translation'}}]}]
  dest={'nodes':[{'name':'Body','translation':[0,3,0]}],'bufferViews':[],'accessors':[]};data=bytearray();anim={'channels':[],'samplers':[]}
  track={'clips':[{'name':'lie','start':1/30,'duration':1,'clipIn':.25,'speed':.5}]}
  namespace['bake'](dest,data,source,raw,track,{0:0},1+1/30,anim)
  sampler=anim['samplers'][0];values=read_accessor(dest,data,sampler['output'])
  self.assertAlmostEqual(values[0][0],.5);self.assertEqual(values[0],values[1])
  self.assertAlmostEqual(values[-1][0],1.5)
 def test_zero_start_keeps_authored_pose(self):
  actual=namespace['interpolate'](np.array([0.,1.]),np.array([[1.,2.,3.],[3.,4.,5.]]),np.array([0.,.5,1.]),'LINEAR',False)
  np.testing.assert_allclose(actual,[[1,2,3],[2,3,4],[3,4,5]])

if __name__=='__main__':unittest.main()
