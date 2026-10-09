"""Builds the website: src/pages/*.html (a few header lines, then the page body) inside one layout.

    python tools/build.py

Writes, all next to index.html (commit them: Hostinger serves the repository as it is):
- <name>.html for every page in src/pages,
- assets/css/site.min.css (assets/fonts/fonts.css + assets/css/site.css, minified) and assets/js/site.min.js,
- sitemap.xml (with the date each page last changed), robots.txt and site.webmanifest (the site icons: tools/images.py).

Every /assets/ address in the pages and the CSS gets ?v=<hash of the file>, so browsers and Cloudflare may keep
assets for a year (.htaccess) and still see a changed file at once. Images: see tools/images.py.

Page header lines: title (<= 60 characters), description (<= 155), optional crumb (the short name in the
breadcrumb trail) and robots (noindex for pages that should stay out of search).
"""
import datetime
import hashlib
import html
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://esysmax.com'
NOT_LISTED = ('404', 'thank-you')  # not in the sitemap (and noindex)
# The Terms version a card buyer accepts: {terms} in a page becomes it (the buy form's data-terms, which
# site.js sends with the checkout). Keep it the same as "Version ..." at the top of src/pages/terms.html.
TERMS_VERSION = '2026-10-03'

# Six links: Download is the header's own button, so it is not repeated here.
NAV = [('Features', '/#features'), ('How it works', '/#how'), ('Pricing', '/#pricing'), ('FAQ', '/#faq'), ('Guides', '/guides'), ('Licence', '/licence')]

# IndexNow (Bing, Yandex, Seznam, Naver...): the key file at the site root proves the site is ours; tools/indexnow.py
# tells them which pages changed after a deploy. Not a secret: it is public by design.
INDEXNOW_KEY = '826669878385841d9bc3533d0dc24155'

ICONS = {
    'check': '<path d="M20 6 9 17l-5-5"/>',
    'x': '<path d="M18 6 6 18M6 6l12 12"/>',
    'spark': '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>',
    'list': '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    'car': '<path d="M5 17h14M6 17l-1-5 2-5h10l2 5-1 5"/><circle cx="7.5" cy="17" r="1.5"/><circle cx="16.5" cy="17" r="1.5"/><path d="M5 12h14"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    'history': '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    'shield': '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    'save': '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h8V3M8 21v-7h8v7"/>',
    'alert': '<path d="M12 3 2 20h20z"/><path d="M12 9v5M12 17h.01"/>',
    'chip': '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    'file': '<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4M9 13h6M9 17h6"/>',
    'bolt': '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    'battery': '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2M6 10v4M10 10v4"/>',
    'moon': '<path d="M20 14.5A8 8 0 1 1 9.5 4 6.5 6.5 0 0 0 20 14.5z"/>',
    'refresh': '<path d="M21 12a9 9 0 0 1-15.5 6.3L3 16M3 12a9 9 0 0 1 15.5-6.3L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
    'download': '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
    'send': '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/>',
    'card': '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/>',
    'windows': '<path d="M3 5.5 10 4.5v7H3zM11 4.3 21 3v8.5H11zM3 12.5h7v7L3 18.5zM11 12.5h10V21l-10-1.3z"/>',
    'plug': '<path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0zM12 18v4"/>',
    'pc': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    'flag': '<path d="M4 21V4M4 4h13l-2 4 2 4H4"/>',
    'lock': '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    'dollar': '<path d="M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    'chat': '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    'key': '<circle cx="8" cy="15" r="4"/><path d="m10.8 12.2 8.7-8.7M17 6l3 3M15 8l2 2"/>',
}


