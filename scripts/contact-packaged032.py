"""Create critical-frame evidence using actual packaged application captures."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

root = Path(__file__).resolve().parent.parent
groups = [
    ('mine', 'f207310_0', [11.5, 12, 12.6, 13.2, 13.7]),
    ('mine', 'f207310_0', [16.2, 16.6, 17, 17.8, 18.6]),
    ('kikyou_swimsuit', 'f210372_0', [19.3, 19.5, 19.8, 20.3, 20.9]),
    ('kikyou_swimsuit', 'f210372_0', [23.1, 23.2, 23.4, 24, 24.6]),
    ('hanako_swimsuit', 'f210316_0', None),
    ('mine', 'f207310_0', [25.5, 26.5]),
]
for yaw in [0, .7, -.7]:
    rows = groups if not yaw else groups[:4]
    sheet = Image.new('RGB', (1500, 310 * len(rows)), (31, 38, 47))
    draw = ImageDraw.Draw(sheet)
    for y, (character, action, times) in enumerate(rows):
        manifest = json.loads((root / f'characters/{character}/character.json').read_text('utf8'))
        duration = next(f['duration'] for f in manifest['furniture'] if f['id'] == action)
        suffix = f'-yaw{yaw}' if yaw else ''
        pattern = f'packaged032-{character}-{action}-*{suffix}.png'
        captures = {}
        prefix = f'packaged032-{character}-{action}-'
        for file in (root / 'test-results').glob(pattern):
            tail = file.stem[len(prefix):]
            if not yaw and '-yaw' in tail:
                continue
            fraction = float(tail.removesuffix(suffix) if suffix else tail)
            captures[fraction] = file
        fractions = [t / duration for t in times] if times else [.1, .3, .5, .7, .9]
        for x, fraction in enumerate(fractions):
            closest = min(captures, key=lambda n: abs(n - fraction))
            assert abs(closest - fraction) < 1e-8
            im = Image.open(captures[closest]).convert('RGBA')
            bounds = im.getbbox()
            if bounds:
                im = im.crop(bounds)
            im.thumbnail((290, 275))
            sheet.paste(im, (x * 300 + (300 - im.width) // 2, y * 310 + 28), im)
            draw.text((x * 300 + 4, y * 310 + 5), f'{character} {fraction * duration:.2f}s / yaw {yaw}', fill='white')
    name = 'packaged032-focus-contact' if not yaw else f'packaged032-focus-yaw{yaw}'
    sheet.save(root / f'test-results/{name}.jpg', quality=92)
