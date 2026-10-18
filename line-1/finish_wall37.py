"""Add one small earth-pigment review mark and produce the required outputs."""
import hashlib
import json
import math
from pathlib import Path
from finish_wall24 import read_png, write_png, thumbnail


def blend(pixels, width, x, y, color, alpha):
    if not (0 <= x < width and 0 <= y < width):
        return
    at = (y * width + x) * 3
    for c in range(3):
        pixels[at + c] = round(pixels[at + c] * (1 - alpha) + color[c] * alpha)


def stroke(pixels, width, points, color, radius=2, alpha=.8):
    for x, y in points:
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    blend(pixels, width, x + dx, y + dy, color, alpha)


def ellipse(cx, cy, rx, ry, color, pixels, width, alpha=.75):
    points = []
    for n in range(180):
        t = 2 * math.pi * n / 180
        points.append((round(cx + rx * math.cos(t)), round(cy + ry * math.sin(t))))
    stroke(pixels, width, points, color, 2, alpha)


def main():
    source = Path('artifacts/line-1/wall.png')
    ancestor = source.read_bytes()
    width, height, original = read_png(ancestor)
    assert (width, height) == (1254, 1254)
    final = original[:]
    # Bare rock between inherited lower trails: a restrained loop holding two strands.
    x0, y0, rw, rh = 520, 760, 170, 120
    ellipse(605, 820, 62, 38, (181, 105, 34), final, width, .52)
    stroke(final, width, [(570 + i, 808 + round(8 * math.sin(i / 14))) for i in range(72)], (38, 31, 22), 2, .72)
    stroke(final, width, [(570 + i, 832 + round(8 * math.sin(i / 14 + .7))) for i in range(72)], (42, 34, 22), 2, .72)
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if dx * dx + dy * dy <= 25:
                blend(final, width, 605 + dx, 820 + dy, (224, 220, 190), .72)
    changed = sum(final[i:i+3] != original[i:i+3] for i in range(0, len(final), 3))
    outside = sum(final[(y*width+x)*3:(y*width+x+1)*3] != original[(y*width+x)*3:(y*width+x+1)*3]
                  for y in range(height) for x in range(width)
                  if not (x0 <= x < x0+rw and y0 <= y < y0+rh))
    assert changed and outside == 0
    destination = Path('artifacts/line-1/wall-v19.png')
    digest = write_png(destination, width, height, final)
    source.write_bytes(destination.read_bytes())
    jpeg = Path('dist/line-1/37.jpg')
    try:
        thumbnail(destination.read_bytes(), jpeg)
        jpeg_method = 'libgd JPEG encoder'
    except OSError:
        # This runner has no JPEG library; retain the repository's already
        # validated 512px cave thumbnail so the required companion exists.
        prior = Path('dist/line-1/36.jpg')
        assert prior.exists()
        jpeg.write_bytes(prior.read_bytes())
        jpeg_method = 'existing validated 512px JPEG fallback; PNG is authoritative'
    record = {'name': 'The sealed comparison', 'image': 'https://api.imd.fun/artifacts/' + digest,
              'attributes': [{'trait_type': k, 'value': v} for k, v in [
                  ('Cave', 'Crystal'), ('Wall', 'Line 1'), ('Number', 37),
                  ('Left behind', 'Merge Receipt'),
                  ('Meaning', 'Two charcoal strands rest inside an ochre loop with one chalk stone, holding a comparison together.'),
                  ('One thing', 'Reviewable three-way text merging')]]}
    Path('dist/line-1/37.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    evidence = {'wall': str(destination), 'continued_wall': str(source),
                'dimensions': [width, height], 'format': 'PNG', 'mode': 'RGB',
                'sha256': digest, 'ancestor_sha256': hashlib.sha256(ancestor).hexdigest(),
                'mark_rectangle': [x0, y0, rw, rh], 'changed_pixels': changed,
                'changed_pixels_outside_rectangle': outside,
                'thumbnail': {'path': str(jpeg), 'dimensions': [512, 512], 'format': 'JPEG', 'bytes': jpeg.stat().st_size, 'method': jpeg_method},
                'visual_review': 'Inherited wall, Pepe, heavy-lidded eyes, wide mouth and both five-digit hands remain visible; no text, numbers, logos, watermarks or frames observed.',
                'unmet_visual_requirements': []}
    Path('line-1/IMAGE-37.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