# The US flag, drawn (Windows shows the flag emoji as the letters "US").
USFLAG = '''<svg class="usflag" viewBox="0 0 38 20" role="img" aria-label="United States flag"><rect width="38" height="20" fill="#b22234"/><path d="M0 2.3h38M0 5.4h38M0 8.5h38M0 11.5h38M0 14.6h38M0 17.7h38" stroke="#fff" stroke-width="1.54"/><rect width="15.2" height="10.8" fill="#3c3b6e"/><g fill="#fff"><circle cx="2.5" cy="2" r=".6"/><circle cx="5.5" cy="2" r=".6"/><circle cx="8.5" cy="2" r=".6"/><circle cx="11.5" cy="2" r=".6"/><circle cx="4" cy="4.2" r=".6"/><circle cx="7" cy="4.2" r=".6"/><circle cx="10" cy="4.2" r=".6"/><circle cx="13" cy="4.2" r=".6"/><circle cx="2.5" cy="6.4" r=".6"/><circle cx="5.5" cy="6.4" r=".6"/><circle cx="8.5" cy="6.4" r=".6"/><circle cx="11.5" cy="6.4" r=".6"/><circle cx="4" cy="8.6" r=".6"/><circle cx="7" cy="8.6" r=".6"/><circle cx="10" cy="8.6" r=".6"/><circle cx="13" cy="8.6" r=".6"/></g></svg>'''


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + '</svg>')


# The logo in the header (40 px high) and the footer (30 px high); tools/images.py makes the files.
def logo(css_width, height, extra=''):
    return ('<picture><source type="image/webp" srcset="/assets/img/logo-dark.webp 129w, /assets/img/logo-dark@2x.webp 258w, '
            '/assets/img/logo-dark@3x.webp 388w" sizes="{0}px"><img src="/assets/img/logo-dark@2x.png" width="{0}" height="{1}" '
            'alt="E-Sys MAX"{2}></picture>').format(css_width, height, extra)


LAYOUT = '''<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
{seo}<link rel="preload" href="/assets/fonts/Inter-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/JetBrainsMono-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.min.css">
<meta name="theme-color" content="#0a0c10">
<meta property="og:type" content="website">
<meta property="og:site_name" content="E-Sys MAX">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
{og_url}<meta property="og:image" content="{site}/assets/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="E-Sys MAX: BMW coding with E-Sys, in plain English">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{site}/assets/img/og.png">
<meta name="twitter:image:alt" content="E-Sys MAX: BMW coding with E-Sys, in plain English">
<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="icon" type="image/png" sizes="48x48" href="/assets/img/favicon-48.png">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/img/favicon-96.png">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/img/favicon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
{jsonld}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/" aria-label="E-Sys MAX home">{logo_head}</a>
    <nav class="nav" id="site-nav" aria-label="Main">{nav}</nav>
    <div class="head-cta">
      <a class="btn btn-ghost btn-sm" href="/download">Free trial</a>
      <a class="btn btn-primary btn-sm" href="/buy">Buy</a>
    </div>
    <button class="menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span></button>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        {logo_foot}
        <p>BMW coding with E-Sys, in plain English. Setting names, ready-made changes, backups and history: every change stays yours to approve.</p>
        <p class="made-usa">''' + USFLAG + '''<span>Made in the USA by KDR Coding, Los Angeles, California. Prices in US dollars.</span></p>
      </div>
      <nav aria-label="Product"><p class="foot-h">Product</p><a href="/#features">Features</a><a href="/#how">How it works</a><a href="/#trust">Safety &amp; privacy</a><a href="/#pricing">Pricing</a><a href="/#faq">FAQ</a><a href="/download">Download</a><a href="/guides">E-Sys coding guides</a><a href="/guide">Quick Start Guide</a><a href="/assets/E-Sys-MAX-Quick-Start-Guide.pdf">Guide (PDF)</a></nav>
      <nav aria-label="Licence"><p class="foot-h">Licence</p><a href="/buy">Buy a licence</a><a href="/licence">Activate &amp; find my licence</a><a href="/licence#move">New PC</a><a href="https://t.me/EsysMaxbot">@EsysMaxbot on Telegram</a></nav>
      <nav aria-label="Legal"><p class="foot-h">Legal</p><a href="/terms">Terms &amp; licence</a><a href="/security">Privacy &amp; security</a><a href="/privacy">Privacy Policy</a><a href="/refunds">Refunds</a><a href="/disclaimer">Coding disclaimer</a><a href="/contact">Contact</a></nav>
    </div>
    <div class="foot-legal">
      <span>&copy; <span data-year>2026</span> KDR Coding, Los Angeles, California. All rights reserved.</span>
      <span>Vehicle coding is at your own risk. Not affiliated with BMW AG. BMW and E-Sys are trademarks of BMW AG. E-Sys and PSdZData are not included.</span>
    </div>
  </div>
</footer>
<script src="/assets/js/site.min.js" defer></script>
</body>
</html>
'''


