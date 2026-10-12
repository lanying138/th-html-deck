#!/usr/bin/env python3
"""Tile page screenshots into one contact-sheet image for cheap visual review.
Usage: python3 contact_sheet.py <out.png> <img1> <img2> ... [--cols N] [--cell WxH]
Default: 3 columns, 800x450 cells (16:9). Read the sheet instead of each page.
"""
import sys
from PIL import Image

args = [a for a in sys.argv[1:]]
out = args[0]
cols = 3
cw, ch = 800, 450
imgs_arg = []
i = 1
while i < len(args):
    a = args[i]
    if a == '--cols':
        cols = int(args[i + 1]); i += 2; continue
    if a == '--cell':
        cw, ch = map(int, args[i + 1].split('x')); i += 2; continue
    imgs_arg.append(a); i += 1

imgs = [Image.open(p).convert('RGB').resize((cw, ch)) for p in imgs_arg]
rows = (len(imgs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cw, rows * ch), '#151515')
for k, im in enumerate(imgs):
    sheet.paste(im, ((k % cols) * cw, (k // cols) * ch))
sheet.save(out)
print('saved', out, len(imgs), 'pages', sheet.size)
