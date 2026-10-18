"""Check gathering 39 bytes, record/gallery contract and protected line trees."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from check_deliverable import jpeg_size
from finish_wall import read_png
from check_round39 import fingerprints


def load(path):
    return json.loads(Path(path).read_text())


def main():
    checks = load('gathering/checks-39.json')
    protected = fingerprints()
    assert checks['line_files_unchanged']
    assert len(protected) == checks['protected_files_count']
    assert hashlib.sha256(json.dumps(protected,sort_keys=True).encode()).hexdigest() == checks['protected_files_sha256']
    assert len(checks['suites']) == 67 and checks['total_tests'] == 869
    assert len(checks['demos']) == 78
    assert all(row['exit'] == row['expected_exit'] for row in checks['suites']+checks['demos'])
    latest = load('gathering/latest-checks-39.json')
    assert len(latest) == 4 and all(row['exit'] == 0 for row in latest)
    shared = load('gathering/shared-checks-39.json')
    assert len(shared['suites']) == 5 and shared['total_tests'] == 136
    assert all(row['exit'] == 0 for row in shared['suites'])
    assert all(row['exit'] == 0 for row in shared['demos'])

    wall = Path('artifacts/gathering/wall-v19.png')
    ancestor = Path('artifacts/gathering/wall-v18.png')
    width,height,pixels = read_png(wall)
    aw,ah,old = read_png(ancestor)
    evidence = load('gathering/image-preservation-39.json')
    assert (width,height) == (aw,ah) == (1254,1254)
    assert hashlib.sha256(ancestor.read_bytes()).hexdigest() == evidence['ancestor_sha256']
    digest = hashlib.sha256(wall.read_bytes()).hexdigest()
    assert digest == evidence['wall_sha256']
    x0,y0,w,h = evidence['new_mark_rectangle']
    changed = outside = 0
    for at in range(width*height):
        if old[3*at:3*at+3] != pixels[3*at:3*at+3]:
            changed += 1
            x,y = at%width,at//width
            outside += not (x0 <= x < x0+w and y0 <= y < y0+h)
    assert changed == evidence['changed_pixels'] == 4091 and outside == 0
    assert Path('artifacts/gathering/wall.png').resolve() == wall.resolve()

    record = load('dist/gathering/39.json')
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/'+digest
    assert len(record['attributes']) == 6
    traits = {row['trait_type']:row['value'] for row in record['attributes']}
    assert set(traits) == {'Cave','Wall','Number','Left behind','Meaning','One thing'}
    assert traits['Cave'] == 'Crystal' and traits['Wall'] == 'Gathering'
    assert type(traits['Number']) is int and traits['Number'] == 39
    assert traits['One thing'] == 'Gathering' and traits['Left behind'] == 'Merge Selection Equivalence'
    assert all(set(row) == {'trait_type','value'} for row in record['attributes'])
    preview = Path('dist/gathering/39.jpg')
    assert jpeg_size(preview.read_bytes()) == (512,512)

    goals = [{'line':n,'goal':Path(f'line-{n}/GOAL.md').read_text().strip()} for n in range(1,5)]
    assert load('dist/goals.json') == goals
    page = Path('dist/index.html').read_text()
    groups = json.loads(re.search(r'<script id="records" type="application/json">(.*?)</script>',page,re.S)[1])
    assert len(groups) == 5
    total = pending = 0
    for group,folder in zip(groups,('line-1','line-2','line-3','line-4','gathering')):
        paths = sorted(Path('dist',folder).glob('[0-9][0-9].json'),reverse=True)
        expected = [{'number':int(p.stem),'path':p.relative_to('dist').as_posix(),**load(p)} for p in paths]
        assert group['records'] == expected
        total += len(paths)
        for row in expected:
            if row['name'] == 'Not painted yet':
                pending += 1
                assert not Path('dist',row['path']).with_suffix('.jpg').exists()
    assert total == 189 and pending == 100
    gallery = load('gathering/gallery-checks-39.json')
    assert gallery['passed'] and gallery['newest_gathering'] == 39 and gallery['records'] == total
    assert Path('gathering/COINS.md').read_text().startswith('none\n')
    assert not Path('gathering/coin-order.json').exists()
    for folder in ('gathering','shared','dist'):
        assert all(p.stat().st_size <= 100000 for p in Path(folder).rglob('*') if p.is_file())
    # Tracked changes must stay inside assignment scope. Include untracked
    # source/deliverable files; ignored named PNG output is checked above.
    changed_paths = subprocess.check_output(['git','diff','--name-only','-z']).decode().split('\0')
    untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z']).decode().split('\0')
    for name in changed_paths+untracked:
        if name:
            assert name.startswith(('gathering/','shared/','dist/','artifacts/gathering/','test/scratch/')),name
    review = {'number':39,'line_files_and_records_unchanged':True,
              'line_suites_passed':67,'line_tests_passed':869,
              'expected_demo_statuses':78,'direct_current_demos_passed':4,
              'shared_tests_passed':136,'gallery_records':total,'preserved_placeholders':pending,
              'wall':{'path':str(wall),'dimensions':[width,height],'format':'PNG','mode':'RGB','sha256':digest},
              'preview':{'path':str(preview),'dimensions':[512,512],'format':'JPEG','bytes':preview.stat().st_size},
              'changed_pixels':changed,'changed_pixels_outside_rectangle':outside,
              'visual_review':{'method':'Full wall and 512-pixel JPEG explicitly inspected locally.',
                               'pepe':'Inherited wide mouth and heavy-lidded eyes remain.',
                               'hands':'No hands or handprints added; inherited concealed hands untouched.',
                               'text_or_prohibited_symbols_observed':False,
                               'limitation':'The small generated motif is subtle at thumbnail scale.'},
              'unmet_visual_requirements':[],'coins':'none'}
    Path('gathering/REVIEW-39.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
