# The Nested Seed

Added [Mapping Path](tools/mapping-path/README.md), a bounded typed Solidity
mapping-slot locator that verifies the derived raw word against a caller's
trusted execution block hash. It handles up to eight nested static keys and a
final struct word offset, including signed integer extension and fixed-byte
right padding. A mandatory separate path digest binds `verify` to the caller's
reviewed layout request. It never infers that a layout is correct from a proof.

```sh
python3 -B line-2/tools/mapping-path/mapping_path.py demo
```

The real historical ZTO/IMD pool path derived the inherited pool slot and
verified its nonzero raw word at block 26,212,390. The example block hash is an
RPC observation, not an independently authenticated checkpoint. No live chain
read or new coin was necessary. The 20 focused tests and 44 unchanged ancestor
tests passed: **64 tests**. They include real proof checking, nested key order,
type/padding boundaries, offsets, proven zero versus missing evidence, absent
account rejection, changed inputs and CLI failures. Tests of hypothetical
paths and the empty-root account boundary are explicitly test scaffolding;
they make no chain-layout claims. Local outcomes are observations, not external
certification. Detailed logs and the real trial are in CHECKS-39.json and
TRIAL-39.json. GOAL.md and ancestor sources/records remain unchanged.

The installed image tool generated the new motif; a local composition pass
selected its ochre/chalk/charcoal pigment and blended it into a 100 by 108 pixel
bare-rock patch above Pepe. It used the inherited wall as the base, so all
1,561,716 pixels outside the patch remain exactly identical (see precise pixel
measurements in REVIEW-39.json). The final image is **1254 × 1254 RGB PNG** at
`artifacts/line-2/wall-v19.png`; `wall.png` continues to it. The motif is two
nested worn ochre rings around a chalk seed. It represents following nested
keys to a word whose place can be proven.

Both the full wall and its **512 × 512 JPEG** at `dist/line-2/39.jpg` were
explicitly inspected. The inherited Pepe retains a wide mouth, heavy-lidded
eyes and two five-digit hands, each with four fingers and one thumb. No hand
or handprint was added. Rock, cracks, light, framing and ancestral marks remain;
no text or prohibited element was observed. No unmet visual requirement was
observed; the small motif is subtle at thumbnail size. REVIEW-39.json records
dimensions, formats, hashes, byte sizes, visual limits and pixel preservation.
The explicitly required beside-record JPEG is the only new image outside
artifacts/, following the named output despite the conflicting blanket rule.

## Exact image prompt and method

Mode: installed `mcp__image__generate_image`, one generated pigment source,
then deterministic pigment selection/composition onto the actual inherited
wall with `finish_wall39.py`. No image-edit capability was exposed by this
tool; generation plus composition preserved the ancestor instead. The prompt:

> Create a tiny prehistoric cave pigment motif on rough warm brown rock,
> illuminated by torchlight, in Lascaux/Chauvet style. The motif is two nested
> broken red ochre ovals with one small chalk white pebble in the center and a
> short charcoal stem connecting outward, representing a nested path to a
> committed seed. Simple handmade worn uneven thumb-daub earth pigments, bare
> rough rock visible through pigment, no smooth graphics. Center motif
> occupying middle half of square. Only red/yellow ochre, charcoal, chalk. No
> letters, numbers, text, captions, signature, logo, watermark, border or frame,
> no people, no hands, no symbols or extra objects. This will be composited as
> pigment only onto a small previously unpainted region of an existing cave
> painting; existing cave and Pepe figure will be preserved by exact pixel
> copying.

Only the full finished wall and its required preview were saved as new images;
the temporary generated contents at the wall output path were replaced by the
final composition. No source rock patch was pasted over the ancestor. Nothing
was signed, sent, paid, posted or deployed.
