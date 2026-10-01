# NYE in Manchester

An independent guide to New Year's Eve in Manchester: a live countdown (GMT), an events directory with filters, a fireworks and where-to-watch guide, a planning guide, and a paid **List your event** page (£399).

## How it works

- `data/events.json`: every listing (name, venue, suburb, area, categories, price in £, inclusions, booking URL, `featured`). Prices marked "2025 price, TBC" are last year's and should be updated as venues release 2026 tickets.
- `src/style.css`, `src/main.js`: the design, the countdown, the fireworks animation, the directory filters and the listing form.
- `build.py`: generates the full static site into `docs/`.

```bash
python3 build.py                     # rebuild docs/
cd docs && python3 -m http.server    # preview at http://localhost:8000
```

`build.py` generates:

- Home page: countdown, filterable directory, timeline, where to see in the new year and FAQ
- Category landing pages: dinners, parties, club nights and family
- Fireworks page: the St Peter's Square fireworks (2024 and 2025) and where to watch
- Planning guide: timings, Metrolink, buses, trains, taxis, road closures, weather and accessibility
- List-your-event page with the £399 offer and an intake form
- One SEO page per event, with `Event` schema (prices in GBP)
- `sitemap.xml`, `robots.txt`, `404.html` and the OG image

## Before going live: edit `CONFIG` in `build.py`

| Key | What to set |
| --- | --- |
| `site_url` | `https://nyeinmanchester.com` (used for canonical URLs, the sitemap and OG tags) |
| `contact_email` | `aj@metatapdigital.com`: the inbox for listing requests |
| `form_endpoint` | `https://formsubmit.co/ajax/aj@metatapdigital.com`: emails each listing request to that inbox |
| `payment_link` | A Stripe Payment Link for £399 GBP. After the form saves, the buyer is redirected here with their email prefilled |

The first submission triggers a one-time FormSubmit activation email to `aj@metatapdigital.com`. Click the link in it, and every request after that arrives as a formatted email. Until `payment_link` is set, submitters see a thank-you message and you send them an invoice.

## Adding a paid listing

Add an entry to `data/events.json`. Set `"featured": true` if you want it pinned to the top with a badge. Then run `python3 build.py` and deploy.

## Deploying (Vercel)

`vercel.json` tells Vercel to serve the pre-built `docs/` folder. No build step runs, so always run `python3 build.py` and commit `docs/` before pushing.

1. On vercel.com, choose **Add New → Project**, import the `nyeinmanchester` repository and click **Deploy**. No settings need changing.
2. Under **Project → Settings → Domains**, add `nyeinmanchester.com` and `www.nyeinmanchester.com`, then set the DNS records Vercel shows at your registrar (usually an A record `76.76.21.21` for the apex and a CNAME `cname.vercel-dns.com` for `www`). `vercel.json` already redirects `www` to the apex.
3. Every push to the production branch redeploys the site automatically.

After launch, submit `https://nyeinmanchester.com/sitemap.xml` in Google Search Console.

To regenerate `og.png`, open `docs/og.html` at 1200×630 and screenshot it.