# ---------------------------------------------------------------- assets: hashes, minified CSS and JS

_hashes = {}


def file_hash(address):
    """The first 10 hex digits of the SHA-256 of the file behind an /assets/... address."""
    if address not in _hashes:
        with open(os.path.join(ROOT, address.lstrip('/').replace('/', os.sep)), 'rb') as f:
            _hashes[address] = hashlib.sha256(f.read()).hexdigest()[:10]
    return _hashes[address]


def versioned(text):
    """Adds ?v=<hash> to every /assets/ file address (not the PDF guide, which keeps one plain address)."""
    return re.sub(r'/assets/[\w./@-]+?\.(?:css|js|woff2|png|jpe?g|webp|svg|ico)(?![\w?])',
                  lambda m: m.group(0) + '?v=' + file_hash(m.group(0)), text)


def minify_css(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = []
    for part in re.split(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')', css):
        if part[:1] in ('"', "'"):
            out.append(part)
            continue
        part = re.sub(r'\s+', ' ', part)
        part = re.sub(r'\s*([{};,>])\s*', r'\1', part)
        part = re.sub(r':\s+', ':', part)
        out.append(part.replace(';}', '}'))
    return ''.join(out).strip() + '\n'


def minify_js(js):
    """Drops indentation, blank lines and whole-line comments; keeps line breaks, so nothing can change meaning."""
    lines = (line.strip() for line in js.splitlines())
    return '\n'.join(line for line in lines if line and not line.startswith('//')) + '\n'


def write(path, text):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def read(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as f:
        return f.read()


def build_assets():
    css = minify_css(read('assets/fonts/fonts.css') + '\n' + read('assets/css/site.css'))
    write('assets/css/site.min.css', '/* E-Sys MAX website. Built by tools/build.py from assets/fonts/fonts.css and assets/css/site.css. */\n' + versioned(css))
    write('assets/js/site.min.js', '// E-Sys MAX website. Built by tools/build.py from assets/js/site.js.\n' + minify_js(read('assets/js/site.js')))


# ---------------------------------------------------------------- structured data (JSON-LD)

def text_of(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', fragment))).strip()


# The logo: the square site icon (emblem on the dark background) that tools/images.py makes; it reads well on
# Google's white background, which the light grey emblem alone does not.
ORG = {
    '@type': 'Organization', '@id': SITE + '/#organization', 'name': 'KDR Coding', 'url': SITE + '/',
    'logo': {'@type': 'ImageObject', 'url': SITE + '/assets/img/icon-512.png', 'width': 512, 'height': 512},
    'image': SITE + '/assets/img/icon-512.png',
    'address': {'@type': 'PostalAddress', 'addressLocality': 'Los Angeles', 'addressRegion': 'CA', 'addressCountry': 'US'},
    'contactPoint': {'@type': 'ContactPoint', 'contactType': 'customer support', 'url': SITE + '/contact', 'availableLanguage': 'English'},
    'sameAs': ['https://t.me/EsysMaxbot'],
}
# name and alternateName: the site name Google shows above the result (see "site names" in Google's documentation).
WEBSITE = {'@type': 'WebSite', '@id': SITE + '/#website', 'name': 'E-Sys MAX', 'alternateName': ['EsysMax', 'ESys MAX'],
           'url': SITE + '/', 'inLanguage': 'en-US', 'publisher': {'@id': SITE + '/#organization'}}
SOFTWARE = {
    '@type': 'SoftwareApplication', '@id': SITE + '/#software', 'name': 'E-Sys MAX', 'url': SITE + '/',
    'description': 'A Windows add-on and launcher for BMW E-Sys: English names for coding settings, ready-made coding changes, '
                   'a vehicle order helper, fault scan, full backups and coding history. E-Sys itself is not included.',
    'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'Windows 10, Windows 11',
    'softwareRequirements': 'BMW E-Sys with PSdZData and an ENET cable or a BMW ICOM (not included)',
    'downloadUrl': SITE + '/download', 'screenshot': SITE + '/assets/img/vehicle-order.jpg',
    'image': SITE + '/assets/img/icon-512.png',
    'publisher': {'@id': SITE + '/#organization'},
    'offers': [
        {'@type': 'Offer', 'name': name, 'description': text, 'price': price, 'priceCurrency': 'USD',
         'availability': 'https://schema.org/InStock', 'url': SITE + '/buy?plan=' + plan, 'seller': {'@id': SITE + '/#organization'}}
        for name, plan, price, text in (
            ('1 month', 'month', '39.00', 'Every feature for 30 days on one PC. One-time payment, no automatic renewal.'),
            ('1 year', 'year', '59.00', 'Every feature for 365 days on one PC. One-time payment, no automatic renewal.'),
            ('Lifetime', 'lifetime', '99.00', 'Every feature and every future update, one PC; can be moved to a new PC one time. One-time payment.'))
    ],
}


def structured_data(name, meta, body):
    if meta.get('robots', '').startswith('noindex'):
        return ''
    url = SITE + ('/' if name == 'index' else '/' + name)
    graph = []
    if name == 'index':
        graph += [ORG, WEBSITE, SOFTWARE]
    else:
        # Home > (Guides >) this page.
        trail = [('E-Sys MAX', SITE + '/')]
        if meta.get('parent') == 'guides':
            trail.append(('Guides', SITE + '/guides'))
        trail.append((meta.get('crumb') or meta['title'], url))
        graph.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': label, 'item': link} for i, (label, link) in enumerate(trail)]})
    if meta.get('type') == 'article':
        changed = last_changed('src/pages/{0}.html'.format(name))
        graph.append({'@type': 'TechArticle', '@id': url + '#article', 'headline': meta.get('headline') or meta['title'],
                      'description': meta['description'], 'url': url, 'mainEntityOfPage': url, 'inLanguage': 'en-US',
                      'datePublished': meta.get('published') or changed, 'dateModified': changed,
                      'image': SITE + '/assets/img/' + (meta.get('image') or 'vehicle-order.jpg'),
                      'author': {'@id': SITE + '/#organization'}, 'publisher': {'@id': SITE + '/#organization'},
                      'about': [{'@type': 'Thing', 'name': 'BMW E-Sys'}, {'@type': 'Thing', 'name': 'BMW coding'}]})
        if not any(item.get('@id') == ORG['@id'] for item in graph):
            graph.append(ORG)
    # Every question in a FAQ, with or without an id (linked answers: <details id="upgrade">).
    faq = re.findall(r'<details(?: id="[\w-]+")?><summary>(.*?)</summary><div class="answer">(.*?)</div></details>', body, re.S)
    if faq:
        graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': [
            {'@type': 'Question', 'name': text_of(q), 'acceptedAnswer': {'@type': 'Answer', 'text': text_of(a)}} for q, a in faq]})
    data = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':'))
    return '<script type="application/ld+json">' + data.replace('</', '<\\/') + '</script>\n'


