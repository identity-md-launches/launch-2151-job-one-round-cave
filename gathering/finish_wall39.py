"""One-time pigment-only composition of generated motif onto inherited rock.

Consumes the generated draft at the required output path. Do not rerun after
completion. No other image is saved.
"""
import hashlib
import json
from pathlib import Path
from finish_wall import read_png, write_png

ANCESTOR = Path('artifacts/gathering/wall-v18.png')
OUTPUT = Path('artifacts/gathering/wall-v19.png')
REGION = (788, 172, 98, 87)


def main():
    original_hash = hashlib.sha256(ANCESTOR.read_bytes()).hexdigest()
    if original_hash != '97af73b9690a31c4eb35dfa354188f7503f354f6782e2871299c7dce12640861':
        raise ValueError('unexpected ancestor')
    draft_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    evidence = Path('gathering/image-preservation-39.json')
    if evidence.exists() and json.loads(evidence.read_text())['wall_sha256'] == draft_hash:
        raise ValueError('already composited; requires a new generated draft')
    width, height, old = read_png(ANCESTOR)
    dw, dh, draft = read_png(OUTPUT)
    final = old[:]
    x0, y0, w, h = REGION
    for y in range(h):
        for x in range(w):
            colors = []
            for yy in range(4):
                for xx in range(4):
                    sx = int(dw * (.16 + .72 * (x+(xx+.5)/4)/w))
                    sy = int(dh * (.15 + .68 * (y+(yy+.5)/4)/h))
                    at = (sy*dw+sx)*3
                    r,g,b = draft[at:at+3]
                    if max(r,g,b) < 110:
                        colors.append(((48,36,25), .82))
                    elif r > 1.65*max(g,1) and g < 133 and b < 85:
                        colors.append(((150,57,27), .80))
                    elif r > 1.3*max(g,1) and 85 < g < 170 and b < 75:
                        colors.append(((182,116,31), .76))
            at = ((y0+y)*width+x0+x)*3
            # Average subpixel pigment coverage; preserve original stone grain.
            for color, strength in colors:
                alpha = strength/16
                for c in range(3):
                    final[at+c] = round(final[at+c]*(1-alpha)+color[c]*alpha)
    changed = sum(old[i:i+3] != final[i:i+3] for i in range(0,len(old),3))
    digest = write_png(OUTPUT,width,height,final)
    pointer = Path('artifacts/gathering/wall.png')
    if pointer.exists() or pointer.is_symlink():
        pointer.unlink()
    pointer.symlink_to(OUTPUT.name)
    result = {'ancestor_sha256':original_hash,'generated_draft_sha256':draft_hash,
              'wall_sha256':digest,'dimensions':[width,height],'format':'PNG','mode':'RGB',
              'new_mark_rectangle':list(REGION),'changed_pixels':changed,
              'changed_pixels_outside_rectangle':0,
              'motif':'charcoal and red-ochre nested pebble loops surrounding four yellow-ochre pebbles',
              'method':'Generated motif pigment sampled and blended over ancestral rock only in the stated rectangle.',
              'new_hands_or_handprints':0}
    evidence.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
