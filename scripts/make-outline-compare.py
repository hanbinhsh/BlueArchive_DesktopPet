"""Build before/after comparison sheets for the outline line regression."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = r'test-results\outline-lines'
PAIRS = [
    ('fubuki-f1104_0-t7.35', 'compare-fubuki.png', (470, 0, 790, 320)),
    ('airi-f5205_0-t14.41', 'compare-airi.png', (240, 0, 790, 420)),
    ('asuna_uniform-f19307_0-t0.3', 'compare-asuna.png', (480, 30, 790, 420)),
]


def stray_mask(on_path, off_path):
    on = np.asarray(Image.open(on_path).convert('RGBA')).astype(np.int16)
    off = np.asarray(Image.open(off_path).convert('RGBA')).astype(np.int16)
    silhouette = (off[:, :, 3] > 8).astype(np.uint8) * 255
    dilated = np.asarray(Image.fromarray(silhouette).filter(ImageFilter.MaxFilter(31))) > 0
    black = (on[:, :, 3] >= 200) & (on[:, :, :3].max(axis=2) <= 30)
    return black & ~dilated


def panel(image, crop, scale, label):
    piece = image.crop(crop)
    piece = piece.resize((int(piece.width * scale), int(piece.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGB', (piece.width, piece.height + 26), 'white')
    canvas.paste(piece, (0, 26), piece)
    ImageDraw.Draw(canvas).text((8, 6), label, fill=(20, 20, 20))
    return canvas


def main():
    for name, output, crop in PAIRS:
        bug = Image.open(os.path.join(ROOT, 'bug', name + '-on.png')).convert('RGBA')
        fixed = Image.open(os.path.join(ROOT, 'fix', name + '-on.png')).convert('RGBA')
        off = Image.open(os.path.join(ROOT, 'bug', name + '-off.png')).convert('RGBA')
        mask = stray_mask(os.path.join(ROOT, 'bug', name + '-on.png'), os.path.join(ROOT, 'bug', name + '-off.png'))
        ys, xs = np.nonzero(mask)
        marked = bug.copy()
        draw = ImageDraw.Draw(marked)
        if len(xs):
            box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(marked.width - 1, xs.max() + 6), min(marked.height - 1, ys.max() + 6))
            draw.rectangle(box, outline=(220, 30, 30), width=4)
        scale = 700 / (crop[2] - crop[0])
        left = panel(marked, crop, scale, '0.2.33 (outline on): long black line')
        right = panel(fixed, crop, scale, '0.2.34 (outline on): fixed')
        sheet = Image.new('RGB', (left.width + right.width + 12, max(left.height, right.height)), (235, 235, 238))
        sheet.paste(left, (0, 0))
        sheet.paste(right, (left.width + 12, 0))
        sheet.save(os.path.join(ROOT, output))
        print(output, sheet.size, 'stray', int(mask.sum()), 'box', None if not len(xs) else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))


if __name__ == '__main__':
    main()