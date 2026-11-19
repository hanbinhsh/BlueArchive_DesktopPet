import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compressed_skin import decode_packed_skin

class PackedSkinTest(unittest.TestCase):
    def test_implied_fourth_influence_uses_same_quantized_unit(self):
        weights,indices=decode_packed_skin([14,7,5],[35,34,32,36],1)
        self.assertEqual(weights,[(14/31,7/31,5/31,5/31)])
        self.assertEqual(indices,[(35,34,32,36)])
        self.assertAlmostEqual(sum(weights[0]),1)
    def test_variable_influence_counts_keep_vertex_boundaries(self):
        weights,indices=decode_packed_skin([31,20,11,10,10,11],[9,1,2,3,4,5],3)
        self.assertEqual(indices,[(9,0,0,0),(1,2,0,0),(3,4,5,0)])
        self.assertTrue(all(abs(sum(w)-1)<1e-12 for w in weights))
    def test_truncated_or_overweight_streams_are_rejected(self):
        for weights,bones,count in [([14,7,5],[1,2,3],1),([20,20],[1,2],1),([10],[1],1)]:
            with self.assertRaises(ValueError):decode_packed_skin(weights,bones,count)

if __name__=='__main__':unittest.main()
