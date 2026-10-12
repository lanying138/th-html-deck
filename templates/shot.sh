#!/bin/zsh
# Per-page headless screenshots of a deck for visual QA.
# Usage: ./shot.sh <theme-prefix> <output.html> <page> [page ...]
# Writes qa/<prefix>p<page>.png at true 1600x900 (scale forced to 1).
prefix="$1"; file="$2"; shift 2
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p qa
for p in "$@"; do
  "$CH" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1600,900 \
    --screenshot="qa/${prefix}p${p}.png" --virtual-time-budget=4000 \
    "file://$PWD/$file#$p" >/dev/null 2>&1
done
echo "shots: $(ls qa/${prefix}p*.png | wc -l | tr -d ' ')"
