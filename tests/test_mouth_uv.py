import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from mouth_events import mouth_events, normalize_repeat_uv


class MouthUVTests(unittest.TestCase):
    def test_hasumi_preserves_repeat_sample(self):
        original = {'x': .25, 'y': 2.5}
        self.assertEqual(normalize_repeat_uv(original, 0, 0), {'x': .25, 'y': .5})
        self.assertEqual(original['y'], 2.5)

    def test_negative_repeats(self):
        self.assertEqual(normalize_repeat_uv({'x': -.125, 'y': 1}, 0, 0), {'x': .875, 'y': 0})

    def test_in_range_uv_does_not_require_repeat(self):
        value = {'x': .125, 'y': .75}
        self.assertEqual(normalize_repeat_uv(value, 1, 1), value)

    def test_non_repeat_out_of_range_is_not_guessed(self):
        for wrap in [None, 1, 2, 3]:
            with self.assertRaises(ValueError):
                normalize_repeat_uv({'x': .25, 'y': 2.5}, 0, wrap)

    def test_signed_negative_mouth_tile_normalized(self):
        clip = {'events': [
            {'time': 0.0, 'function': 'SetMouthTile', 'int': -704},
            {'time': 0.5, 'function': 'SetHorizontallyFlippedMouthTile', 'int': -501},
            {'time': 1.0, 'function': 'SetMouthTileToDefault', 'int': 0},
        ]}
        self.assertEqual(mouth_events(clip, 704), [
            {'time': 0.0, 'tile': 704},
            {'time': 0.5, 'tile': 501, 'flipped': True},
            {'time': 1.0, 'tile': 704, 'reset': True},
        ])


if __name__ == '__main__':
    unittest.main()
