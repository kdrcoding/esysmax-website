# esysmax.com

The E-Sys MAX website: plain HTML, CSS and a little JavaScript, served by Hostinger from this repository.

| Page | What it does |
| --- | --- |
| `/` | Product, features, pricing, FAQ |
| `/download` | Installer from the update feed (`/updates/latest.json`) |
| `/buy` | PC ID + plan, then Stripe Checkout (`licence.esysmax.com/api/checkout`); or Telegram |
| `/thank-you` | The licence of a paid order (`/api/order`) |
| `/licence` | Activate, find a licence by e-mail + PC ID (`/api/lookup`), move to a new PC |
| `/privacy`, `/terms`, `/404` | |

The licence server (`licence.esysmax.com`, Vercel) is in the esys-max repository under `licence-bot/`.

## Edit

Pages live in `src/pages/*.html` (a few header lines, `---`, then the body); the shared header and footer in
`tools/build.py`. After editing:

    python tools/build.py      # writes the .html pages and sitemap.xml
    python tools/serve.py      # preview on http://localhost:8790

Commit the built pages too: Hostinger serves the repository as it is.

## Updates

Each release puts `latest.json` and `latest.json.sig` (signed with the update key) in `updates/`. The installer
itself is attached to a GitHub release; `latest.json` names its address. The launcher reads
`https://esysmax.com/updates/latest.json`.

## Hosting

- Hostinger: Websites > esysmax.com > Advanced > Git: this repository, branch `main`, directory empty
  (deploys into `public_html`). Turn on auto-deployment and add Hostinger's webhook URL to the GitHub repository.
- Cloudflare DNS: `esysmax.com` A record to the Hostinger IP, `www` CNAME to `esysmax.com` (DNS only, so Hostinger
  can issue the SSL certificate); `licence` A record `76.76.21.21` (Vercel, DNS only).
- `.htaccess`: https, no www, clean addresses (`/buy`), security headers, no caching for the update feed.
