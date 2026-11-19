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
 def test_overlapping_segments_blend_smoothly_for_translation_and_rotation(self):
  source={'nodes':[{'name':'Plate'}],'bufferViews':[],'accessors':[]};raw=bytearray()
  t0=append_accessor(source,raw,[(0.,),(1.,)],'SCALAR')
  p0=append_accessor(source,raw,[(0.,0.,0.),(1.,0.,0.)],'VEC3')
  r0=append_accessor(source,raw,[(0.,0.,0.,1.),(0.,0.,0.,1.)],'VEC4')
  t1=append_accessor(source,raw,[(0.,),(1.,)],'SCALAR')
  p1=append_accessor(source,raw,[(2.,0.,0.),(2.,0.,0.)],'VEC3')
  # 90-degree Z rotation with negated quaternion sign to verify shortest-arc SLERP.
  q90=-math.sin(math.pi/4)
  r1=append_accessor(source,raw,[(0.,0.,q90,q90),(0.,0.,q90,q90)],'VEC4')
  source['animations']=[
   {'name':'seg0','samplers':[{'input':t0,'output':p0,'interpolation':'LINEAR'},{'input':t0,'output':r0,'interpolation':'LINEAR'}],'channels':[{'sampler':0,'target':{'node':0,'path':'translation'}},{'sampler':1,'target':{'node':0,'path':'rotation'}}]},
   {'name':'seg1','samplers':[{'input':t1,'output':p1,'interpolation':'LINEAR'},{'input':t1,'output':r1,'interpolation':'LINEAR'}],'channels':[{'sampler':0,'target':{'node':0,'path':'translation'}},{'sampler':1,'target':{'node':0,'path':'rotation'}}]},
  ]
  dest={'nodes':[{'name':'Plate'}],'bufferViews':[],'accessors':[]};data=bytearray();anim={'channels':[],'samplers':[]}
  track={'clips':[{'name':'seg0','start':0.,'duration':1.2,'clipIn':0.,'speed':1.},{'name':'seg1','start':.6,'duration':1.2,'clipIn':0.,'speed':1.}]}
  namespace['bake'](dest,data,source,raw,track,{0:0},1.8,anim)
  pos_ch=next(c for c in anim['channels'] if c['target']['path']=='translation')
  rot_ch=next(c for c in anim['channels'] if c['target']['path']=='rotation')
  ts=np.array(read_accessor(dest,data,anim['samplers'][pos_ch['sampler']]['input']))[:,0]
  ps=np.array(read_accessor(dest,data,anim['samplers'][pos_ch['sampler']]['output']))
  rs=np.array(read_accessor(dest,data,anim['samplers'][rot_ch['sampler']]['output']))
  i_start=int(np.argmin(np.abs(ts-0.6)))
  i_mid=int(np.argmin(np.abs(ts-0.9)))
  i_end=int(np.argmin(np.abs(ts-1.2)))
  # No hard jump at overlap start (0.6s): still 100% seg0 -> x=0.6, angle=0deg
  self.assertAlmostEqual(ps[i_start][0],0.6,places=5)
  # Midpoint (0.9s = 27/30s): 50% seg0 (x=0.9, 0deg) + 50% seg1 (x=2.0, 90deg) -> x=1.45, angle=45deg
  self.assertAlmostEqual(ps[i_mid][0],1.45,places=5)
  ang_mid=math.degrees(2*math.acos(min(1.,abs(rs[i_mid][3]))))
  self.assertAlmostEqual(ang_mid,45.0,places=3)
  # Overlap end (1.2s): 100% seg1 -> x=2.0, angle=90deg
  self.assertAlmostEqual(ps[i_end][0],2.0,places=5)
  ang_end=math.degrees(2*math.acos(min(1.,abs(rs[i_end][3]))))
  self.assertAlmostEqual(ang_end,90.0,places=3)

if __name__=='__main__':unittest.main()
