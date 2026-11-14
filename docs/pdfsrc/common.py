"""Shared design and helpers for the AstroFlare PDFs (HTML printed to PDF by Edge)."""
import html as _html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'engine'))
FONTS = (ROOT / 'public').as_uri()
DATE = '14 November 2026'


def esc(s):
    return _html.escape(str(s), quote=False)


CSS = """
@font-face{font-family:'Instrument Serif';src:url('%(f)s/InstrumentSerif-400.ttf')}
@font-face{font-family:'Instrument Sans';font-weight:400;src:url('%(f)s/InstrumentSans-400.ttf')}
@font-face{font-family:'Instrument Sans';font-weight:600;src:url('%(f)s/InstrumentSans-600.ttf')}
@font-face{font-family:'Instrument Sans';font-weight:700;src:url('%(f)s/InstrumentSans-700.ttf')}
:root{--ink:#111;--muted:#555;--faint:#767676;--line:#d9d7d2;--blue:#b9ddf3;--green:#b9e6c5;--blue-deep:#2b6f9e;--green-deep:#2f7a47}
@page{size:A4;margin:22mm 20mm 24mm 20mm}
@page{@bottom-left{content:string(doctitle);font:8pt 'Instrument Sans',sans-serif;color:#767676;letter-spacing:.08em;text-transform:uppercase}
      @bottom-right{content:counter(page) ' / ' counter(pages);font:8pt 'Instrument Sans',sans-serif;color:#767676}}
@page :first{margin:0;@bottom-left{content:''}@bottom-right{content:''}}
*{box-sizing:border-box}
html{font:9.6pt/1.55 'Instrument Sans',system-ui,sans-serif;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0}
.docname{string-set:doctitle content(text);display:none}
h1,h2,h3{font-family:'Instrument Serif',Georgia,serif;font-weight:400;margin:0;letter-spacing:-.01em;line-height:1.1;break-after:avoid}
h1{font-size:30pt;margin:0 0 4mm;padding-top:2mm}
h1::before{content:'';display:block;width:16mm;height:2.4mm;background:var(--blue);margin-bottom:5mm}
h2{font-size:17pt;margin:8mm 0 2.5mm}
h3{font-size:12.5pt;margin:5.5mm 0 1.5mm}
h4{font:700 7.8pt 'Instrument Sans';letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:4.5mm 0 1.2mm;break-after:avoid}
p{margin:0 0 2.6mm;max-width:none;orphans:3;widows:3}
ul,ol{margin:0 0 3mm;padding-left:5mm}li{margin:0 0 1mm}
a{color:var(--ink);text-decoration:underline;text-decoration-color:var(--blue);text-decoration-thickness:1.4pt;text-underline-offset:1pt}
code{font:8.4pt Consolas,'Cascadia Mono',monospace;background:none;border-bottom:.5pt solid var(--line);padding:0 .6mm}
pre{font:7.8pt/1.45 Consolas,'Cascadia Mono',monospace;border-left:1.2mm solid var(--blue);padding:1.5mm 0 1.5mm 4mm;margin:0 0 3.5mm;white-space:pre-wrap;break-inside:avoid}
.lede{font:14pt/1.4 'Instrument Serif',Georgia,serif;color:#333;margin:0 0 5mm;max-width:150mm;border-left:1.2mm solid var(--green);padding-left:4.5mm}
.pagebreak{break-after:page}
section.page{break-before:page}
table{border-collapse:collapse;width:100%;margin:1.5mm 0 4.5mm;font-size:8.6pt;line-height:1.4}
th{font:700 7.2pt 'Instrument Sans';letter-spacing:.1em;text-transform:uppercase;text-align:left;border-bottom:.9mm solid var(--blue);padding:1.4mm 3mm 1.4mm 0;color:#222}
td{border-bottom:.3mm solid var(--line);padding:1.5mm 3mm 1.5mm 0;vertical-align:top}
tr{break-inside:avoid}
td.n,th.n{text-align:right;white-space:nowrap}
td.ok{color:var(--green-deep);font-weight:700}td.bad{color:#a33;font-weight:700}
.note{border-left:1.2mm solid var(--blue);padding:.5mm 0 .5mm 4.2mm;margin:3mm 0 4mm;break-inside:avoid}
.note.g{border-left-color:var(--green)}
.note b{font-weight:700}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:0 9mm}
.cols3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 7mm}
.stat{border-top:.8mm solid var(--blue);padding-top:2mm;margin-bottom:4mm}
.stat.g{border-top-color:var(--green)}
.stat .v{font:24pt 'Instrument Serif',serif;line-height:1}
.stat .l{font:600 7.4pt 'Instrument Sans';letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:1.2mm}
figure{margin:3mm 0 5mm;break-inside:avoid}
figcaption{font-size:8pt;color:var(--muted);margin-top:1.5mm}
.toc{columns:2;column-gap:10mm;font-size:9.6pt}
.toc div{display:flex;gap:3mm;border-bottom:.3mm solid var(--line);padding:1.2mm 0;break-inside:avoid}
.toc span.n{font:12pt 'Instrument Serif';min-width:7mm}
/* cover */
.cover{height:297mm;width:210mm;position:relative;padding:26mm 22mm;break-after:page;overflow:hidden}
.cover .bar{width:34mm;height:5mm;background:var(--blue);margin-bottom:12mm}
.cover .kicker{font:700 8pt 'Instrument Sans';letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-bottom:5mm}
.cover h1{font-size:64pt;line-height:.95;margin:0 0 7mm;padding:0}.cover h1::before{display:none}
.cover .sub{font:19pt/1.3 'Instrument Serif',serif;color:#333;max-width:130mm;border-left:2mm solid var(--green);padding-left:6mm;margin-bottom:14mm}
.cover .meta{position:absolute;left:22mm;right:22mm;bottom:24mm;display:grid;grid-template-columns:repeat(3,1fr);gap:8mm;border-top:.4mm solid var(--ink);padding-top:5mm}
.cover .meta div{font-size:8.6pt;color:var(--muted)}.cover .meta b{display:block;font:700 7pt 'Instrument Sans';letter-spacing:.14em;text-transform:uppercase;color:#222;margin-bottom:1mm}
"""


