#!/usr/bin/env python3
"""Zet de WordPress-export van jaapgerritsma.nl om naar een statische site.

Gebruik: python3 build.py src/export.xml site/
De beelden (wp-content/uploads) worden apart in site/wp-content/uploads gezet.
Alle oude adressen blijven werken (zelfde paden als in WordPress).
"""
import html, json, re, shutil, sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
HERE = Path(__file__).parent
NS = {'wp': 'http://wordpress.org/export/1.2/',
      'content': 'http://purl.org/rss/1.0/modules/content/'}
BASE = 'https://jaapgerritsma.nl'
MAANDEN = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
           'augustus', 'september', 'oktober', 'november', 'december']

SKIP_POSTS = {'welkom-bij-het-blog'}          # standaard WordPress-welkomstbericht
SKIP_PAGES = {'privacybeleid-2', 'blog'}      # geen tracking meer; blog wordt gegenereerd

NAV = [('/', 'Over Jaap'), ('/boeken/', 'Boeken'), ('/blog/', 'Blog'),
       ('/columns/', 'Columns'), ('/in-de-media/', 'In de media'),
       ('/wetenschap/', 'Wetenschap')]

# Boeken in volgorde van verschijnen (jaartallen uit de pagina "Over Jaap")
BOEKEN = [
    ('het-vliegende-laatje', 'Het vliegende laatje', '2001', 'Sprookjes'),
    ('bittere-maretak', 'Bittere maretak', '2009', 'Roman'),
    ('opa-vertelt', 'Opa vertelt', '2015', 'Fantastische verhalen'),
    ('ontstemde-liefde', 'Ontstemde liefde', '2015', 'Roman'),
    ('klabbertoet', 'Klabbertoet', '2020', 'Roman'),
    ('ongedachte-belevenissen', 'Ongedachte belevenissen', '2022', 'Roman'),
    ('sluitsteen', 'Sluitsteen', '2023', 'Korte verhalen'),
    ('fabeltjesboot', 'De Fabeltjesboot', '2024', 'Fabels'),
]


def nl_datum(s):
    y, m, d = s[:10].split('-')
    return f'{int(d)} {MAANDEN[int(m) - 1]} {y}'


def path_of(link):
    p = link.replace(BASE, '') or '/'
    return p if p.endswith('/') else p + '/'


used_files = set()


def yt(m):
    url = m.group(1)
    vid = re.search(r'(?:youtu\.be/|v=)([\w-]{11})', url).group(1)
    return (f'<figure class="video"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
            f'title="Video" loading="lazy" allow="encrypted-media; picture-in-picture" '
            f'allowfullscreen></iframe></figure>')


def clean(body):
    body = re.sub(r'<figure class="wp-block-embed[^"]*"><div class="wp-block-embed__wrapper">\s*(\S+)\s*</div></figure>', yt, body)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'\s(?:style|width|height|data-type|data-id|srcset|sizes)="[^"]*"', '', body)

    def keep_class(m):
        keep = [c for c in m.group(1).split() if re.match(r'^(align(left|right|center)|wp-block-gallery|video)$', c)]
        return f' class="{" ".join(keep)}"' if keep else ''
    body = re.sub(r'\sclass="([^"]*)"', keep_class, body)
    # interne links en beelden relatief maken
    body = re.sub(r'https?://(?:www\.)?jaapgerritsma\.nl', '', body)
    body = re.sub(r'(/wp-content/uploads/[^"]+)\.heic', r'\1.jpg', body)  # browsers tonen geen HEIC
    body = body.replace('href="/over-jaap/"', 'href="/"').replace('/sprookjes/het-vliegende-laatje/', '/het-vliegende-laatje/')  # oude adressen
    for f in re.findall(r'/wp-content/uploads/[^"\'\s)<>]+', body):
        used_files.add(f)
    body = re.sub(r'<img ', '<img loading="lazy" ', body)
    body = re.sub(r'<p>\s*(&nbsp;)?\s*</p>', '', body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    # losse regels zonder <p> (oudere berichten) netjes in alinea's
    if '<p' not in body:
        body = ''.join(f'<p>{x.strip()}</p>\n' for x in re.split(r'\n\s*\n', body) if x.strip())
    return body.strip()


def excerpt(body, n=32):
    t = html.unescape(re.sub(r'<[^>]+>', ' ', body))
    words = t.split()
    return ' '.join(words[:n]) + (' …' if len(words) > n else '')


def first_img(body):
    m = re.search(r'<img[^>]+src="([^"]+)"', body)
    return m.group(1) if m else None


def layout(title, content, path, desc='', bodyclass=''):
    navhtml = ''.join(
        f'<a href="{h}"{" aria-current=\"page\"" if (h == path or (h != "/" and path.startswith(h))) else ""}>{t}</a>'
        for h, t in NAV)
    full_title = 'Jaap Gerritsma' if path == '/' else f'{title} · Jaap Gerritsma'
    desc = html.escape(desc or 'Jaap Gerritsma (1942–2025), medisch wetenschapper en schrijver.')
    return f'''<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="preload" href="/assets/fonts/newsreader-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body class="{bodyclass}">
<a class="skip" href="#inhoud">Naar de inhoud</a>
<header class="kop">
  <a class="merk" href="/">Jaap Gerritsma</a>
  <nav aria-label="Hoofdmenu">{navhtml}</nav>
</header>
<main id="inhoud">
{content}
</main>
<footer class="voet">
  <p class="voet-naam">Jaap Gerritsma <span>1942 – 2025</span></p>
  <p>Deze site wordt in zijn herinnering bewaard door zijn familie.</p>
</footer>
</body>
</html>
'''


def write(path, doc):
    target = OUT / path.lstrip('/') / 'index.html' if path.endswith('/') else OUT / path.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding='utf-8')


