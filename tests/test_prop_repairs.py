import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prop_materials import adapt_prop_material
from prop_visibility import apply_prop_visibility


class PropRepairsTests(unittest.TestCase):
    def test_karin_glass_and_shigure_fruitbar_materials(self):
        karin_glass = {'name': 'CH0100_Table_02', 'alphaMode': 'BLEND', 'doubleSided': True, 'pbrMetallicRoughness': {}}
        adapt_prop_material(karin_glass)
        self.assertEqual(karin_glass['alphaMode'], 'BLEND')
        self.assertFalse(karin_glass['doubleSided'])
        self.assertAlmostEqual(karin_glass['pbrMetallicRoughness']['baseColorFactor'][3], 0.30, places=3)
        self.assertFalse(karin_glass['extras']['BA_depthWrite'])

        cup_wall = {'name': 'my_seahouse_01_tableitems _a', 'alphaMode': 'MASK', 'alphaCutoff': 0.5, 'pbrMetallicRoughness': {}}
        adapt_prop_material(cup_wall)
        self.assertEqual(cup_wall['alphaMode'], 'BLEND')
        self.assertNotIn('alphaCutoff', cup_wall)
        self.assertAlmostEqual(cup_wall['pbrMetallicRoughness']['baseColorFactor'][3], 0.35686275, places=5)
        self.assertFalse(cup_wall['extras']['BA_depthWrite'])

        cup_body = {'name': 'my_seahouse_01_tableitems', 'alphaMode': 'MASK', 'alphaCutoff': 0.5, 'pbrMetallicRoughness': {}}
        adapt_prop_material(cup_body)
        self.assertEqual(cup_body['alphaMode'], 'OPAQUE')
        self.assertNotIn('alphaCutoff', cup_body)

    def test_sandart_step_mask_marks_srgb(self):
        mat = {
            'name': 'cafe_particle_42',
            'pbrMetallicRoughness': {},
            'extras': {
                'BA_cafeParticle': {'texture': {'name': 'FX_TEX_CH0347_Sandart'}},
                'BA_smokeFx': {'kind': 'step', 'maskTexture': {'index': 25, 'st': [1, 1, 0, 0]}},
            },
        }
        adapt_prop_material(mat)
        self.assertTrue(mat['extras']['BA_smokeFx']['maskTexture']['srgb'])

    def test_shigure_onsen_visibility_hides_cutin_body_and_deck_duck_ripples(self):
        doc = {
            'nodes': [
                {'name': 'CH0123_CutIn_Body', 'mesh': 0},
                {'name': 'CH0123_Body', 'mesh': 1},
                {'name': 'CH0123_Prop', 'mesh': 3},
                {'name': 'furniture_16_FX_my_hotsprings_woodenbathtub_duck_02_Bubble', 'mesh': 2},
                {'name': 'furniture_18_FX_my_hotsprings_woodenbathtub_duck_01_Bubble'},
            ],
            'scenes': [{'extras': {'BA_pet_visibility': {'defaults': {'0': True, '1': True, '2': False, '3': True}}}}],
        }
        apply_prop_visibility(doc, 'shigure_onsen', 'my_hotsprings_01_woodenbathtub_CH0123')
        defaults = doc['scenes'][0]['extras']['BA_pet_visibility']['defaults']
        self.assertFalse(defaults['0'])
        self.assertTrue(defaults['1'])
        self.assertTrue(defaults['2'])
        self.assertFalse(defaults['3'])
        self.assertFalse(defaults['4'])


if __name__ == '__main__':
    unittest.main()
