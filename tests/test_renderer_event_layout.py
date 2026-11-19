import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from renderer_event_layout import renderer_event_layout
from visibility import attach_visibility

class FaceLayoutTests(unittest.TestCase):
 def test_original_face_events_remain_exclusive_and_never_toggle_halo(self):
  for character,a,b,names in [('chiaki',7,8,['CH0238_Face01','CH0238_Face02','CH0238_Halo']),('juri_parttime',6,7,['CH0286_Face_Outline','CH0286_Face01_Outline','CH0286_Halo'])]:
   with self.subTest(character=character):
    events=[dict(time=0,function='AniEvt_EnableChildRenderer',int=a),dict(time=0,function='AniEvt_DisableChildRenderer',int=b),dict(time=2,function='AniEvt_DisableChildRenderer',int=a),dict(time=2,function='AniEvt_EnableChildRenderer',int=b)]
    doc={'nodes':[{'name':n}for n in names],'scenes':[{'extras':{'BAAD_unity_animation':{'clips':[{'name':'original','track':'held','events':events}]}}}]}
    attach_visibility(doc,renderer_event_layout(character,['unused']*(b+1)))
    tracks=doc['scenes'][0]['extras']['BA_pet_visibility']['clips']['held'];self.assertEqual({t['node']for t in tracks},{0,1})
    for time in [0,1.9,2,4]:
     visible={t['node']:next(value for at,value in reversed(t['keys'])if at<=time)for t in tracks};self.assertEqual(sum(visible.values()),1)
     self.assertEqual(visible[0],time<2)

if __name__=='__main__':unittest.main()