# ---------- inlezen ----------
ch = ET.parse(SRC).getroot().find('channel')
pages, posts = {}, []
for it in ch.findall('item'):
    pt = it.findtext('wp:post_type', namespaces=NS)
    if it.findtext('wp:status', namespaces=NS) != 'publish' or pt not in ('page', 'post'):
        continue
    slug = it.findtext('wp:post_name', namespaces=NS)
    rec = dict(
        title=html.unescape(it.findtext('title') or '').strip(),
        slug=slug, path=path_of(it.findtext('link')),
        date=it.findtext('wp:post_date', namespaces=NS),
        body=clean(it.findtext('content:encoded', namespaces=NS) or ''),
        comments=[dict(author=c.findtext('wp:comment_author', namespaces=NS),
                       date=c.findtext('wp:comment_date', namespaces=NS),
                       text=c.findtext('wp:comment_content', namespaces=NS))
                  for c in it.findall('wp:comment', namespaces=NS)
                  if c.findtext('wp:comment_approved', namespaces=NS) == '1'
                  and c.findtext('wp:comment_type', namespaces=NS) not in ('pingback', 'trackback')])
    if pt == 'page':
        if slug not in SKIP_PAGES:
            pages[slug] = rec
    elif slug not in SKIP_POSTS:
        posts.append(rec)
posts.sort(key=lambda p: p['date'], reverse=True)


def comments_html(cs):
    if not cs:
        return ''
    items = ''.join(
        f'<li><p class="reactie-kop"><strong>{html.escape(c["author"])}</strong> · {nl_datum(c["date"])}</p>'
        f'{"".join(f"<p>{html.escape(html.unescape(x))}</p>" for x in c["text"].split(chr(10)) if x.strip())}</li>'
        for c in cs)
    return f'<section class="reacties"><h2>Reacties van lezers</h2><ol>{items}</ol></section>'


# ---------- boeken-kaartjes ----------
OMSLAG = {'sluitsteen': '/assets/omslag-sluitsteen.jpg', 'klabbertoet': None}


def boek_kaart(slug, titel, jaar, soort):
    p = pages.get(slug)
    img = OMSLAG[slug] if slug in OMSLAG else (first_img(p['body']) if p else None)
    href = p['path'] if p else f'/{slug}/'
    cover = f'<img src="{img}" alt="Omslag {html.escape(titel)}" loading="lazy">' if img else f'<span class="omslag-leeg"><span>{titel}</span><span class="omslag-auteur">Jaap Gerritsma</span></span>'
    return (f'<a class="boek" href="{href}"><span class="omslag">{cover}</span>'
            f'<span class="label">{jaar} · {soort}</span><span class="boek-titel">{titel}</span></a>')


boeken_grid = '<div class="boeken">' + ''.join(boek_kaart(*b) for b in BOEKEN) + '</div>'


def post_lijst(ps, kort=False):
    out = ['<ul class="lijst">']
    for p in ps:
        ex = '' if kort else f'<p class="ex">{html.escape(excerpt(p["body"]))}</p>'
        out.append(f'<li><a href="{p["path"]}"><span class="label">{nl_datum(p["date"])}</span>'
                   f'<span class="lijst-titel">{html.escape(p["title"])}</span>{ex}</a></li>')
    out.append('</ul>')
    return ''.join(out)


# ---------- home ----------
over = pages.pop('over-jaap', None) or next(p for p in pages.values() if p['path'] == '/')
pages = {k: v for k, v in pages.items() if v['path'] != '/'}
portret = first_img(over['body'])
over_body = re.sub(r'<figure[^>]*>(?:(?!</figure>).)*' + re.escape(portret) + r'.*?</figure>', '', over['body'], count=1, flags=re.S) if portret else over['body']
home = f'''
<section class="held">
  <div class="held-tekst">
    <p class="label">Medisch wetenschapper en schrijver</p>
    <h1>Jaap Gerritsma</h1>
    <p class="jaren">1942 – 2025</p>
  </div>
  {f'<img class="portret" src="{portret}" alt="Jaap Gerritsma">' if portret else ''}
</section>
<article class="tekst">{over_body}</article>
<section class="blok">
  <h2 class="sectie"><span class="label">Boeken</span></h2>
  {boeken_grid}
</section>
<section class="blok smal">
  <h2 class="sectie"><span class="label">Laatst geschreven</span></h2>
  {post_lijst(posts[:5])}
  <p class="meer"><a href="/blog/">Alle {len(posts)} verhalen en columns</a></p>
</section>'''
write('/', layout('Over Jaap', home, '/', bodyclass='home'))

