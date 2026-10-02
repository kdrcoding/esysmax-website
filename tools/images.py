"""Makes the website's image sizes: WebP screenshots for phones and desktops, and small logos.

    python tools/images.py      (needs Pillow: pip install pillow)

Run it after changing an image, then `python tools/build.py`. Commit the files it writes.

- Screenshots: assets/img/<name>.jpg stays the source and the fallback for old browsers; <name>-<width>.webp are made from it.
- Logos: the large originals live in src/img/ (not served); the small sizes the pages use are written to assets/img/.
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'assets', 'img')
SRC = os.path.join(ROOT, 'src', 'img')

# name -> widths of the WebP files (the largest is the original width)
SCREENSHOTS = {
    'vehicle-order': [720, 1320],
    'cafd-panel': [461],
    'search': [640, 1164],
    'history': [640, 1164],
}


def resized(im, width=None, height=None):
    if width is None:
        width = round(im.width * height / im.height)
    if height is None:
        height = round(im.height * width / im.width)
    return im if (width, height) == im.size else im.resize((width, height), Image.LANCZOS)


def save(im, name, **options):
    path = os.path.join(IMG, name)
    im.save(path, **options)
    print('{0:32} {1:>4}x{2:<4} {3:>7,} bytes'.format(name, im.width, im.height, os.path.getsize(path)))


def main():
    for name, widths in SCREENSHOTS.items():
        im = Image.open(os.path.join(IMG, name + '.jpg')).convert('RGB')
        for width in widths:
            save(resized(im, width), '{0}-{1}.webp'.format(name, width), format='WEBP', quality=85, method=6)

    # Header and footer logo: 40 px high on screen (1x, 2x, 3x), PNG for browsers without WebP.
    logo = Image.open(os.path.join(SRC, 'logo-dark.png')).convert('RGBA')
    save(resized(logo, height=40), 'logo-dark.webp', format='WEBP', quality=90, method=6)
    save(resized(logo, height=80), 'logo-dark@2x.webp', format='WEBP', quality=90, method=6)
    save(resized(logo, height=120), 'logo-dark@3x.webp', format='WEBP', quality=90, method=6)
    save(resized(logo, height=80), 'logo-dark@2x.png', format='PNG', optimize=True)

    # The logo on the printed guide (34 px high on paper, sharp at about 300 dpi).
    printed = Image.open(os.path.join(SRC, 'logo-print.png')).convert('RGBA')
    save(resized(printed, width=360), 'logo-print.png', format='PNG', optimize=True)


if __name__ == '__main__':
    main()
