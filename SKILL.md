---
name: tianhong-html-deck
description: Builds and edits 天弘-style fullscreen single-file HTML presentation decks (cool fintech dark style by default, plus white theme) from fragment JSON, redraws architecture diagrams natively in HTML/CSS instead of recolored bitmaps, runs visual QA via headless Chrome/CDP, and exports print-faithful PDF. Use when converting PPT/reports into web decks, redrawing architecture/流程图 pages, editing divider pages, adding a white version, or exporting deck PDFs.
version: 2.1.0
enabled_at: 1790218528144
---

# 天弘科技对外材料 HTML Deck 流水线

End-to-end recipe for producing a fullscreen, offline, single-file HTML deck in the cool fintech dark house style (plus an optional white version), keeping them in sync, QA-ing visually, and exporting a print-faithful PDF. Reuse this for every new 汇报/评审/奖项 material. v2 adds the native HTML/CSS architecture-diagram redraw pipeline (crisp text, scalable, style-unified) replacing recolored raster embeds.

## Step 0 — style default + redraw scope (MANDATORY, ask the user)
1. Default look is the 酷炫金融科技风 dark house style: `--bg:#060e1b` + cyan/gold glow, ambient starfield, HUD corner brackets (`.diagram-frame`), letter-spaced kickers. Produce the white/light build only on request or for print.
2. Inventory the source: list every page whose body is an architecture/flow diagram image (from PPTX renders or extracted shapes).
3. BEFORE drawing, use AskUserQuestion: "哪些页的架构图需要原生 HTML/CSS 重绘？" with options: 全部架构图页（推荐，文字清晰/可缩放/风格统一）/ 仅指定页（用户给页码，其余页保留重着色位图）/ 全部保留位图. Record the answer; only selected pages go through the native pipeline below.
4. Also confirm enrichment appetite if unclear: native redraws may add model-inferred complements (see "Content enrichment").

## Canonical house project (copy as starter)
A complete working project lives at:
`/Users/guobin/.qoderwork/workspace/mu3udn5g0ld8tvy6`
It contains the house `shell.html` (all CSS/JS), `assemble.py`, `audit_html.py`, fragment JSONs (`main/research/wealth/ai_slides.json`), QA scripts, and `outputs/`. For a NEW material, copy `shell.html + assemble.py + audit_html.py + qa scripts` into the new workspace and swap the fragment JSONs + source list. Do NOT rebuild the shell from scratch — it encodes the house style and the light-theme remap asserts. A second worked example with the v2 native-diagram pipeline (8-page deck, per-page `build_bodies.py` specs + `assemble8.py` EXTRA_CSS injection) is at `/Users/guobin/.qoderwork/workspace/mu68b0rv3ayrtzk6/work`.

