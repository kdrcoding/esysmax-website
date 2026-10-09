"""Tells IndexNow search engines (Bing, Yandex, Seznam, Naver...) that pages changed. Run after a deploy is live:

    python tools/indexnow.py            every page in sitemap.xml
    python tools/indexnow.py /guides    only these paths

The key is INDEXNOW_KEY in tools/build.py; build.py writes it to /<key>.txt so the engines can check it.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://esysmax.com'
KEY = re.search(r"^INDEXNOW_KEY = '([0-9a-f]+)'", open(os.path.join(ROOT, 'tools', 'build.py'), encoding='utf-8').read(), re.M).group(1)

if len(sys.argv) > 1:
    urls = [SITE + (p if p.startswith('/') else '/' + p) for p in sys.argv[1:]]
else:
    urls = re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read())

body = json.dumps({'host': 'esysmax.com', 'key': KEY, 'keyLocation': SITE + '/' + KEY + '.txt', 'urlList': urls}).encode()
request = urllib.request.Request('https://api.indexnow.org/indexnow', data=body,
                                 headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
with urllib.request.urlopen(request, timeout=30) as answer:
    print('IndexNow:', answer.status, 'for', len(urls), 'pages')
