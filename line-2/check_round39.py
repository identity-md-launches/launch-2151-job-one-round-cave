"""Read-only local output checks; no independent behavior/visual certification."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('check_png39', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)
wall = Path('artifacts/line-2/wall-v19.png')
ancestor = Path('artifacts/line-2/wall-v18.png')
review = json.loads(Path('line-2/REVIEW-39.json').read_text())
record = json.loads(Path('dist/line-2/39.json').read_text())
assert set(record) == {'name', 'image', 'attributes'}
traits = record['attributes']
assert len(traits) == 6 and all(set(t) == {'trait_type', 'value'} for t in traits)
assert [t['trait_type'] for t in traits] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
assert [t['value'] for t in traits[:4]] == ['Crystal','Line 2',39,'Mapping Path']
assert type(traits[2]['value']) is int
records = list(Path('dist/line-2').glob('[0-9][0-9].json'))
assert len(records) == 39
assert len([p for p in records if int(p.stem) < 39]) == 38
digest = hashlib.sha256(wall.read_bytes()).hexdigest()
assert digest == review['wallSha256']
assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
assert hashlib.sha256(ancestor.read_bytes()).hexdigest() == review['ancestorSha256']
assert Path('artifacts/line-2/wall.png').read_bytes() == wall.read_bytes()
w,h,current = png.read_png(wall)
aw,ah,old = png.read_png(ancestor)
assert (w,h,aw,ah) == (1254,1254,1254,1254)
rect = review['newMarkRectangle']
changed = outside = 0
for i in range(w*h):
    if current[i*3:i*3+3] != old[i*3:i*3+3]:
        changed += 1
        outside += not (rect[0] <= i%w < rect[0]+rect[2] and
                        rect[1] <= i//w < rect[1]+rect[3])
assert changed == review['changedPixels'] and outside == 0

# Parse JPEG segments to inspect the actual SOF dimensions, not a file label.
preview = Path('dist/line-2/39.jpg').read_bytes()
assert preview[:2] == b'\xff\xd8' and preview[-2:] == b'\xff\xd9'
at, dimensions = 2, None
while at < len(preview):
    assert preview[at] == 255
    marker = preview[at+1]
    if marker == 0xda:
        break
    length = int.from_bytes(preview[at+2:at+4], 'big')
    if marker == 0xc0:
        dimensions = [int.from_bytes(preview[at+7:at+9], 'big'),
                      int.from_bytes(preview[at+5:at+7], 'big')]
        break
    at += length + 2
assert dimensions == [512,512]
assert len(preview) == review['preview']['bytes'] <= 100_000
assert hashlib.sha256(preview).hexdigest() == review['preview']['sha256']
assert review['unmetVisualRequirements'] == []
assert 'Pending' not in review['visualReview']

# Git checks inspect tracked originals without altering the index or working tree.
original_goal = subprocess.run(['git','show','HEAD:line-2/GOAL.md'],
                               check=True,capture_output=True).stdout
assert Path('line-2/GOAL.md').read_bytes() == original_goal
changed_tracked = subprocess.run(['git','diff','--name-only','HEAD'],
                                check=True,capture_output=True,text=True).stdout.splitlines()
assert set(changed_tracked) == {'line-2/USED.md','artifacts/line-2/wall.png'}
new_files = subprocess.run(['git','ls-files','--others','--exclude-standard'],
                          check=True,capture_output=True,text=True).stdout.splitlines()
assert all(path.startswith(('line-2/','dist/line-2/','artifacts/line-2/')) for path in new_files)
assert all(Path(path).stat().st_size <= 100_000 for path in new_files
           if not path.startswith('artifacts/'))
assert wall.as_posix() not in subprocess.run(['git','ls-files'],check=True,
                                           capture_output=True,text=True).stdout.splitlines()
print(json.dumps({'passed':True,'wall':str(wall),'dimensions':[w,h],
                  'format':'PNG','sha256':digest,'recordNumber':39,
                  'previewDimensions':dimensions,'previewFormat':'JPEG',
                  'changedPixels':changed,'changedPixelsOutsideRectangle':outside,
                  'goalByteIdentical':True,'olderRecordsUnchanged':True,
                  'pathsWithinScope':True,'unmetVisualRequirements':[],
                  'meaning':'Local structural checks and explicit visual inspection; not independent certification.'},indent=2))
