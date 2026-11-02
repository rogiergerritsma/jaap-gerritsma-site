# Wordt door build.py uitgevoerd (exec) met dezelfde variabelen: OUT, HERE, layout, write, html, re, shutil.
# E-book "Problem Based Learning in Leprosy and Tuberculosis" (2001), overgenomen van de Google Site.
from urllib.parse import unquote

PBL_SRC = HERE / 'pbl_src'
PBL_ORDER = ['acknowledgements', 'preface', 'pbl-learning', 'pbl-in-practice', 'pbl-in-practice/olumide',
             'how-to-help-students-to-improve-their-learning', 'tutorial-groups', 'problem-solving',
             'the-implementation-of-pbl-problems-and-strategies', 'assessment-and-evaluation', 'assessment',
             'evaluation', 'model-answers-1', 'model-answers-2', 'selected-references']
PBL_TITEL = 'Problem Based Learning in Leprosy and Tuberculosis'
pbl_paths = []


def pbl_clean(h):
    h = re.sub(r'href="/gerritsma\.net/problem-based-learning/([^"?]*)(\?[^"]*)?"',
               lambda m: f'href="/pbl/{m.group(1)}/"', h)

    def unwrap(m):
        q = re.search(r'[?&]q=([^&]+)', html.unescape(m.group(1)))
        url = unquote(q.group(1)) if q else ''
        if not url or 'sites.google.com' in url:
            return 'data-weg="1"'
        return f'href="{url}"'
    h = re.sub(r'href="(https?://www\.google\.com/url\?[^"]*)"', unwrap, h)
    h = re.sub(r'<a data-weg="1">(.*?)</a>', r'\1', h, flags=re.S)
    h = re.sub(r'<u>(.*?)</u>', r'\1', h, flags=re.S)
    h = re.sub(r'<p>\s*</p>', '', h)
    h = re.sub(r'(<img src="([^"]+)"[^>]*>)', r'<a href="\2">\1</a>', h)  # 'click on the figure to enlarge'
    return h.strip()


def kale_tekst(k):
    return re.sub(r'<[^>]+>', '', k).strip()


hoofdstukken = []
if PBL_SRC.exists():
    for slug in PBL_ORDER:
        raw = (PBL_SRC / 'raw' / (slug.replace('/', '__') + '.html')).read_text(encoding='utf-8')
        h = pbl_clean(raw)
        koppen = re.findall(r'<h2>(.*?)</h2>', h, flags=re.S)
        if slug == 'assessment-and-evaluation':
            titel = 'Part Two: ' + kale_tekst(koppen[1])
            h = re.sub(r'<h2>.*?</h2>\s*<h2>.*?</h2>', '', h, count=1, flags=re.S)
        else:
            titel = kale_tekst(koppen[0])
            h = re.sub(r'<h2>.*?</h2>', '', h, count=1, flags=re.S)
        if titel.isupper():
            titel = titel.capitalize()
        hoofdstukken.append(dict(slug=slug, titel=titel, body=h, path=f'/pbl/{slug}/'))

    def toc(actief=None):
        items = []
        for c in hoofdstukken:
            sub = ' class="sub"' if '/' in c['slug'] else ''
            cur = ' aria-current="page"' if c['slug'] == actief else ''
            items.append(f'<li{sub}><a href="{c["path"]}"{cur}>{html.escape(c["titel"])}</a></li>')
        return '<ol class="toc">' + ''.join(items) + '</ol>'

    colofon = (
        '<div class="colofon">\n<p class="label">Colofon</p>\n'
        '<p>Written by Jaap Gerritsma, Eldryd Parry, Gani Alabi and Remi Verduin. '
        'Made for the <a href="https://www.leprastichting.nl/">Netherlands Leprosy Relief</a>. '
        '&copy;2001 Bureau Gerritsma.</p>\n'
        '<p>All parts of this publication may be downloaded or reproduced, with reference to the authors.</p>\n'
        '<p class="rol">De eerste webversie van dit e-book bouwde Rogier Gerritsma in 2001, als student.</p>\n'
        '</div>')
    cover = (
        '<article class="tekst boek-pbl">\n'
        '<header class="titel"><p class="label"><a href="/wetenschap/">Wetenschap</a> &middot; E-book &middot; 2001</p>'
        f'<h1>{PBL_TITEL}</h1>\n'
        '<p class="ondertitel">Jaap Gerritsma, Eldryd Parry, Gani Alabi en Remi Verduin</p></header>\n'
        '<p>Een handleiding voor probleemgestuurd onderwijs in de opleiding van gezondheidswerkers in lepra en '
        'tuberculose, geschreven voor de Netherlands Leprosy Relief. De tekst is in het Engels en staat hier zoals hij '
        'in 2001 werd gepubliceerd.</p>\n'
        '<h2 class="sectie"><span class="label">Inhoud</span></h2>\n'
        f'{toc()}\n{colofon}\n</article>')
    write('/pbl/', layout(PBL_TITEL, cover, '/pbl/',
                          'E-book van Jaap Gerritsma, Eldryd Parry, Gani Alabi en Remi Verduin (2001).'))
    pbl_paths.append('/pbl/')

    for i, c in enumerate(hoofdstukken):
        vorige = hoofdstukken[i - 1] if i > 0 else None
        volgende = hoofdstukken[i + 1] if i + 1 < len(hoofdstukken) else None
        nav = '<nav class="buren" aria-label="Hoofdstukken">'
        if vorige:
            nav += f'<a class="ouder" href="{vorige["path"]}"><span class="label">Vorige</span>{html.escape(vorige["titel"])}</a>'
        else:
            nav += '<a class="ouder" href="/pbl/"><span class="label">Vorige</span>Inhoud</a>'
        if volgende:
            nav += f'<a class="nieuwer" href="{volgende["path"]}"><span class="label">Volgende</span>{html.escape(volgende["titel"])}</a>'
        else:
            nav += '<span></span>'
        nav += '</nav>'
        doc = (
            '<article class="tekst boek-pbl" lang="en">\n'
            f'<header class="titel"><p class="label"><a href="/pbl/">{PBL_TITEL}</a></p>'
            f'<h1>{html.escape(c["titel"])}</h1></header>\n'
            f'{c["body"]}\n</article>\n{nav}\n'
            f'<details class="toc-blok"><summary class="label">Inhoud</summary>{toc(c["slug"])}</details>')
        write(c['path'], layout(c['titel'], doc, c['path'], f'{c["titel"]}: {PBL_TITEL} (2001).'))
        pbl_paths.append(c['path'])

    (OUT / 'pbl' / 'img').mkdir(parents=True, exist_ok=True)
    for f in (PBL_SRC / 'img').iterdir():
        shutil.copy2(f, OUT / 'pbl' / 'img' / f.name)
    # GitHub Pages is hoofdlettergevoelig: /PBL/ stuurt door naar /pbl/
    (OUT / 'PBL').mkdir(exist_ok=True)
    (OUT / 'PBL' / 'index.html').write_text(
        '<!doctype html><meta charset="utf-8"><title>Problem Based Learning</title>'
        '<link rel="canonical" href="https://jaapgerritsma.nl/pbl/">'
        '<meta http-equiv="refresh" content="0; url=../pbl/"><a href="../pbl/">Problem Based Learning</a>\n',
        encoding='utf-8')
