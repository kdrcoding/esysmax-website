"""Makes the website's image sizes: WebP screenshots for phones and desktops, and small logos.

    python tools/images.py          (needs Pillow: pip install pillow)
    python tools/images.py icons    (only the site icons: favicons, apple-touch-icon, manifest icon)

Run it after changing an image, then `python tools/build.py`. Commit the files it writes.

- Screenshots: assets/img/<name>.jpg stays the source and the fallback for old browsers; <name>-<width>.webp are made from it.
- Logos: the large originals live in src/img/ (not served); the small sizes the pages use are written to assets/img/.
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'assets', 'img')
SRC = os.path.join(ROOT, 'src', 'img')

# name -> widths of the WebP files (the largest is the original width)
SCREENSHOTS = {
    'vehicle-order': [720, 1318],
    'cafd-panel': [480, 862],
    'cafd-front': [560],
    'search': [640, 1148],
    'history': [640, 1304],
    'batch': [640, 984],
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

    icons()


# The site icon: the emblem on the site's dark background (the light grey emblem alone almost disappears on
# Google's white results page and in light browser tabs). Google wants a square favicon whose size is a multiple
# of 48 px, linked from the home page; tools/build.py links these files and writes /site.webmanifest.
ICON_BG = (11, 12, 15, 255)  # --bg in site.css


def icon_square(size, fill, radius=0.0):
    """The emblem, cropped to its outline, centred on a dark square `size` px wide; `fill` is the emblem's share
    of the width, `radius` the corner rounding as a share of the width (0: a plain square)."""
    emblem = Image.open(os.path.join(IMG, 'emblem-512.png')).convert('RGBA')
    emblem = emblem.crop(emblem.getchannel('A').getbbox())
    big = size * 8  # drawn large, then scaled down once: crisp edges at 16 px too
    canvas = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    mask = Image.new('L', (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), radius=round(big * radius), fill=255)
    canvas.paste(Image.new('RGBA', (big, big), ICON_BG), (0, 0), mask)
    art = resized(emblem, width=round(big * fill))
    canvas.alpha_composite(art, ((big - art.width) // 2, (big - art.height) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def icons():
    # Browser tabs and Google: slightly rounded; the emblem stays inside the circle Google crops
    # its result icons to; in the 16 and 32 px tab icons it fills more of the square, so it stays readable.
    for size in (48, 96, 192):
        save(icon_square(size, 0.76, 0.18), 'favicon-{0}.png'.format(size), format='PNG', optimize=True)
    # Home screens (Android via site.webmanifest, iOS via apple-touch-icon): plain squares, the system rounds them.
    save(icon_square(512, 0.72), 'icon-512.png', format='PNG', optimize=True)
    save(icon_square(180, 0.72), 'apple-touch-icon.png', format='PNG', optimize=True)
    # /favicon.ico at the site root: 16, 32 and 48 px, each drawn at its own size.
    small = [icon_square(s, 0.86 if s < 48 else 0.76, 0.18) for s in (16, 32, 48)]
    path = os.path.join(ROOT, 'favicon.ico')
    small[-1].save(path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)], append_images=small[:-1])
    print('{0:32} 16, 32, 48   {1:>7,} bytes'.format('favicon.ico (site root)', os.path.getsize(path)))


if __name__ == '__main__':
    import sys
    icons() if sys.argv[1:] == ['icons'] else main()
