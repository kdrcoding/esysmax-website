"""Builds the site's pages: src/pages/*.html (a few header lines, then the page body) inside one layout.

    python tools/build.py

Writes <name>.html next to index.html. Commit the built pages: Hostinger serves the repository as it is.
"""
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://esysmax.com'

NAV = [('Features', '/#features'), ('How it works', '/#how'), ('Pricing', '/#pricing'), ('Download', '/download'), ('Licence', '/licence'), ('FAQ', '/#faq')]

ICONS = {
    'check': '<path d="M20 6 9 17l-5-5"/>',
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
}


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + '</svg>')


LAYOUT = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0b0c0f">
<meta property="og:type" content="website">
<meta property="og:site_name" content="E-Sys MAX">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/assets/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/assets/img/favicon-64.png">
<link rel="apple-touch-icon" href="/assets/img/emblem-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v={version}">
{extra_head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="/" aria-label="E-Sys MAX home"><img src="/assets/img/logo-dark.png" srcset="/assets/img/logo-dark.png 1x, /assets/img/logo-dark@2x.png 2x" width="224" height="40" alt="E-Sys MAX"></a>
    <nav class="nav" aria-label="Main">{nav}</nav>
    <div class="head-cta">
      <a class="btn btn-ghost btn-sm" href="/download">Free trial</a>
      <a class="btn btn-primary btn-sm" href="/buy">Buy</a>
    </div>
    <button class="menu-toggle" type="button" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <img src="/assets/img/logo-dark.png" width="170" height="30" alt="E-Sys MAX" style="height:30px;width:auto;margin-bottom:14px">
        <p>BMW coding with E-Sys, in plain English. Setting names, ready-made changes, backups and history: every change stays yours to approve.</p>
      </div>
      <div><h4>Product</h4><a href="/#features">Features</a><a href="/#pricing">Pricing</a><a href="/download">Download</a><a href="/#faq">FAQ</a></div>
      <div><h4>Licence</h4><a href="/buy">Buy a licence</a><a href="/licence">Activate &amp; find my licence</a><a href="/licence#move">New PC</a><a href="https://t.me/EsysMaxbot">@EsysMaxbot on Telegram</a></div>
      <div><h4>Legal</h4><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href="https://t.me/EsysMaxbot">Contact</a></div>
    </div>
    <div class="foot-legal">
      <span>&copy; <span data-year>2026</span> E-Sys MAX. All rights reserved.</span>
      <span>Not affiliated with BMW AG. BMW and E-Sys are trademarks of BMW AG. E-Sys and PSdZData are not included.</span>
    </div>
  </div>
</footer>
<script src="/assets/js/site.js?v={version}" defer></script>
</body>
</html>
'''


def render(name, text, version):
    head, _, body = text.partition('\n---\n')
    meta = dict(line.split(':', 1) for line in head.strip().splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    path = '/' if name == 'index' else '/' + name
    nav = ''.join('<a href="{0}"{1}>{2}</a>'.format(href, ' aria-current="page"' if href == path else '', label) for label, href in NAV)
    body = re.sub(r'\{icon:(\w+)\}', lambda m: icon(m.group(1)), body)
    extra = meta.get('robots')
    return LAYOUT.format(
        title=html.escape(meta['title']), description=html.escape(meta['description']), url=SITE + path, site=SITE,
        nav=nav, body=body.strip('\n'), version=version,
        extra_head=('<meta name="robots" content="' + extra + '">\n') if extra else '')


def main():
    version = str(int(max(os.path.getmtime(os.path.join(ROOT, 'assets', d, f)) for d, f in [('css', 'site.css'), ('js', 'site.js')])))
    pages = os.path.join(ROOT, 'src', 'pages')
    built = []
    for file in sorted(os.listdir(pages)):
        if not file.endswith('.html'):
            continue
        name = file[:-5]
        with open(os.path.join(pages, file), encoding='utf-8') as f:
            out = render(name, f.read(), version)
        with open(os.path.join(ROOT, file), 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        built.append(file)
    urls = [p for p in built if p not in ('404.html', 'thank-you.html')]
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for p in urls:
            f.write('  <url><loc>{0}{1}</loc></url>\n'.format(SITE, '/' if p == 'index.html' else '/' + p[:-5]))
        f.write('</urlset>\n')
    print('built', ', '.join(built))


if __name__ == '__main__':
    main()
