# Built-in imagegen edit prompt

Use case: precise-object-edit. Edit target: supplied ancestral square cave wall.
Keep its exact 1254x1254 size, rock, cracks, colors, torchlight, framing, Pepe
frog, hands and ALL existing ancestral paintings unchanged. Add ONLY a small
sparse prehistoric pigment mark on unused rock at x 760..850, y 1000..1060
(near lower center-right, above the dark horizontal ledge and below existing
ochre stone marks). Mark: two short charcoal dotted paths converging into one
small red ochre pebble. Handmade uneven worn earth pigments showing rock
through. No new figures or hands. No letters numbers captions signatures logos
watermarks borders or frames. Do not redraw or remove any existing mark.
Preserve all other pixels as closely as possible.

Target: inherited `artifacts/line-4/wall.png`. Transparency: false.
Method: built-in imagegen, then `finish_wall36.py` retained only generated pigment
within a small mask at the actual mark location. All ancestral pixels outside
the mask were restored exactly. No other image was retained in the workspace.