# ---------- boeken ----------
write('/boeken/', layout('Boeken', f'''
<header class="titel"><p class="label">Romans, sprookjes en verhalen</p><h1>Boeken</h1></header>
{boeken_grid}
<p class="meer tekst"><a href="/sprookjes/">Over de sprookjes</a></p>''', '/boeken/', 'De boeken van Jaap Gerritsma.'))

# ---------- blog ----------
per_jaar = {}
for p in posts:
    per_jaar.setdefault(p['date'][:4], []).append(p)
blog = '<header class="titel"><p class="label">Verhalen en columns</p><h1>Blog</h1></header>'
blog += '<p class="intro tekst">Jaap schreef zo nu en dan een verhaal op zijn blog. Hier staan ze allemaal, de nieuwste bovenaan.</p>'
for jaar, ps in per_jaar.items():
    blog += f'<section class="jaar"><h2 class="sectie"><span class="label">{jaar}</span></h2>{post_lijst(ps)}</section>'
write('/blog/', layout('Blog', blog, '/blog/', 'Verhalen en columns van Jaap Gerritsma.'))

# ---------- berichten ----------
for i, p in enumerate(posts):
    nieuwer = posts[i - 1] if i > 0 else None
    ouder = posts[i + 1] if i + 1 < len(posts) else None
    nav = '<nav class="buren" aria-label="Meer verhalen">'
    nav += f'<a class="ouder" href="{ouder["path"]}"><span class="label">Vorige</span>{html.escape(ouder["title"])}</a>' if ouder else '<span></span>'
    nav += f'<a class="nieuwer" href="{nieuwer["path"]}"><span class="label">Volgende</span>{html.escape(nieuwer["title"])}</a>' if nieuwer else '<span></span>'
    nav += '</nav>'
    doc = f'''<article class="tekst">
<header class="titel"><p class="label"><a href="/blog/">Blog</a> · {nl_datum(p["date"])}</p><h1>{html.escape(p["title"])}</h1></header>
{p["body"]}
</article>
{comments_html(p["comments"])}
{nav}'''
    write(p['path'], layout(p['title'], doc, p['path'], excerpt(p['body'], 25)))

# ---------- pagina's ----------
for slug, p in pages.items():
    doc = f'''<article class="tekst">
<header class="titel"><h1>{html.escape(p["title"])}</h1></header>
{p["body"]}
</article>
{comments_html(p["comments"])}'''
    write(p['path'], layout(p['title'], doc, p['path'], excerpt(p['body'], 25)))

# ---------- 404, sitemap, overige ----------
(OUT / '404.html').write_text(layout('Niet gevonden', '''<article class="tekst">
<header class="titel"><h1>Deze pagina bestaat niet meer</h1></header>
<p>Misschien is het adres veranderd. Begin bij <a href="/">Over Jaap</a> of kijk in het <a href="/blog/">overzicht van alle verhalen</a>.</p>
</article>''', '/404/'), encoding='utf-8')
urls = ['/', '/boeken/', '/blog/'] + [p['path'] for p in pages.values()] + [p['path'] for p in posts]
(OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                 + ''.join(f'<url><loc>{BASE}{u}</loc></url>\n' for u in urls) + '</urlset>\n', encoding='utf-8')
(OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
(OUT / 'CNAME').write_text('jaapgerritsma.nl\n')
(OUT / '.nojekyll').write_text('')
shutil.copytree(HERE / 'assets', OUT / 'assets', dirs_exist_ok=True)
UPL = HERE / 'zip_in'
if UPL.exists():
    for f in used_files:
        src = UPL / f.replace('/wp-content/uploads/', '')
        dst = OUT / f.lstrip('/')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
(OUT.parent / 'used_uploads.json').write_text(json.dumps(sorted(used_files), indent=1))
print(f'{len(pages)} pagina\'s, {len(posts)} berichten, {len(used_files)} beeldverwijzingen')

# ---------- relatieve paden: werkt zowel op jaapgerritsma.nl als op een tijdelijk adres ----------
import os
for f in OUT.rglob('*.html'):
    if f.name == '404.html':
        continue
    rel = os.path.relpath(OUT, f.parent).replace(os.sep, '/')
    pre = '' if rel == '.' else rel + '/'
    s = f.read_text(encoding='utf-8')
    def fix(m):
        attr, path = m.group(1), m.group(2)
        if path.startswith('//'):
            return m.group(0)
        target = path.lstrip('/')
        if target == '' or target.endswith('/'):
            target += 'index.html'
        return f'{attr}="{pre}{target}"'
    s = re.sub(r'(href|src)="(/[^"]*)"', fix, s)
    f.write_text(s, encoding='utf-8')
