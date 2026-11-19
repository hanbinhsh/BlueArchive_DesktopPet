import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from particle_emission import emission_times,burst_times,limit_births


class EmissionTests(unittest.TestCase):
    def test_zero_cycles_repeat_until_system_duration(self):
        burst={'time':0.,'repeatInterval':0.03999999910593033,'cycleCount':0}
        births=burst_times(burst,1.)
        self.assertEqual(len(births),25)
        self.assertEqual(births[0],0)
        self.assertAlmostEqual(births[-1],.96,places=6)

    def test_finite_cycles_and_delayed_burst(self):
        self.assertEqual(burst_times({'time':.2,'repeatInterval':.25,'cycleCount':3},1),[.2,.45,.7])
        self.assertEqual(burst_times({'time':2,'repeatInterval':.25,'cycleCount':0},1),[])
        self.assertEqual(len(burst_times({'time':0,'repeatInterval':.1,'cycleCount':0},10)),100)

    def test_indefinite_zero_interval_is_rejected(self):
        with self.assertRaises(ValueError):burst_times({'time':0,'repeatInterval':0,'cycleCount':0},1)

    def test_one_slot_equalizer_does_not_spawn_hundreds_of_overlapping_sprites(self):
        rows=[(n*.01,0,1,n) for n in range(601)]
        initial={'maxNumParticles':1,'startLifetime':{'minMaxState':0,'scalar':3}}
        self.assertEqual([r[0] for r in limit_births(rows,initial,{'scalar':0})],[0,3,6])

    def test_capacity_is_released_on_death_and_uses_actual_delay(self):
        rows=[(.1,0,1,1),(0,0,1,2),(.2,0,1,3)]
        initial={'maxNumParticles':2,'startLifetime':{'scalar':.15}}
        self.assertEqual([r[0] for r in limit_births(rows,initial,{'scalar':1})],[0,.1,.2])

    def test_constant_rate_keeps_previous_schedule(self):
        self.assertEqual(emission_times({'scalar': 4, 'minMaxState': 0}, 0, 1, 1), [.25, .5, .75])
        self.assertEqual(emission_times({'scalar': 4, 'minMaxState': 0}, -1, 1, 1), [-.75, -.5, -.25, 0, .25, .5, .75])

    def test_ramp_uses_integrated_rate_not_uniform_spacing(self):
        curve = {'scalar': 20, 'minMaxState': 1, 'maxCurve': {'m_Curve': [
            {'time': 0, 'value': 0, 'inSlope': 1, 'outSlope': 1},
            {'time': 1, 'value': 1, 'inSlope': 1, 'outSlope': 1},
        ]}}
        births = emission_times(curve, 0, 1, 1)
        for i, time in enumerate(births):
            self.assertAlmostEqual(time, math.sqrt((i+1)/10), delta=1/240)
        self.assertTrue(all(a < b for a, b in zip(births, births[1:])))
        self.assertEqual(births, emission_times(curve, 0, 1, 1))

    def test_zero_rate_does_not_emit(self):
        self.assertEqual(emission_times({'scalar': 0, 'minMaxState': 0}, 0, 10, 1), [])

    def test_random_rate_uses_seeded_integrated_samples_not_one_fixed_interval(self):
        c={'minMaxState':3,'minScalar':.85,'scalar':.35}
        with self.assertRaises(ValueError):emission_times(c,0,30,30)
        a=emission_times(c,0,30,30,seed=123)
        self.assertEqual(a,emission_times(c,0,30,30,seed=123))
        self.assertNotEqual(a,emission_times(c,0,30,30,seed=124))
        self.assertTrue(17<=len(a)<=19) # Native Unity probe emits 17–18 over 30 s.
        intervals=[b-a for a,b in zip(a,a[1:])]
        self.assertGreater(max(intervals)-min(intervals),.01)
        self.assertTrue(all(1/.85<=v<=1/.35 for v in intervals))


if __name__ == '__main__':
    unittest.main()
