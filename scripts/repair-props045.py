"""Repair prop materials and visibility in existing verified character packs."""

import argparse
from pathlib import Path
import shutil

from glb import load, save
from prop_materials import adapt_prop_material
from prop_visibility import apply_prop_visibility


def repair(source, output):
    targets = {
        'karin_bunnygirl': ('model.glb',),
        'shigure': ('f9107_0.glb',),
        'shigure_onsen': ('model.glb', 'f6301_0.glb'),
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