# ---------------------------------------------------------------- pages

def label_tables(body):
    """Copies each column title of a table.data into data-label on its cells, for the stacked phone layout."""
    def table(m):
        rows = re.findall(r'<tr>.*?</tr>', m.group(0), re.S)
        heads = [text_of(h) for h in re.findall(r'<th>(.*?)</th>', rows[0], re.S)] if rows else []
        if not heads:
            return m.group(0)

        def row(r):
            cells = iter(heads)
            return re.sub(r'<td>', lambda _: '<td data-label="{0}">'.format(html.escape(next(cells, ''), quote=True)), r.group(0))
        return re.sub(r'<tr>(?:(?!<th>).)*?</tr>', row, m.group(0), flags=re.S)
    return re.sub(r'<table class="data">.*?</table>', table, body, flags=re.S)


def render(name, text):
    head, _, body = text.partition('\n---\n')
    meta = {k.strip(): v.strip() for k, v in (line.split(':', 1) for line in head.strip().splitlines())}
    for key, limit in (('title', 60), ('description', 155)):
        if len(meta[key]) > limit:
            print('  warning: {0}: {1} is {2} characters (keep it to {3})'.format(name, key, len(meta[key]), limit))
    path = '/' if name == 'index' else '/' + name
    url = SITE + path
    noindex = meta.get('robots', '').startswith('noindex')
    nav = ''.join('<a href="{0}"{1}>{2}</a>'.format(href, ' aria-current="page"' if href == path else '', label) for label, href in NAV)
    body = re.sub(r'\{icon:(\w+)\}', lambda m: icon(m.group(1)), body.strip('\n')).replace('{terms}', TERMS_VERSION).replace('{usflag}', USFLAG)
    body = label_tables(body)
    if noindex:
        seo = '<meta name="robots" content="{0}">\n'.format(meta['robots'])
        og_url = ''
    else:
        seo = '<link rel="canonical" href="{0}">\n<meta name="robots" content="index, follow, max-image-preview:large">\n'.format(url)
        og_url = '<meta property="og:url" content="{0}">\n'.format(url)
    page = LAYOUT.format(
        title=html.escape(meta['title']), description=html.escape(meta['description']), site=SITE, seo=seo, og_url=og_url,
        nav=nav, body=body, jsonld=structured_data(name, meta, body),
        logo_head=logo(129, 40), logo_foot=logo(97, 30, ' class="foot-logo" loading="lazy"'))
    return versioned(page)