## Architecture
- `shell.html` — ALL css/js (stage, slides, nav, dialogs, print rules, theme vars, house component classes). assemble.py only stitches; it does not hold CSS.
- Fragment JSONs — one file per act; key = page number; fields `title/kicker/subtitle/body/quote`. `body` is raw HTML using house classes + inline styles. Per-page `bodystyle` (inline `top/height` on `.slide-body`) budgets vertical space per density.
- `assemble.py` — loads shell + fragments + a per-page `source` text list (for audit + 原稿 dialog) + base64 assets; emits dark by default and light with `python3 assemble.py light`. A third theme `python3 assemble.py master [combo]` ports the 《技术研发部PPT模版-打印版》 slideMaster (white canvas, brand red #B7002E, grey-band chrome) — chrome geometry, tokens and porting pitfalls in references/master-theme.md. Project-specific component CSS (e.g. the native arch library) is injected as an EXTRA_CSS block here, not in shell.
- `audit_html.py [filename]` — asserts section count, exact source text retained, assets valid, 0 external deps. Run after EVERY rebuild, for BOTH builds.

## House style constants
- Dark `:root`: `--bg:#060e1b;--panel:#0b1b2b;--fg:#edf4f5;--muted:#99adbd;--cyan:#64e1e8;--gold:#d8b77d;--line:rgba(149,186,201,.18)`
- Light `:root`: `--bg:#ffffff;--panel:#f5f8fa;--fg:#1e2d3d;--muted:#5b6d80;--cyan:#0b7f8e;--gold:#a2761a;--line:rgba(30,60,90,.16)`
- Font stack `"PingFang SC","Microsoft YaHei",Arial,sans-serif` (this mac has NO YaHei; Windows falls back gracefully).
- Stage 1600×900; `.slide-body{left:72px;right:72px;top:214px;height:560px}` → usable width 1456px. Remember this when budgeting column widths. Dense diagram pages override per page, e.g. `top:186px;height:616px` with `subtitle=''`.
- Boundary feel (dark): outer border rgba alpha .45–.55, inner cells .32–.4, base fill .06–.1; add border separators on label cells/titles.
- White-version stage: grid overlay off; cool-blue radial top-right + warm-gold radial bottom-left + white-center linear; `#ambient` opacity .3; panels white gradient + `rgba(23,48,77,.05-.07)` soft shadow.

## Native architecture-diagram redraw (v2 core)
Why: recolored bitmaps blur at projection zoom, fight the house palette, and bloat the file (base64). Native HTML/CSS keeps every module label crisp, scalable, theme-consistent, editable, and cuts ~2MB per deck.

Extraction (fidelity first — never replace diagrams with abstract cards):
1. `pdftoppm -r 200` the PPTX-exported PDF (osascript PowerPoint: `activate`+`open` in one tell, `delay 8`, separate tell `save ... as save as PDF`; avoids -1712/-9074/-2753).
2. python-pptx text in DOCUMENT ORDER for the module list; nested-group transforms are unreliable — use the high-res render crops to infer logical grouping (which chips sit under which panel title).
3. Keep the source module list 1:1; layer/section titles stay INSIDE their layer (`.ptitle`/`.asub`), vertical layer names use `.rail`.

Components: paste `templates/arch_lib.css` into the project EXTRA_CSS and build bodies with `templates/arch_helpers.py` (`chips/lrow/panel/sub/rail/flow/band/note`). Core grammar: page body = `<div class="arch [loose|mid]">` stacking `.arow` rows; the row that must absorb leftover height gets `.arow.fill`; panels inside it get `grow=True`.

Density tiers (pick per page, then verify by screenshot):
- `loose` — sparse pages (≤3 content rows: overview/flow/menu pages). Big type (chip 15px, note 15.5px), rows spread via space-between.
- default — medium pages (one big workstation grid).
- `mid` — dense pages (4+ stacked chip rows / rail rows). chip 12.5px, rail 13px. NEVER below 11.5px type; if a column still overflows at `mid`, trim gaps/paddings or raise the page `bodystyle` height before shrinking fonts.
- `.chip.t` (11.5px, wraps) for narrow many-chip columns — prevents ellipsis truncation; give chip-heavy panels a numeric flex (`grow=1.6` vs `grow=0.8`) so labels fit.

Fill recipes (kill dead space, user hates empty margins):
- Vertical: `pcls='spread'` on columns shorter than their tallest sibling — `.apanel.spread` space-between + nested grids `align-content:space-evenly` distributes rows over full column height.
- Horizontal: chip grids beside a rail get `gcls='rowfill'` (flex:1 + `align-self:center` so chips don't stretch into tall boxes); conclusion `.band` rows get `grow=True` so bands span the stage.
- Prose columns: `.arch.loose .note` 15.5px/1.95 justified; unequal text columns keep equal-height panels (stretch) — that is expected, not a bug.

Content enrichment (model judgment, allowed and encouraged):
- May add complements that make the diagram read complete: explicit `›`/`+` arrows between stages the source implies, grouping sub-captions, a closing summary `.band`, legend/footnote `.note`, consistent layer naming, HUD frame around the whole diagram.
- MUST be derivable from source text (no invented modules, metrics, or product names); keep an enrichment list and disclose it in the final summary so the user can veto items.

QA loop for redrawn pages:
1. Rebuild → screenshot each redrawn page headless (see Build & QA loop). `rm` the old png FIRST: headless Chrome can fail silently and leave a stale shot, which reads as "still broken".
2. Contact sheet (2 cols) for cross-page density/consistency; then full-res Read of any page with suspected overflow.
3. Overflow rule: bottom bands/rows must clear `.slide-quote`; if they collide, trim gaps/paddings/`bodystyle`, not fonts.
4. CDP `measure.js` rects can DISAGREE with the screenshot when `#stage` scale≠1 — for overflow calls trust the 1600×900 screenshot (ground truth), use CDP only for wrap/width questions with the mandated window flags.
5. When the native redraw is final, drop the now-unused recolored webp assets from the assembler (file size −50%+); keep the 原稿-dialog originals.

## Recolored-raster fallback (pages not selected for native redraw)
HSV recolor into the dark palette: grayscale (S<0.10) → invert luminance `V'=0.055+0.90*(1-V)`, H=0.575, S=0.30; hue remap red/orange→0.50, yellow→0.105, green→0.45, blue→0.53, purple→0.56; light fills (V>0.80,S<0.45)→V0.145/S0.55; solids (S≥0.45,V>0.35)→V0.80/S0.62. Crop title bands via gray-band row detection (|px−242|max≤6, run>0.35·W, gap tolerance 260 rows). Embed OPAQUE with panel bg matched to image bg (#090c0e) — PIL floodfill hangs >2min at 5000px, never use it. Wrap in `.diagram-frame` for HUD brackets.

## Light-theme remap (keep both builds in sync)
- `INLINE_FAM`: rgba-family prefixes converted in fragment inline styles, e.g. `rgba(76,216,232,`→`rgba(11,127,142,`, `rgba(217,189,139,`→`rgba(162,118,26,`, and regex `rgba(22,48,73,<a>)`→`rgba(44,76,108,.06)`.
- `INLINE_HEX`: `#4cd8e8`→`#0e8fa0`, `#d9bd8b`→`#a2761a`, etc.
- `SHELL_LIGHT`: list of exact `(old,new)` string pairs applied to shell.html; assemble ASSERTS each old appears exactly once. When you edit shell CSS that differs per theme, add/refresh a pair here or the assert fails.
- Rule: any fragment edit must be rebuilt in EVERY shipped build (`assemble.py`, `assemble.py light`, and `assemble.py master` when the master version is in scope) and audited once per build. Never overwrite one theme's output with another's. Master-theme remap coverage + porting pitfalls: see references/master-theme.md and references/lessons-learned.md.

## Build & QA loop
1. Edit fragment JSON → `python3 assemble.py` → `python3 assemble.py light`.
2. Screenshot pages: headless Chrome
   `--headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --window-size=1600,900 --screenshot=qa/<name>.png --virtual-time-budget=4000 "file://$PWD/outputs/<file>.html#<N>"`
3. Multi-page review: PIL contact sheet (resize each to 800×450, tile 2–3 per row) then Read the sheet — cheaper than reading pages individually and shows cross-page consistency.
4. `python3 audit_html.py` and `python3 audit_html.py "<white file>"`.
5. For precise layout/wrap questions use CDP (see templates/measure.js). CRITICAL: pass `--window-size=1600,900 --force-device-scale-factor=1`, else `#stage` scale≈0.9 distorts rects. Wrap detection = `round(rect.height/lineHeight)`; do NOT use `scrollWidth` or a `white-space:nowrap` rect (both return the container width). `clientWidth` is unaffected by transform.

## Layout / visual pitfalls (hard-won)
- A flex wrapper containing a wide absolutely-positioned child is forced to the child's min-content width unless you set `min-width:0` on the wrapper.
- `transform:scale()` shrinks the VISUAL only, not the layout width — the wrapper still reserves the unscaled width.
- `.slide-body` already insets ~72px; adding horizontal padding to an inner hero double-counts and squeezes middle columns.
- A big display number (`font-size:300px`) has min-content WIDER than its `flex:0 0 300px` basis (≈320px). To reclaim width, reduce the FONT SIZE, not just the basis.
- Absolutely-positioned SVG over flow text always collides (dots over labels, checks crossing titles). Make each graphic a self-contained `position:relative` container and compute safe-area coords for shapes and text separately.
- `writing-mode:vertical-rl` layer names: 7 chars ×14px + `letter-spacing:5px` wraps to two columns past ~122px height; use `letter-spacing:2px`.
- Raster/grid diagram text desensitization: numpy color-threshold clustering → text bboxes → fill with background color → redraw with PingFang.ttc (SC Regular idx2 / Semibold idx8), font size fitted from glyph bbox height.
- HTML→editable-PPTX: layout extractors miss nested flex/grid children; rebuild such pages by hard-coding, not from extracted JSON. PPTX Chinese font = PingFang SC (no YaHei locally).
- Logos: white transparent PNG sits directly on the dark top bar (`height:24px` + light drop-shadow). A black logo on dark needs a white rounded plate behind it; check alpha extremes + dominant color with PIL before embedding.
- Grids with `repeat(N,1fr)` inside a flex row size to max-content unless the grid gets `flex:1` — rail rows then look ragged; always pair rail-row grids with `rowfill`.
- Equal-height flex columns + `justify-content:space-between` on a single-child panel pushes the child to the bottom; use `flex:1` on the child (or `spread` with ≥2 children) instead.

## Chapter-divider (navigation) page template
Pages 3/10/19/29 share one layout: gold display number + vertical rule + eyebrow + two-line headline (2nd line cyan) + single-line muted + right-side tilted 4-layer stack (`.foundation-visual/.foundation-slab/.slab1-4/.slab-axis`, reused from shell). Working geometry that keeps even the longest muted on ONE line: hero `gap:30px;padding:30px 0`; number `flex:0 0 280px;font-size:280px;letter-spacing:-18px`; text block `padding:30px 0 30px 42px`; stack wrapper `flex:0 0 470px;min-width:0` with `transform:translateX(8px) scale(.82)`. Metadata convention: `title=幕名·主题`, `subtitle=第X幕｜语句`, `quote=""`.

## PDF export
Use templates/topdf.js (Node + CDP `Page.printToPDF{printBackground:true,preferCSSPageSize:true}`); `@page{size:1600px 900px;margin:0}` yields 1200×675pt landscape pages.
Two shell print rules are MANDATORY or the PDF is wrong:
- `.slide:last-of-type{break-after:auto;page-break-after:auto}` — otherwise the last slide's page-break emits a 41st blank page.
- `@media print{html,body{...background:var(--bg)}}` (NOT `white`) — the page-margin band is painted from the root background; white there shows as ugly side bars in fullscreen. Theme-aware var fixes both themes.
Verify: `pdfinfo` page count == slide count; `pdftoppm -png -r 150` then scan edge pixels (x=0 and x=w-1 across several rows) — must equal theme bg, not white.

## Content conventions for external materials
- Desensitize person names in outward-facing versions.
- Narrative order for tech outreach: 科技底座 → 投研 → 销售科技 → AI与荣誉; investment-research pages must cover 权益/指数量化/固收/固收+ and keep original architecture diagrams as the主体 (native redraw preferred, recolored raster acceptable; never abstract cards).
- Architecture diagrams: layer/section titles must stay INSIDE their layer (no straddling borders); thin layers use left-inset labels, thick layers use a vertical rail.
- User preferences (this owner): no tiny fonts, no large empty margins — content must fill the stage; when in doubt raise type size and spread rows, don't shrink to fit.

## Master-theme page-ops playbook (2026-09 rounds)
Fragment authoring palette for master (write DARK inline values; the remap chain converts them):
- Red accent `#53d5e6` + tint `rgba(83,213,230,.06-.10)` + class `.cyan`; gold workflow accent `rgba(226,197,143,.06/.35)` + class `.accent`.
- Panel fill `#0c223566` or `rgba(19,43,69,.8)`; inner cards `rgba(12,34,53,.55)`; borders `rgba(154,181,204,.22/.28/.35)`; muted `#9ab5cc`; chip text `#b8cad9`.
- Screenshot zones: white plate `background:#fff;border:1px solid rgba(154,181,204,.35);border-radius:10px` with 10.5-12px bar labels/captions in `#516374`; EVERY embedded screenshot gets `class='zoomable'`; phone mocks = fixed w/h + `object-fit:cover` + radius 6 + caption.
- Proven body skeletons (inner width 1456, `height:560px;display:grid;gap:16px`): rows `150px 64px 1fr` (3 cards + THEREFORE band + 3 columns), `272px 272px` (two horizontal blocks), cols `168px 1fr 250px 516px` (label | compressed text | big-stat tint | image zone).
- Dense company-wide architecture redraw (≈128 leaf modules, p8 2026-09): two-band grid `34px rail | 1fr`, rows `410px 194px`; top band `485fr 515fr` = the two big domains (asset/channel rail × 2 center columns matrix), bottom band `1fr 1fr 1fr` = the three small domains (center columns + optional full-width band). CRITICAL: matrix rows must be AUTO-height (`flex:none`, content-sized) with `justify-content:space-between` on the matrix wrapper to absorb leftover — `flex:1` equal rows shrink 2-chip-line rows below content and chips paint ACROSS the next row's border (user veto: "功能框与其他的重叠…不要线的重叠"). Compress the bottom band to buy top-band height: compact chips (11px/1px pad), domain padding 6, domain title 13px. Center-panel internal layout (owner-mandated for the small domains): title PINNED TOP (`flex:none`) so all center names in a domain share one baseline, then chips in a `flex:1;min-height:0` wrapper with `align-content:center;justify-content:center` so each column's chip block is vertically+horizontally centered in the equal-height leftover — reads aligned & symmetric; do NOT center the title+chips as one block (titles then drift to different heights). SEAM RULE: a domain flex column has NO gap, so any block placed right after the matrix (交易中心 bottom_block, centers_row) needs `margin-top:8px` or its top border fuses with the last matrix row's bottom border into a double line (owner veto: "边框线叠在一起了"). Because only the master build ships, authoring in LITERAL master palette is acceptable and pixel-exact: red `#b7002e`, red tint `rgba(183,0,46,.06/.12)`, inner `#f8fafc`/`#d6dee6`, row border `#cfd8e0`, cream chips `#fcf6e0/#e2cea6/#604a20`, rail `#b7002e` bg + `#fff` vertical-rl text. Dropping the raster reference auto-shrinks the file (assets 28→27, −480KB).

Asset & builder pitfalls:
- `{{asset:name}}` inside Python f-strings MUST be written `{{{{asset:name}}}}`; single-brace collapse yields assemble `AssertionError: Unresolved asset NN` or imgs with nat 0x0. Repair regex: `\{\{asset:([\w.]+)\}(?!\})` → `{{asset:\1}}`. Verify via `body.count('{{asset:')` and assemble's `assets:` count bump.
- Builder scripts that rewrite a fragment JSON: `d.pop(key,None)` BEFORE ordered re-insert, else iterating the stale key overwrites the fresh fragment.
- Back up per round: `cp wealth_slides.json wealth_slides.json.bak-<tag>`.

Page-insert / renumber checklist (e.g. 46→47): shift fragment keys in ALL fragment JSONs → positional `insert()` in source.json → shell.html (topnav `data-goto`, go() next-chain, `共N页`, `c0` chapter array) → escaped `data-goto` inside fragment bodies → assemble.py (`count=`, closing page number, chapter list) → audit_html.py `==N` asserts (two places) → grep-verify each token's occurrence count.

QA ops:
- `assemble.py` does NOT implement a `bodystyle` fragment field (it is silently ignored). To give a dense page more than the default 560px body, put the height on the body wrapper div itself plus a negative top margin, e.g. `height:616px;margin-top:-30px;display:grid` (occupies 186..802, clears the ~827 quote line). Do not add a `bodystyle` key expecting it to work.
- Because of the over-height wrapper, shot.mjs `overflow:[...]` is measured against the 560px `.slide-body` rect and WILL list bottom-band chips as false positives; trust the screenshot for collision calls (quote line ~827, footer ~880).
- Project screenshot helper is `node shot.mjs "<html filename in outputs/>" <tagPrefix> <pages...>` writing `qa/<tag>p<n>.png` at 1600×900 (there is no /tmp/page_shot.mjs after reboots).
- Node measure/shot scripts need `$PWD`-ABSOLUTE html and out paths (relative → file:// load fail → infinite `window.presentation` wait; pkill stray headless Chrome afterwards).
- Stale-shot trap stands, but bundling `rm -f old.png` into the shot command was permission-DENIED by the user — shoot to a FRESH filename each round (m29b/m29c/…) and verify mtime/size instead.
- `bad:[]` from the measure script ≠ no visual clipping: panels without `overflow:hidden` let chips/rows paint across their border. Always Read the screenshot for dense cards. Vertical budget per 150px card: padding 32 + title 33 + p-line 22.5 + chip row ≈23 + gaps.
- CJK chip width ≈ chars×font-size + 2·padH + 2; row capacity = panel inner width; shorten labels (e.g. 问卷·红包·广告回传包装) to force the wanted wrap rows.
- Inline-grid arch columns: `flex:1;min-height:0` on inner boxes kills dead space; an eyebrow like `SERVICE WORKFLOW` in a 168px label column only stays one line at ≤10.5px + `letter-spacing:1px`.

Redesign workflow (owner-mandated):
- Draft first: PIL 1920×1080 wireframe (PingFang.ttc idx0/idx1) with REAL screenshots pasted → present_files → AskUserQuestion BEFORE implementing; if the user interrupts with "重新让我选择下", re-issue AskUserQuestion with the built screenshot attached.
- Redesigning an existing page: keep the ORIGINAL punchy copy and quantified stats verbatim (a rewrite that dropped them was vetoed: "保留原版文字…有效果量化数字"); compress text left, images right as 示意; strong block design (16px-radius blocks, per-workflow accent color).
- Delivery discipline: ship ONLY 母版版.html per round to /Users/guobin/Downloads/汇报Fintech/; never report "delivered" before running assemble + cp + ls-verify (past failure: user asked "怎么没有看到第46页" because a rebuild was skipped).

## Bundled templates
- `templates/arch_lib.css` — native architecture-diagram component library (arch/arow/apanel/chip/lrow/rail/fnode/band/note + loose/mid density tiers + spread/rowfill/chip.t fill modifiers). Paste into project EXTRA_CSS.
- `templates/arch_helpers.py` — Python builders for those components (chips/lrow/panel/sub/rail/flow/band/note with gcls/pcls/grow params).
- `templates/topdf.js` — CDP PDF exporter (args: in.html out.pdf).
- `templates/measure.js` — CDP layout/wrap measurer (args: file.html; prints per-page column widths + line counts for divider pages).
- `templates/contact_sheet.py` — tile screenshots into one review image.
- `templates/shot.sh` — per-page headless screenshot loop.
- `templates/verify_pdf.py` — checks page count + scans edge pixels for white side bands (exit 0 = good).
