"""Detect stray black pixels painted by the outline pass.

Compares an outline-on screenshot against its outline-off twin at the same
frozen animation time.  Pixels that are (nearly) black in the outline-on image
but lie farther than ~15 px from any visible geometry in the outline-off image
cannot be a silhouette outline; they are the long-line artifact.

Usage: python scripts/outline-lines-metric.py <directory>
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

RADIUS = 31          # odd box size: dilate the silhouette by 15 px
BLACK_MAX = 30       # channel ceiling for "ink black"
ALPHA_MIN = 200

def analyse(directory):
    rows = []
    for on_path in sorted(glob.glob(os.path.join(directory, '*-on.png'))):
        off_path = on_path[:-7] + '-off.png'
        if not os.path.exists(off_path):
            continue
        on = np.asarray(Image.open(on_path).convert('RGBA')).astype(np.int16)
        off = np.asarray(Image.open(off_path).convert('RGBA')).astype(np.int16)
        alpha_on, alpha_off = on[:, :, 3], off[:, :, 3]
        silhouette = (alpha_off > 8).astype(np.uint8) * 255
        dilated = np.asarray(
            Image.fromarray(silhouette).filter(ImageFilter.MaxFilter(RADIUS))
        ) > 0
        rgb_max = on[:, :, :3].max(axis=2)
        black = (alpha_on >= ALPHA_MIN) & (rgb_max <= BLACK_MAX)
        stray = black & ~dilated
        count = int(stray.sum())
        box = None
        if count:
            ys, xs = np.nonzero(stray)
            box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        rows.append({
            'frame': os.path.basename(on_path)[:-7],
            'black': int(black.sum()),
            'stray': count,
            'stray_box': box,
            'width': int(on.shape[1]),
            'height': int(on.shape[0]),
        })
    return rows

def main():
    directory = sys.argv[1]
    rows = analyse(directory)
    if not rows:
        raise SystemExit('no screenshot pairs found in ' + directory)
    worst = max(rows, key=lambda r: r['stray'])
    for row in rows:
        if row['stray']:
            print('{frame}: stray={stray} black={black} box={stray_box}'.format(**row))
    print('\nsummary: frames={} worst={} stray_total={}'.format(
        len(rows), worst['frame'], sum(r['stray'] for r in rows)))
    print('worst stray box:', worst['stray_box'])
    try:
        with open(os.path.join(directory, 'metric.json'), 'w', encoding='utf-8') as fh:
            json.dump({'radius': RADIUS, 'rows': rows}, fh, indent=2)
    except OSError as error:
        print('could not write metric.json:', error)
    return 0 if worst['stray'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())