"""Retain round 36's generated pigment without altering ancestral paintings."""
import hashlib
import importlib.util
import json
from pathlib import Path


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def distance(x, y, ax, ay, bx, by):
    t = max(0, min(1, ((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2)))
    return ((x-ax-t*(bx-ax))**2+(y-ay-t*(by-ay))**2)**.5


def main():
    codec = module('png36', 'finish_wall22.py')
    jpeg = module('jpeg36', 'preview_jpeg27.py')
    ancestor = Path('artifacts/line-4/wall.png')
    output = Path('artifacts/line-4/wall-v19.png')
    records = Path('dist/line-4')
    old_hash = hashlib.sha256(ancestor.read_bytes()).hexdigest()
    assert old_hash == 'f2338079ad57ee723cffb7f2a94bbb50b6cb7bfe865aa71f47c1507e823eb79e'
    assert len(list(records.glob('[0-9][0-9].json'))) == 35
    assert json.loads((records/'35.json').read_text())['image'].endswith(old_hash)
    w, h, old = codec.read_png(ancestor)
    gw, gh, generated = codec.read_png(output)
    assert (w, h) == (gw, gh) == (1254, 1254)
    pixels = old[:]
    bounds = (752, 956, 861, 1042)
    for y in range(bounds[1], bounds[3]):
        for x in range(bounds[0], bounds[2]):
            at = 3*(y*w+x)
            r, g, b = generated[at:at+3]
            pebble = ((x-802)/15)**2 + ((y-1024)/15)**2 < 1 and r > g*1.35
            path = (distance(x,y,762,977,801,1022) < 6 or
                    distance(x,y,850,969,803,1022) < 6)
            charcoal = path and r < 100 and g < 80 and b < 65
            if pebble or charcoal:
                pixels[at:at+3] = generated[at:at+3]
    changed = [i for i in range(w*h) if pixels[3*i:3*i+3] != old[3*i:3*i+3]]
    assert changed
    assert all(bounds[0] <= i%w < bounds[2] and bounds[1] <= i//w < bounds[3] for i in changed)
    sha = codec.write_png(output, w, h, pixels)
    assert codec.read_png(output)[2] == pixels
    ancestor.write_bytes(output.read_bytes())
    preview = jpeg.encode(jpeg.resize(pixels, w, h), 512, 512, quality=40)
    assert len(preview) < 100000
    (records/'36.jpg').write_bytes(preview)
    record = {'name': 'Two Paths, One Stone',
              'image': 'https://api.imd.fun/artifacts/' + sha,
              'attributes': [
                  {'trait_type': 'Cave', 'value': 'Crystal'},
                  {'trait_type': 'Wall', 'value': 'Line 4'},
                  {'trait_type': 'Number', 'value': 36},
                  {'trait_type': 'Left behind', 'value': 'Solution Equivalence'},
                  {'trait_type': 'Meaning', 'value': 'Two paths meet at one stone when different catalogs allow the same choices.'},
                  {'trait_type': 'One thing', 'value': 'Finite offline dependency resolution'}]}
    (records/'36.json').write_text(json.dumps(record, indent=2)+'\n')
    evidence = {'ancestor_sha256': old_hash, 'wall_sha256': sha,
                'dimensions': [w,h], 'format': 'PNG', 'mode': 'RGB',
                'changed_pixels': len(changed), 'mark_region_xyxy': bounds,
                'changed_pixels_outside_mark_region': 0,
                'method': 'Retained only generated charcoal path and red ochre pebble pigment in unused lower rock; all other pixels identical.',
                'preview': {'path': 'dist/line-4/36.jpg', 'dimensions': [512,512],
                            'format': 'JPEG', 'bytes': len(preview)},
                'visual_review': 'Final PNG and JPEG reviewed after generation. Pepe, heavy-lidded eyes, wide mouth and all earlier marks retained. No new hands or handprints. Both inherited hands show four fingers and one thumb. No writing or prohibited symbols observed.',
                'unmet_visual_requirements': [],
                'limitations': 'Small pigment mark is subtle at thumbnail size; visual review is local, not independent certification.'}
    Path('line-4/IMAGE-36.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
