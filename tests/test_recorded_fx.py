import sys,pathlib,unittest,struct,copy,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from unity_recorded import curves,sample
from fx_hierarchy import annotate,reparent,multiply
from static_fx_meshes import attach_static_particles

class RecordedFXTests(unittest.TestCase):
 def test_streamed_cubic_dense_interpolation_and_constant_indices(self):
  raw=struct.pack('<fII4f',0.,1,0,1.,2.,3.,4.)
  data={'m_StreamedClip':{'data':list(struct.unpack('<'+'I'*(len(raw)//4),raw)),'curveCount':2},'m_DenseClip':{'m_CurveCount':1,'m_FrameCount':2,'m_BeginTime':0.,'m_SampleRate':2.,'m_SampleArray':[2.,4.]},'m_ConstantClip':{'data':[7.]}}
  c=curves({'m_MuscleClip':{'m_Clip':{'data':data}}})
  self.assertAlmostEqual(sample(c[0],.5),6.125);self.assertAlmostEqual(sample(c[2],.25),3.);self.assertEqual(sample(c[2],2),4.);self.assertEqual(sample(c[3],100),7.)
 def test_sub_emitter_keeps_original_rotation_after_parent_change(self):
  node=lambda q,children=[]:{'rotation':q,'scale':[1,1,1],'children':children,'position':[0,0,0]}
  parent=node([math.sin(.14),0,0,math.cos(.14)]);child=node([0,0,0,1]);root=node([0,math.sin(.3),0,math.cos(.3)],[parent,child]);annotate(root);expected=child['_worldRotation'];reparent(child,parent)
  self.assertTrue(all(abs(a-b)<1e-6 for a,b in zip(multiply(parent['_worldRotation'],child['rotation']),expected)))
 def test_effect_without_static_mesh_or_particle_is_left_alone(self):
  effect={'children':[]};attach_static_particles(effect,1);self.assertEqual(effect,{'children':[]})

if __name__=='__main__':unittest.main()
