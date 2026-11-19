"""Repair prop materials, renderer event visibility, and sRGB step masks in verified character packs."""

import argparse
from pathlib import Path
import shutil

from glb import load, save
from prop_materials import adapt_prop_material
from prop_visibility import apply_prop_visibility
from renderer_event_layout import renderer_event_layout
from visibility import attach_visibility

SHIGURE_ONSEN_RENDERERS = [
    'CH0123_Weapon',
    'CH0123_CutIn_Body',
    'CH0123_Body',
    'CH0123_Prop',
    'CH0123_Halo',
]


def repair(source, output):
    targets = {
        'karin_bunnygirl': ('model.glb', 'f207305_0.glb'),
        'shigure': ('f9107_0.glb',),
        'shigure_onsen': ('model.glb', 'f6301_0.glb'),
        'ibuki_swimsuit': ('f211311_1.glb',),
        'iroha_swimsuit': ('f211311_1.glb',),
    }
    for character, models in targets.items():
        dest = output / character
        dest.mkdir(parents=True, exist_ok=True)
        for path in (source / character).iterdir():
            if path.is_file() and path.name not in models:
                shutil.copy2(path, dest / path.name)
        for filename in models:
            doc, binary = load(source / character / filename)
            for material in doc['materials']:
                adapt_prop_material(material)
            if character == 'shigure_onsen' and filename == 'model.glb':
                existing_defaults = doc['scenes'][0]['extras']['BA_pet_visibility'].get('defaults', {})
                defaults_by_name = {
                    doc['nodes'][int(k)]['name']: v for k, v in existing_defaults.items()
                }
                layout = renderer_event_layout('shigure_onsen', SHIGURE_ONSEN_RENDERERS)
                attach_visibility(doc, layout, defaults_by_name)
            timeline = ('my_hotsprings_01_woodenbathtub_CH0123'
                        if filename == 'f6301_0.glb' else None)
            apply_prop_visibility(doc, character, timeline)
            save(dest / filename, doc, binary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    repair(args.source, args.output)
