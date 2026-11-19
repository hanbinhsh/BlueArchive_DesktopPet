"""Build contact sheets for Wave 21 outfits and furniture scenes."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, math, sys

T = Path('test-results')
R = Path('.assets/wave21-final')
specs = json.loads(Path('scripts/roster-wave21.json').read_text('utf8'))
mode = sys.argv[1]

if mode == 'thumbs':
    ids = list(specs)
    cols = 8
    rows_n = math.ceil(len(ids) / cols)
    canvas = Image.new('RGB', (cols * 260, rows_n * 310), (31, 38, 47))
    draw = ImageDraw.Draw(canvas)
    for i, k in enumerate(ids):
        p = R / k / 'thumbnail.png'
        im = Image.open(p).convert('RGBA')
        x = (i % cols) * 260
        y = (i // cols) * 310
        canvas.paste(im, (x + 10, y + 25), im)
        draw.text((x + 6, y + 4), k, fill='white')
    canvas.save(T / 'wave21-thumbs-contact.jpg', quality=94)
    print('Saved wave21-thumbs-contact.jpg')
elif mode == 'angles':
    rows = [
        dict(character=k, id=f['id'], status='ready', times=[min(5.0, f['duration'] / 3)], yaw=yaw)
        for k in specs
        for f in json.loads((R / k / 'character.json').read_text('utf8')).get('furniture', [])
        for yaw in [0, math.pi / 2, math.pi, math.pi * 1.5]
    ]
    (T / 'wave21-angles-rows.json').write_text(json.dumps(rows), 'utf8')
    print('Wrote', len(rows), 'angle rows')
elif mode == 'angle-sheets':
    rows = json.loads((T / 'wave21-angles-rows.json').read_text('utf8'))
    for page, start in enumerate(range(0, len(rows), 16)):
        group = rows[start:start + 16]
        canvas = Image.new('RGB', (1200, math.ceil(len(group) / 4) * 300), (31, 38, 47))
        draw = ImageDraw.Draw(canvas)
        for i, row in enumerate(group):
            files = [
                p for p in T.glob(f'wave21a-{row["character"]}-{row["id"]}-*.png')
                if abs((float(p.stem.split('-yaw')[1]) if '-yaw' in p.stem else 0) - row['yaw']) < 1e-8
            ]
            assert len(files) == 1, (row, files)
            im = Image.open(files[0]).convert('RGBA')
            bbox = im.getbbox()
            if bbox:
                im = im.crop(bbox)
            im.thumbnail((294, 270))
            x = (i % 4) * 300
            y = (i // 4) * 300
            canvas.paste(im, (x + (300 - im.width) // 2, y + 28), im)
            draw.text((x + 2, y + 2), f'{row["character"]} {row["id"]} yaw+{row["yaw"]:.2f}', fill='white')
        canvas.save(T / f'wave21-angle-options-{page:02}.jpg', quality=94)
        print(f'Saved wave21-angle-options-{page:02}.jpg')
