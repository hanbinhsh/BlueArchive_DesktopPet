"""Build contact sheets for Wave 18 outfits, Wave 18 Cafe furniture, and Field-Cafe exploration furniture."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, math, sys

T = Path('test-results')
R = Path('.assets/wave18-final')
specs_all = json.loads(Path('scripts/roster-wave18-all.json').read_text('utf8'))
specs_w18 = json.loads(Path('scripts/roster-wave18.json').read_text('utf8'))
mode = sys.argv[1]

# Representative furniture entries to angle-check (all 8 Wave 18 Cafe + 12 Field-Cafe sets)
FIELD_REPRESENTATIVES = [
    ('hina', 'field_bookshelf_ing'),
    ('hina', 'field_cat_ing'),
    ('hina', 'field_piano_ing'),
    ('hina_dress', 'field_table_ing'),
    ('seia', 'field_gymball_ing'),
    ('seia', 'field_mic_ing'),
    ('seia', 'field_cabinet_ing'),
    ('seia', 'field_vending01_ing'),
    ('seia', 'field_vending02_ing'),
    ('seia', 'field_riosbot_ing'),
    ('np0283', 'field_cat_ing'),
    ('np0283', 'field_bench_ing'),
]

def target_furniture():
    items = []
    for k in specs_w18:
        for f in json.loads((R / k / 'character.json').read_text('utf8')).get('furniture', []):
            items.append((k, f))
    for k, fid in FIELD_REPRESENTATIVES:
        f = next(x for x in json.loads((R / k / 'character.json').read_text('utf8')).get('furniture', []) if x['id'] == fid)
        items.append((k, f))
    return items

if mode == 'thumbs':
    ids = list(specs_all)
    cols = 5
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
    canvas.save(T / 'wave18-thumbs-contact.jpg', quality=94)
    print('Saved wave18-thumbs-contact.jpg')
elif mode == 'angles':
    rows = [
        dict(character=k, id=f['id'], status='ready', times=[min(5.0, f['duration'] / 3)], yaw=yaw)
        for k, f in target_furniture()
        for yaw in [0, math.pi / 2, math.pi, math.pi * 1.5]
    ]
    (T / 'wave18-angles-rows.json').write_text(json.dumps(rows), 'utf8')
    print('Wrote', len(rows), 'angle rows')
elif mode == 'angle-sheets':
    rows = json.loads((T / 'wave18-angles-rows.json').read_text('utf8'))
    for page, start in enumerate(range(0, len(rows), 16)):
        group = rows[start:start + 16]
        canvas = Image.new('RGB', (1200, math.ceil(len(group) / 4) * 300), (31, 38, 47))
        draw = ImageDraw.Draw(canvas)
        for i, row in enumerate(group):
            files = [
                p for p in T.glob(f'wave18-angles-{row["character"]}-{row["id"]}-*.png')
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
        canvas.save(T / f'wave18-angle-options-{page:02}.jpg', quality=94)
        print(f'Saved wave18-angle-options-{page:02}.jpg')
elif mode == 'furniture-final':
    rows = [
        dict(character=k, id=f['id'], status='ready', times=[0.0, f['duration'] * 0.25, f['duration'] * 0.5, f['duration'] * 0.75], yaw=0)
        for k, f in target_furniture()
    ]
    (T / 'wave18-furniture-rows.json').write_text(json.dumps(rows), 'utf8')
    print('Wrote', len(rows), 'final furniture rows')
elif mode == 'furniture-sheets':
    rows = json.loads((T / 'wave18-furniture-rows.json').read_text('utf8'))
    for page, start in enumerate(range(0, len(rows), 4)):
        group = rows[start:start + 4]
        canvas = Image.new('RGB', (1200, len(group) * 300), (31, 38, 47))
        draw = ImageDraw.Draw(canvas)
        for r_i, row in enumerate(group):
            for c_i, frac in enumerate([0, 0.25, 0.5, 0.75]):
                p = T / f'wave18-furn-{row["character"]}-{row["id"]}-{frac}.png'
                if not p.exists():
                    continue
                im = Image.open(p).convert('RGBA')
                bbox = im.getbbox()
                if bbox:
                    im = im.crop(bbox)
                im.thumbnail((294, 270))
                x = c_i * 300
                y = r_i * 300
                canvas.paste(im, (x + (300 - im.width) // 2, y + 28), im)
                draw.text((x + 2, y + 2), f'{row["character"]} {row["id"]} t={frac:.2f}', fill='white')
        canvas.save(T / f'wave18-furniture-review-{page:02}.jpg', quality=94)
        print(f'Saved wave18-furniture-review-{page:02}.jpg')
