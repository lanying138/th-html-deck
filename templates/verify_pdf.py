#!/usr/bin/env python3
"""Verify a deck PDF: page count + no white side bands (fullscreen letterbox check).
Usage: python3 verify_pdf.py <file.pdf> <expected_pages> [theme_bg_hex]
Rasterizes page 1 at 150dpi, scans left/right edge columns across rows.
Dark theme default bg #060e1b; pass e.g. #ffffff for the white version.
"""
import subprocess, sys, tempfile, os
from PIL import Image

pdf, expect = sys.argv[1], int(sys.argv[2])
bg = sys.argv[3].lstrip('#') if len(sys.argv) > 3 else '060e1b'
bg = tuple(int(bg[i:i+2], 16) for i in (0, 2, 4))

info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
pages = int([l for l in info.splitlines() if l.startswith('Pages:')][0].split(':')[1])
ok_pages = pages == expect

tmp = tempfile.mkdtemp()
subprocess.run(['pdftoppm', '-png', '-r', '150', '-f', '1', '-l', '1', pdf,
                os.path.join(tmp, 'p')], capture_output=True)
img = Image.open(sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith('.png'))[0]).convert('RGB')
w, h = img.size
px = img.load()

def near(c, t, tol=26):
    return all(abs(a - b) <= tol for a, b in zip(c, t))

bad = []
for y in [0, h // 4, h // 2, 3 * h // 4, h - 1]:
    if not near(px[0, y], bg) or not near(px[w - 1, y], bg):
        bad.append((y, px[0, y], px[w - 1, y]))

print({'pdf': os.path.basename(pdf), 'pages': pages, 'expected': expect,
       'pages_ok': ok_pages, 'edge_bands_ok': not bad, 'bad_rows': bad[:3]})
sys.exit(0 if (ok_pages and not bad) else 1)
