# -*- coding: utf-8 -*-
"""Builder helpers for native HTML/CSS architecture diagrams (tianhong-html-deck).
Emit body HTML using the component classes in templates/arch_lib.css.
Copy these functions into the project's build_bodies.py and compose per-page specs."""


def chips(items, cols, cls='', gcls=''):
    """Grid of module chips. cls: chip variant ('gold','solid','t'); gcls: grid variant ('rowfill')."""
    c = (' ' + cls) if cls else ''
    g = (' ' + gcls) if gcls else ''
    return '<div class="agrid%s" style="grid-template-columns:repeat(%d,minmax(0,1fr))">' % (g, cols) + \
        ''.join('<div class="chip%s">%s</div>' % (c, i) for i in items) + '</div>'


def lrow(label, items, cols, cls=''):
    """Labelled row: right-aligned layer label + chip grid (use for 层→模块 mappings)."""
    return '<div class="lrow"><div class="ll">%s</div>%s</div>' % (label, chips(items, cols, cls))


def panel(title, inner, tcls='', grow=False, pcls=''):
    """Bordered panel. title=None for titleless; tcls: 'gold'; grow=True|<float flex ratio>;
    pcls='spread' distributes children vertically to kill dead space at column bottoms."""
    t = '<div class="ptitle %s">%s</div>' % (tcls, title) if title else ''
    g = ''
    if grow is True: g = ' style="flex:1"'
    elif grow: g = ' style="flex:%s"' % grow
    pc = (' ' + pcls) if pcls else ''
    return '<div class="apanel%s"%s>%s%s</div>' % (pc, g, t, inner)


def sub(t, cls=''):
    """In-panel section caption (gold underline; 'cyan' variant)."""
    return '<div class="asub %s">%s</div>' % (cls, t)


def rail(t, cls=''):
    """Vertical writing-mode layer rail (left edge of a row); 'gold' variant for model columns."""
    return '<div class="rail %s">%s</div>' % (cls, t)


def flow(nodes, arr='›'):
    """Horizontal process flow: node › node › node (centered, nowrap)."""
    out = []
    for i, n in enumerate(nodes):
        if i: out.append('<div class="farr">%s</div>' % arr)
        out.append('<div class="fnode">%s</div>' % n)
    return '<div class="arow" style="align-items:center;justify-content:center;flex-wrap:nowrap">%s</div>' % ''.join(out)


def band(t, cls='', grow=False):
    """Full-width conclusion band; grow=True makes it share the row width (flex:1)."""
    g = ' style="flex:1;min-width:0"' if grow else ''
    return '<div class="band %s"%s>%s</div>' % (cls, g, t)


def note(t):
    """Muted prose block (paragraph columns)."""
    return '<div class="note">%s</div>' % t