# /site.webmanifest (linked from every page): the name and icons for "Install" / "Add to home screen".
MANIFEST = {
    'name': 'E-Sys MAX', 'short_name': 'E-Sys MAX',
    'description': 'BMW coding with E-Sys, in plain English.',
    'start_url': '/', 'scope': '/', 'display': 'standalone',
    'background_color': '#0a0c10', 'theme_color': '#0a0c10',
    'icons': [{'src': '/assets/img/favicon-192.png', 'sizes': '192x192', 'type': 'image/png'},
              {'src': '/assets/img/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}],
}


def last_changed(path):
    """The day the page source was last committed, or today when it has changes not committed yet."""
    try:
        run = lambda *args: subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if not run('status', '--porcelain', '--', path):
            day = run('log', '-1', '--format=%cs', '--', path)
            if day:
                return day
    except OSError:
        pass
    return datetime.date.today().isoformat()


def main():
    build_assets()
    pages = os.path.join(ROOT, 'src', 'pages')
    if 'Version ' + TERMS_VERSION not in read(os.path.join('src', 'pages', 'terms.html')):
        print('  warning: TERMS_VERSION ({0}) is not the version at the top of src/pages/terms.html'.format(TERMS_VERSION))
    built = []
    for file in sorted(os.listdir(pages)):
        if file.endswith('.html'):
            write(file, render(file[:-5], read(os.path.join('src', 'pages', file))))
            built.append(file[:-5])
    listed = sorted((p for p in built if p not in NOT_LISTED), key=lambda p: (p != 'index', p))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in listed:
        lines.append('  <url><loc>{0}{1}</loc><lastmod>{2}</lastmod></url>'.format(
            SITE, '/' if p == 'index' else '/' + p, last_changed('src/pages/{0}.html'.format(p))))
    write('sitemap.xml', '\n'.join(lines + ['</urlset>', '']))
    write('robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: {0}/sitemap.xml\n'.format(SITE))
    write(INDEXNOW_KEY + '.txt', INDEXNOW_KEY)
    write('site.webmanifest', versioned(json.dumps(MANIFEST, indent=2)) + '\n')
    print('built', ', '.join(built), '+ site.min.css, site.min.js, sitemap.xml, robots.txt, site.webmanifest')


if __name__ == '__main__':
    main()