def page(title, body, doctitle):
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>%s</title><style>%s</style>'
            '<body><span class="docname">%s</span>%s</body></html>' % (esc(title), CSS.replace('%(f)s', FONTS), esc(doctitle), body))


def cover(kicker, title, sub, meta):
    m = ''.join('<div><b>%s</b>%s</div>' % (esc(k), v) for k, v in meta)
    return '<div class="cover"><div class="bar"></div><div class="kicker">%s</div><h1>%s</h1><div class="sub">%s</div><div class="meta">%s</div></div>' % (esc(kicker), title, sub, m)


def table(headers, rows, num=()):
    h = ''.join('<th%s>%s</th>' % (' class="n"' if i in num else '', esc(x)) for i, x in enumerate(headers))
    b = ''
    for r in rows:
        b += '<tr>' + ''.join('<td%s>%s</td>' % (' class="n"' if i in num else '', c if isinstance(c, str) and c.startswith('<') else esc(c)) for i, c in enumerate(r)) + '</tr>'
    return '<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (h, b)


def note(text, green=False):
    return '<div class="note%s">%s</div>' % (' g' if green else '', text)


def stat(v, l, green=False):
    return '<div class="stat%s"><div class="v">%s</div><div class="l">%s</div></div>' % (' g' if green else '', v, esc(l))


def toc(items):
    return '<div class="toc">%s</div>' % ''.join('<div><span class="n">%d</span><span>%s</span></div>' % (i + 1, esc(t)) for i, t in enumerate(items))


def svg_text(x, y, s, size=11, weight=400, fill='#111', anchor='start', serif=False):
    fam = "'Instrument Serif',serif" if serif else "'Instrument Sans',sans-serif"
    return '<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" fill="%s" text-anchor="%s">%s</text>' % (x, y, fam, size, weight, fill, anchor, esc(s))
