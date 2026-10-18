'use strict';
// Transfer a bounded generated pigment mark onto the inherited, unchanged wall.
const fs = require('fs');
const crypto = require('crypto');
const assert = require('assert');
const {readPNG, writePNG} = require('./finish_wall36.js');
const jpeg = require('./tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const priorPath = 'artifacts/line-3/wall-v18.png';
const nextPath = 'artifacts/line-3/wall-v19.png';
const priorBytes = fs.readFileSync(priorPath);
const draftBytes = fs.readFileSync(nextPath);
const old = readPNG(priorBytes), draft = readPNG(draftBytes);
assert.deepEqual([old.width, old.height], [1254, 1254]);
assert.deepEqual([draft.width, draft.height], [1254, 1254]);
assert(!fs.existsSync('dist/line-3/38.json'));
const rect = [985, 390, 175, 105];
const pixels = Buffer.from(old.pixels);
const classes = {red: 0, charcoal: 0, chalk: 0, yellow: 0};
for(let y=rect[1]; y<rect[1]+rect[3]; y++) for(let x=rect[0]; x<rect[0]+rect[2]; x++) {
  const at=(y*1254+x)*3;
  const [r,g,b] = draft.pixels.subarray(at,at+3);
  const [or,og,ob] = old.pixels.subarray(at,at+3);
  // Leave older dark, red, and chalk marks untouched even inside the patch.
  if((or>95 && or>og*1.53 && or-og>47) ||
     (or<68 && og<56 && ob<48) ||
     (or>170 && og>157 && ob>130 && or-og<39)) continue;
  if(Math.abs(r-or)+Math.abs(g-og)+Math.abs(b-ob)<45) continue;
  let color, kind;
  if(r>95 && r>g*1.6 && g>b*1.12 && r-g>or-og+11) {
    kind='red'; color=[147,57,29];
  } else if(r<84 && g<73 && b<61 && or-r>25 && og-g>18) {
    kind='charcoal'; color=[37,29,22];
  } else if(r>158 && g>145 && b>121 && g-og>26 && b-ob>28) {
    kind='chalk'; color=[209,195,166];
  } else if(r>135 && g>83 && b<105 && r>g*1.2 && g>b*1.15 && g-og>20) {
    kind='yellow'; color=[178,116,49];
  } else continue;
  classes[kind]++;
  for(let c=0;c<3;c++) pixels[at+c]=Math.round(old.pixels[at+c]*0.23+color[c]*0.77);
}
let changed=0, outside=0;
for(let i=0;i<1254*1254;i++) if(!pixels.subarray(i*3,i*3+3).equals(old.pixels.subarray(i*3,i*3+3))) {
  changed++;
  const x=i%1254, y=Math.floor(i/1254);
  if(x<rect[0] || x>=rect[0]+rect[2] || y<rect[1] || y>=rect[1]+rect[3]) outside++;
}
assert(changed>1000 && changed<rect[2]*rect[3]);
assert.equal(outside,0);
const png=writePNG(1254,1254,pixels);
assert(readPNG(png).pixels.equals(pixels));
const rgba=Buffer.alloc(512*512*4);
for(let y=0;y<512;y++)for(let x=0;x<512;x++) {
  const xa=Math.floor(x*1254/512), xb=Math.floor((x+1)*1254/512);
  const ya=Math.floor(y*1254/512), yb=Math.floor((y+1)*1254/512);
  for(let c=0;c<3;c++) {
    let sum=0;
    for(let sy=ya;sy<yb;sy++)for(let sx=xa;sx<xb;sx++)sum+=pixels[(sy*1254+sx)*3+c];
    rgba[(y*512+x)*4+c]=Math.round(sum/((xb-xa)*(yb-ya)));
  }
  rgba[(y*512+x)*4+3]=255;
}
const thumb=jpeg({data:rgba,width:512,height:512},77).data;
assert(thumb.length<100000);
fs.writeFileSync(nextPath,png);
fs.unlinkSync('artifacts/line-3/wall.png');
fs.symlinkSync('wall-v19.png','artifacts/line-3/wall.png');
fs.writeFileSync('dist/line-3/38.jpg',thumb,{flag:'wx'});
const record={name:'The Many Trails',image:'https://api.imd.fun/artifacts/'+sha(png),attributes:[
  ['Cave','Crystal'], ['Wall','Line 3'], ['Number',38], ['Left behind','Search Batch'],
  ['Meaning','Three ochre search stones follow charcoal trails to a cited white source.'],
  ['One thing','Offline document search with exact source line citations']
].map(([trait_type,value])=>({trait_type,value}))};
fs.writeFileSync('dist/line-3/38.json',JSON.stringify(record,null,2)+'\n',{flag:'wx'});
const report={wall:nextPath,format:'PNG',dimensions:[1254,1254],mode:'RGB',bytes:png.length,
  sha256:sha(png),ancestor_sha256:sha(priorBytes),generated_draft_sha256:sha(draftBytes),
  new_mark_rectangle:rect,pigment_pixels:classes,changed_pixels:changed,
  changed_pixels_outside_rectangle:outside,
  thumbnail:{path:'dist/line-3/38.jpg',format:'JPEG',dimensions:[512,512],bytes:thumb.length},
  hand_review:{new_hands:0,new_handprints:0,inherited_main_spread_hand_visible_digits:5,
    inherited_gripping_hand_total_digits:'unverified due to occlusion; unchanged'},
  visual_review:'Pending final inspection',
  unmet_visual_requirements:['An inherited partly occluded gripping hand cannot be confirmed to have five digits; preserved unchanged.']};
fs.writeFileSync('line-3/IMAGE-38.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
