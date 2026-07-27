#!/usr/bin/env python3
"""
P0 presentation-layer redesign transformer for eutariffguide.com.

This site is committed as pre-rendered static HTML (no generator/templates in
the repo). The two page "families" each have ONE uniform <header> block and one
uniform <style> block, so we apply the redesign by deterministic exact-string
replacement against those uniform fragments. Body content, titles, meta tags,
canonical links and JSON-LD are never touched -> no URL/SEO changes.

Changes applied site-wide:
  1. Design system CSS (mark/logo, single accent, type scale, sticky header,
     search dropdown, trust badge) appended into the existing inline <style>.
  2. Redesigned sticky header: wordmark + logo mark, trust badge text, working
     client-side search box, unified nav (dead /tools/ /about/ links removed).
  3. Calculator/FTA CTA repointed to https://try.eutariffguide.com.
  4. Search JS + lazy-loaded /search-index.json wired before </body>.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---- old header fragments (verified uniform across each family) -------------
HEADER_SIMPLE = (
    '<header>\n<div class="container">\n<nav>\n'
    '<span class="brand">EU Tariff Guide</span>\n'
    '<a href="/">Home</a>\n<a href="/chapters/">Chapters</a>\n'
    '</nav>\n</div>\n</header>'
)
HEADER_HS = (
    '<header>\n<div class="container">\n<nav>\n'
    '<span class="brand">EU Tariff Guide</span>\n'
    '<a href="/">Home</a>\n<a href="/chapters/">Chapters</a>\n'
    '<a href="/tools/">Tools</a>\n<a href="/about/">About</a>\n'
    '</nav>\n</div>\n</header>'
)

# ---- new sticky header (one consistent IA for every page type) --------------
NEW_HEADER = (
    '<header class="p0-header">\n'
    '<div class="container p0-bar">\n'
    '<a class="p0-brand" href="/">'
    '<span class="p0-mark">€</span>'
    '<span class="p0-word">EU Tariff Guide</span>'
    '</a>\n'
    '<div class="p0-search">'
    '<span class="p0-ico" aria-hidden="true">\U0001f50e</span>'
    '<input id="p0q" type="search" autocomplete="off" spellcheck="false" '
    'placeholder="Search 13,981 HS codes or products…" '
    'aria-label="Search HS codes">'
    '<div id="p0results" class="p0-results" role="listbox"></div>'
    '</div>\n'
    '<nav class="p0-nav">\n'
    '<a href="/chapters/">Chapters</a>\n'
    '<a class="p0-cta" href="https://try.eutariffguide.com">Calculator</a>\n'
    '</nav>\n'
    '</div>\n'
    '<div class="p0-trust container">'
    '<span class="p0-dot" aria-hidden="true"></span>'
    'Official EU TARIC data · updated daily · 13,981 codes'
    '</div>\n'
    '</header>'
)

# ---- design-system CSS injected before existing </style> --------------------
P0_CSS = """
/* ===== P0 redesign (presentation layer) ===== */
:root{--p0-ink:#0f1b2d;--p0-muted:#5b6b80;--p0-line:#e3e8ef;--p0-accent:#1b6ef3;--p0-accent-ink:#0b4fc0;--p0-good:#0a8a4a;--p0-good-soft:#e7f6ee;}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--p0-ink);}
.p0-header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.94);backdrop-filter:saturate(180%) blur(10px);border-bottom:1px solid var(--p0-line);color:var(--p0-ink);padding:0;font-size:14px}
.p0-bar{display:flex;align-items:center;gap:14px;height:58px}
.p0-brand{display:flex;align-items:center;gap:9px;font-weight:700;color:var(--p0-ink);font-size:17px;letter-spacing:-.2px;text-decoration:none;flex:none}
.p0-mark{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,var(--p0-accent),#0b4fc0);color:#fff;display:grid;place-items:center;font-size:15px;font-weight:800;flex:none}
.p0-word{white-space:nowrap}
.p0-search{position:relative;flex:1 1 auto;max-width:520px}
.p0-search input{width:100%;font-size:15px;padding:9px 12px 9px 38px;border:1.5px solid var(--p0-line);border-radius:11px;outline:none;background:#f6f8fb;transition:.15s;color:var(--p0-ink)}
.p0-search input:focus{border-color:var(--p0-accent);background:#fff;box-shadow:0 0 0 4px rgba(27,110,243,.12)}
.p0-ico{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--p0-muted);font-size:15px;pointer-events:none}
.p0-results{position:absolute;left:0;right:0;top:calc(100% + 6px);text-align:left;border:1px solid var(--p0-line);border-radius:12px;background:#fff;box-shadow:0 8px 24px rgba(16,30,54,.14);overflow:hidden;display:none;max-height:70vh;overflow-y:auto}
.p0-results.show{display:block}
.p0-results a{display:flex;gap:12px;align-items:baseline;padding:11px 14px;border-bottom:1px solid var(--p0-line);color:var(--p0-ink);text-decoration:none}
.p0-results a:last-child{border-bottom:0}
.p0-results a:hover,.p0-results a:focus{background:#f6f8fb}
.p0-results .code{font-variant-numeric:tabular-nums;font-weight:700;color:var(--p0-accent-ink);font-size:13px;flex:none}
.p0-results .desc{color:var(--p0-muted);font-size:13px;line-height:1.35}
.p0-results .chip{margin-left:auto;font-size:11px;color:var(--p0-muted);background:#f6f8fb;padding:2px 8px;border-radius:6px;flex:none}
.p0-results .empty{padding:14px;color:var(--p0-muted);font-size:13px}
.p0-nav{display:flex;gap:16px;align-items:center;font-size:14px;font-weight:500;flex:none}
.p0-nav a{color:var(--p0-muted);text-decoration:none}
.p0-nav a:hover{color:var(--p0-ink)}
.p0-nav .p0-cta{color:#fff;background:var(--p0-accent);padding:7px 14px;border-radius:9px;font-weight:600}
.p0-nav .p0-cta:hover{background:var(--p0-accent-ink);color:#fff}
.p0-trust{display:flex;align-items:center;gap:8px;color:var(--p0-good);font-size:12.5px;font-weight:600;padding-top:0;padding-bottom:8px}
.p0-bar+.p0-trust{margin-top:-4px}
.p0-dot{width:7px;height:7px;border-radius:50%;background:var(--p0-good);box-shadow:0 0 0 3px var(--p0-good-soft);flex:none}
.breadcrumb a{color:var(--p0-accent-ink)}
@media(max-width:640px){.p0-word{display:none}.p0-nav{gap:10px}.p0-nav a:not(.p0-cta){display:none}.p0-trust{font-size:11px}}
/* ===== end P0 redesign ===== */
"""

# ---- search JS injected before </body> --------------------------------------
P0_JS = """
<script>
(function(){
  var q=document.getElementById('p0q'),box=document.getElementById('p0results'),INDEX=null,loading=false;
  if(!q||!box)return;
  function load(cb){
    if(INDEX){cb();return;}
    if(loading)return;loading=true;
    fetch('/search-index.json').then(function(r){return r.json();}).then(function(d){INDEX=d;cb();}).catch(function(){loading=false;});
  }
  function esc(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function render(items){
    if(!items.length){box.innerHTML='<div class="empty">No matches. Try an HS code like 6404 or a product like \\u201cjacket\\u201d.</div>';box.classList.add('show');return;}
    box.innerHTML=items.map(function(it){
      return '<a href="/hs/'+it[0]+'/" role="option"><span class="code">'+it[0]+'</span><span class="desc">'+esc(it[1])+'</span><span class="chip">Ch '+it[2]+'</span></a>';
    }).join('');
    box.classList.add('show');
  }
  function run(term){
    term=term.trim().toLowerCase();
    if(!term){box.classList.remove('show');box.innerHTML='';return;}
    if(!INDEX){load(function(){run(q.value);});return;}
    var digits=term.replace(/\\D/g,'');
    var out=INDEX.filter(function(it){
      if(digits&&it[0].indexOf(digits)===0)return true;
      return it[1].toLowerCase().indexOf(term)!==-1;
    });
    out.sort(function(a,b){
      var ap=digits&&a[0].indexOf(digits)===0?0:1,bp=digits&&b[0].indexOf(digits)===0?0:1;
      return ap-bp;
    });
    render(out.slice(0,12));
  }
  q.addEventListener('focus',function(){load(function(){});});
  q.addEventListener('input',function(e){run(e.target.value);});
  document.addEventListener('click',function(e){if(!e.target.closest('.p0-search'))box.classList.remove('show');});
})();
</script>
"""

OLD_CTA = 'https://philippseyberth-lgtm.github.io/fta-duty-savings-landing/'
NEW_CTA = 'https://try.eutariffguide.com'

# dead footer links (point to non-existent /about/ and /tools/ pages)
OLD_FOOTER_LINKS = (
    '<p style="margin-top:8px"><a href="/about/">About</a> · '
    '<a href="/tools/">Compliance Tools</a> · '
    '<a href="https://corridoreconomics.substack.com">Corridor Economics Newsletter</a></p>'
)
NEW_FOOTER_LINKS = (
    '<p style="margin-top:8px">'
    '<a href="https://corridoreconomics.substack.com">Corridor Economics Newsletter</a></p>'
)

def transform(path):
    txt = open(path, encoding='utf-8').read()
    orig = txt
    # header
    if HEADER_HS in txt:
        txt = txt.replace(HEADER_HS, NEW_HEADER)
    elif HEADER_SIMPLE in txt:
        txt = txt.replace(HEADER_SIMPLE, NEW_HEADER)
    elif 'p0-header' not in txt:
        # not an old header and not already migrated -> unrecognised
        return 'NO_HEADER'
    # css (inject once before the FIRST closing style tag)
    if '/* ===== P0 redesign' not in txt:
        txt = txt.replace('</style>', P0_CSS + '</style>', 1)
    # cta
    txt = txt.replace(OLD_CTA, NEW_CTA)
    # dead footer links
    txt = txt.replace(OLD_FOOTER_LINKS, NEW_FOOTER_LINKS)
    # search js before </body>
    if 'id="p0q"' in txt and 'getElementById(\'p0q\')' not in txt:
        txt = txt.replace('</body>', P0_JS + '</body>', 1)
    if txt == orig:
        return 'UNCHANGED'
    open(path, 'w', encoding='utf-8').write(txt)
    return 'OK'

def main():
    counts = {}
    total = 0
    for root, dirs, files in os.walk(ROOT):
        if os.sep + '.git' in root:
            continue
        for fn in files:
            if fn != 'index.html':
                continue
            p = os.path.join(root, fn)
            r = transform(p)
            counts[r] = counts.get(r, 0) + 1
            total += 1
    print('files processed:', total)
    for k in sorted(counts):
        print('  ', k, counts[k])
    if counts.get('NO_HEADER'):
        print('WARNING: pages with no recognised header ->', counts['NO_HEADER'])

if __name__ == '__main__':
    main()
