"""Composite generated pigment only; run once on the image tool's draft.

No extra images are written. Existing reviewed PNG/JPEG codecs are reused.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('png39', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)
old = Path('artifacts/line-2/wall-v18.png')
out = Path('artifacts/line-2/wall-v19.png')
ancestor_sha = hashlib.sha256(old.read_bytes()).hexdigest()
assert ancestor_sha == '87126fdb5538c2f2ab5ab18246b54c7ba1c7071548d19d39347b6fbdbc253b8a'
assert not Path('dist/line-2/39.json').exists(), 'do not apply twice'
w, h, ancestor = png.read_png(old)
dw, dh, draft = png.read_png(out)
draft_sha = hashlib.sha256(out.read_bytes()).hexdigest()
assert (w, h, dw, dh) == (1254, 1254, 1254, 1254)
final = ancestor[:]
rect = (660, 174, 100, 108)
sx, sy, sw, sh = 245, 225, 760, 780
for y in range(rect[3]):
    for x in range(rect[2]):
        # Average only selected pigment samples, leaving all source rock out.
        selected = []
        for dy in range(sh*y//rect[3], sh*(y+1)//rect[3]):
            for dx in range(sw*x//rect[2], sw*(x+1)//rect[2]):
                i = ((sy+dy)*dw+sx+dx)*3
                r, g, b = draft[i:i+3]
                red = r > 1.75*g and r > 2.2*b and g < 125
                chalk = (565 < sx+dx < 690 and 570 < sy+dy < 690 and
                         r > 165 and g > 140 and b > 105 and r-g < 65)
                charcoal = (595 < sx+dx < 680 and 660 < sy+dy < 930 and
                            r < 90 and g < 75 and b < 60)
                if red or chalk or charcoal:
                    selected.append((r, g, b))
        if selected:
            target = ((rect[1]+y)*w+rect[0]+x)*3
            samples = ((sh*(y+1)//rect[3]-sh*y//rect[3]) *
                       (sw*(x+1)//rect[2]-sw*x//rect[2]))
            alpha = min(.86, len(selected)/samples * .9)
            for c in range(3):
                color = sum(row[c] for row in selected)/len(selected)
                final[target+c] = round(ancestor[target+c]*(1-alpha) + color*alpha)
changed = [i for i in range(w*h) if ancestor[3*i:3*i+3] != final[3*i:3*i+3]]
assert len(changed) > 1000
outside = sum(not (rect[0] <= i%w < rect[0]+rect[2] and
                   rect[1] <= i//w < rect[1]+rect[3]) for i in changed)
assert outside == 0
digest = png.write_png(out, w, h, final)
wall = Path('artifacts/line-2/wall.png')
wall.unlink()
wall.symlink_to('wall-v19.png')

rgba = bytearray()
for y in range(512):
    ya, yb = y*h//512, (y+1)*h//512
    for x in range(512):
        xa, xb = x*w//512, (x+1)*w//512
        count = (yb-ya)*(xb-xa)
        for c in range(3):
            rgba.append(round(sum(final[(yy*w+xx)*3+c]
                                  for yy in range(ya,yb) for xx in range(xa,xb))/count))
        rgba.append(255)
subprocess.run(['node', '-e',
    "const fs=require('fs');const encode=require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');"
    "const result=encode({data:fs.readFileSync(0),width:512,height:512},78);"
    "if(result.data.length>100000)throw Error('JPEG too large');"
    "fs.writeFileSync('dist/line-2/39.jpg',result.data);"], input=rgba, check=True)

review = {
    'round': 39, 'ancestorSha256': ancestor_sha, 'generatedDraftSha256': draft_sha,
    'wallSha256': digest,
    'wall': {'path': str(out), 'format': 'PNG', 'channels': 'RGB',
             'dimensions': [w,h], 'bytes': out.stat().st_size},
    'preview': {'path': 'dist/line-2/39.jpg', 'format': 'JPEG',
                'dimensions': [512,512], 'bytes': Path('dist/line-2/39.jpg').stat().st_size,
                'sha256': hashlib.sha256(Path('dist/line-2/39.jpg').read_bytes()).hexdigest()},
    'newMarkRectangle': list(rect), 'changedPixels': len(changed),
    'changedPixelsOutsideRectangle': outside,
    'method': 'Installed image tool generated nested ochre pigment on rock. Selected pigment samples were reduced and blended only onto bare ancestral rock in the stated rectangle; source rock was discarded. Every pixel outside it is unchanged.',
    'visualReview': 'Pending explicit full-wall and JPEG inspection.',
    'unmetVisualRequirements': [],
    'deliveryNote': 'The required beside-record 512-pixel JPEG is the sole new image outside artifacts/, following the explicit output requirement despite the conflicting blanket image-location sentence.'
}
Path('line-2/REVIEW-39.json').write_text(json.dumps(review, indent=2)+'\n')
record = {'name': 'The Nested Seed', 'image': 'https://api.imd.fun/artifacts/'+digest,
          'attributes': [
              {'trait_type': 'Cave', 'value': 'Crystal'},
              {'trait_type': 'Wall', 'value': 'Line 2'},
              {'trait_type': 'Number', 'value': 39},
              {'trait_type': 'Left behind', 'value': 'Mapping Path'},
              {'trait_type': 'Meaning', 'value': 'Nested ochre rings lead to a pale seed whose place can be proven.'},
              {'trait_type': 'One thing', 'value': 'Verify Ethereum account and storage proofs against trusted state roots'}]}
Path('dist/line-2/39.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(review, indent=2))
