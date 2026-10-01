#!/usr/bin/env python3
"""Static site generator for NYE in Manchester.

Edit data/events.json (and the CONFIG block below), then run:
    python3 build.py
The complete site is written to ./docs, which Vercel serves as-is (see vercel.json).
"""
import json
import shutil
from datetime import date
from html import escape
from pathlib import Path

# --------------------------------------------------------------------------------------
# CONFIG: change these before going live
# --------------------------------------------------------------------------------------
CONFIG = {
    "site_name": "NYE in Manchester",
    "site_url": "https://nyeinmanchester.com",   # your live domain, no trailing slash
    "contact_email": "aj@metatapdigital.com",
    "listing_price": 399,                        # GBP
    "currency": "GBP",
    # Listing submissions are emailed to contact_email via FormSubmit (no account needed;
    # the first submission sends a one-time activation email to that inbox).
    "form_endpoint": "https://formsubmit.co/ajax/aj@metatapdigital.com",
    # Stripe Payment Link (or similar) for the £399 listing fee. While it still contains
    # "YOUR_", submitters see a thank-you message and you email them an invoice instead.
    "payment_link": "https://buy.stripe.com/YOUR_PAYMENT_LINK",
    "year": 2026,
    "next_year": 2027,
}

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
EVENTS = json.loads((ROOT / "data" / "events.json").read_text())
TODAY = date.today().isoformat()
Y, NY = CONFIG["year"], CONFIG["next_year"]
URL = CONFIG["site_url"]
P = CONFIG["listing_price"]

CATEGORY_LABELS = {
    "party": "Parties",
    "club": "Club nights",
    "dining": "Dinners",
    "fine-dining": "Fine dining",
    "rooftop": "Rooftops & skyline",
    "live-music": "Live music",
    "gay-village": "Gay Village",
    "family": "Family-friendly",
    "budget": "Under £30",
    "free": "Free",
}
AREAS = sorted({e["area"] for e in EVENTS})

NAV = [
    ("/", "Home"),
    ("/#directory", "All events"),
    ("/new-years-eve-dinner-manchester/", "Dinners"),
    ("/new-years-eve-parties-manchester/", "Parties"),
    ("/manchester-nye-club-nights/", "Club nights"),
    ("/manchester-fireworks-new-years-eve/", "Fireworks"),
    ("/plan-your-night/", "Plan"),
]


def j(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")


def money(n):
    if n == 0:
        return "Free"
    return f"£{n:,.0f}" if float(n).is_integer() else f"£{n:,.2f}"


# Manchester skyline: Beetham Tower, Town Hall clock tower, Central Library rotunda,
# Deansgate Square towers and a run of mill and office blocks, above the canal.
SKYLINE = """<svg class="skyline" viewBox="0 0 1440 230" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c0a26"/><stop offset="1" stop-color="#07061a"/></linearGradient>
<linearGradient id="wt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1a1450" stop-opacity=".9"/><stop offset="1" stop-color="#07061a"/></linearGradient></defs>
<g fill="url(#sk)">
<rect x="0" y="128" width="46" height="72"/><rect x="50" y="104" width="34" height="96"/><rect x="88" y="138" width="40" height="62"/>
<rect x="132" y="116" width="30" height="84"/><rect x="166" y="96" width="38" height="104"/><rect x="208" y="132" width="34" height="68"/>
<rect x="246" y="150" width="70" height="50"/><rect x="252" y="140" width="6" height="12"/><rect x="280" y="140" width="6" height="12"/>
<rect x="320" y="120" width="36" height="80"/>
<rect x="372" y="26" width="30" height="174"/><rect x="368" y="62" width="40" height="10"/><rect x="384" y="10" width="4" height="18"/>
<rect x="414" y="110" width="34" height="90"/><rect x="452" y="132" width="40" height="68"/>
<rect x="500" y="150" width="120" height="50"/><rect x="540" y="110" width="22" height="42"/><path d="M536 112 L551 54 L566 112Z"/>
<rect x="508" y="138" width="10" height="14"/><rect x="600" y="138" width="10" height="14"/>
<rect x="640" y="146" width="96" height="54"/><path d="M640 148 Q688 104 736 148Z"/><rect x="646" y="140" width="84" height="8"/>
<rect x="750" y="118" width="34" height="82"/><rect x="788" y="98" width="28" height="102"/><rect x="820" y="130" width="40" height="70"/>
<rect x="866" y="84" width="30" height="116"/><rect x="900" y="122" width="34" height="78"/><rect x="938" y="140" width="46" height="60"/>
<rect x="990" y="106" width="30" height="94"/><rect x="1024" y="128" width="34" height="72"/>
<path d="M1066 200 L1066 40 L1100 30 L1100 200Z"/><path d="M1108 200 L1108 62 L1138 54 L1138 200Z"/>
<path d="M1146 200 L1146 22 L1182 12 L1182 200Z"/><path d="M1190 200 L1190 82 L1218 76 L1218 200Z"/>
<rect x="1228" y="118" width="38" height="82"/><rect x="1270" y="100" width="30" height="100"/><rect x="1304" y="134" width="40" height="66"/>
<rect x="1348" y="112" width="32" height="88"/><rect x="1384" y="138" width="56" height="62"/>
</g>
<rect x="0" y="198" width="1440" height="32" fill="url(#wt)"/>
</svg>"""


def countdown(mini=False):
    units = [("d", "Days"), ("h", "Hours"), ("m", "Minutes"), ("s", "Seconds")]
    inner = "".join(
        f'<div class="cd-unit"><div class="cd-num" data-u="{k}">--</div><div class="cd-label">{v}</div></div>'
        for k, v in units
    )
    return f'<div class="countdown{" mini" if mini else ""}" data-countdown role="timer" aria-label="Countdown to midnight, New Year\'s Eve {Y} in Manchester">{inner}</div>'


def layout(path, title, description, body, schema=None, og_type="website", active=None):
    canonical = URL + path
    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": CONFIG["site_name"],
            "url": URL + "/",
            "potentialAction": {
                "@type": "SearchAction",
                "target": URL + "/?q={search_term_string}#directory",
                "query-input": "required name=search_term_string",
            },
        }
    ] if path == "/" else []
    schemas += schema or []
    cur = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{h}"{cur if h == (active or path) else ""}>{t}</a></li>' for h, t in NAV
    )
    ld = "".join(f'<script type="application/ld+json">{j(s)}</script>' for s in schemas)
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="geo.region" content="GB-MAN"><meta name="geo.placename" content="Manchester">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{CONFIG['site_name']}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{URL}/og.png"><meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{URL}/og.png">
<meta name="theme-color" content="#07061a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="nav"><div class="wrap">
<a class="logo" href="/">NYE <span>in Manchester</span></a>
<nav aria-label="Main"><ul>{nav}</ul></nav>
<a class="btn btn-primary btn-sm" href="/list-your-event/">List your event</a>
<button class="menu-btn" aria-label="Menu" aria-expanded="false">☰</button>
</div></header>
<main id="main">
{body}
</main>
<footer><div class="wrap">
<div class="fgrid">
<div><a class="logo" href="/">NYE <span>in Manchester</span></a>
<p class="muted">The independent guide to New Year's Eve {Y} in Manchester: parties, club nights, dinners, rooftop bars, family events and the city's fireworks, all in one place.</p>
{countdown(mini=True)}</div>
<div><h4>Explore</h4><ul>
<li><a href="/#directory">All NYE events</a></li><li><a href="/new-years-eve-dinner-manchester/">NYE dinners</a></li>
<li><a href="/new-years-eve-parties-manchester/">NYE parties</a></li><li><a href="/manchester-nye-club-nights/">Club nights</a></li>
<li><a href="/family-new-years-eve-manchester/">Family NYE</a></li></ul></div>
<div><h4>Plan</h4><ul>
<li><a href="/manchester-fireworks-new-years-eve/">Fireworks &amp; where to watch</a></li><li><a href="/plan-your-night/">Plan your night</a></li>
<li><a href="/plan-your-night/#transport">Getting home</a></li><li><a href="/#faq">FAQ</a></li></ul></div>
<div><h4>Venues</h4><ul>
<li><a href="/list-your-event/">List your event: £{P}</a></li>
<li><a href="mailto:{CONFIG['contact_email']}">{CONFIG['contact_email']}</a></li></ul></div>
</div>
<p class="fine">NYE in Manchester is an independent guide and is not affiliated with Manchester City Council, Transport for Greater Manchester or any official New Year's Eve event. Prices and details are supplied by venues or based on published information and may change. Prices marked "2025 price, TBC" are last year's and will be updated as venues release {Y} tickets. Always confirm with the venue before booking. © {Y} {CONFIG['site_name']}.</p>
</div></footer>
<script src="/main.js" defer></script>
</body>
</html>"""


# --------------------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------------------
def card(e, i):
    cats = " ".join(e["categories"])
    search = " ".join([e["name"], e["venue"], e["suburb"], e["area"], " ".join(e["categories"]), e["blurb"]]).lower()
    tags = "".join(f'<span class="tag">{CATEGORY_LABELS.get(c, c)}</span>' for c in e["categories"][:3])
    price = e["price_from"]
    price_html = (
        "Free<small>no ticket needed</small>" if price == 0
        else f"{money(price)}<small>from, per person</small>" if price
        else "TBA<small>see venue</small>"
    )
    return f"""<article class="card{' featured' if e.get('featured') else ''}" data-cats="{cats}" data-area="{escape(e['area'])}" data-price="{price if price is not None else ''}" data-featured="{1 if e.get('featured') else 0}" data-order="{i}" data-search="{escape(search)}">
{'<span class="badge">Featured</span>' if e.get('featured') else ''}
<div class="loc">📍 {escape(e['suburb'] if e['suburb'] in e['area'] else e['suburb'] + ' · ' + e['area'])}</div>
<h3><a href="/events/{e['slug']}/">{escape(e['name'])}</a></h3>
<p>{escape(e['blurb'])}</p>
<div class="tags"><span class="tag fw">🎆 {escape(e['fireworks'])}</span>{tags}</div>
<div class="meta"><div class="price">{price_html}</div>
<div class="actions"><a class="btn btn-ghost btn-sm" href="/events/{e['slug']}/">Details</a><a class="btn btn-primary btn-sm" href="{e['url']}" target="_blank" rel="noopener sponsored">Book</a></div></div>
</article>"""


def directory(events, heading, sub, show_filters=True, anchor="directory"):
    used = []
    for e in events:
        for c in e["categories"]:
            if c not in used:
                used.append(c)
    order = [c for c in CATEGORY_LABELS if c in used]
    chips = '<button class="chip" data-cat="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" data-cat="{c}" aria-pressed="false">{CATEGORY_LABELS[c]}</button>' for c in order
    )
    areas = '<option value="all">All areas</option>' + "".join(
        f'<option>{escape(a)}</option>' for a in AREAS if any(e["area"] == a for e in events)
    )
    filters = f"""<div class="filters" role="group" aria-label="Filter by type">{chips}</div>
<div class="toolbar"><input id="q" type="search" placeholder="Search venue, area, vibe…" aria-label="Search events">
<select id="area" aria-label="Filter by area">{areas}</select>
<select id="sort" aria-label="Sort"><option value="featured">Sort: Featured</option><option value="low">Price: low to high</option><option value="high">Price: high to low</option></select></div>
<p class="count" aria-live="polite"></p>""" if show_filters else ""
    cards = "".join(card(e, i) for i, e in enumerate(events))
    return f"""<section id="{anchor}" data-directory><div class="wrap">
<div class="section-head"><h2>{heading}</h2><p>{sub}</p></div>
{filters}
<div class="grid">{cards}</div>
<p class="empty">No events match that search. Try another filter, or <a href="/list-your-event/">list yours</a>.</p>
</div></section>"""


def season_section(p):
    months = [
        ("October", "Planning begins",
         "Club nights, rooftop bars and restaurants release NYE tickets, and Manchester starts searching \"NYE Manchester\". Early birds grab first-release tickets and groups start comparing options.",
         "List now and you're live for the whole season, from day one."),
        ("November", "Comparing &amp; booking",
         "Searchers compare prices, inclusions and line-ups side by side. This is when dinner tables, skyline bars and party tickets get booked.",
         "Your page, with its price, inclusions and a Book button, wins the comparison."),
        ("December", "Peak searches &amp; last-minute rush",
         "Search interest hits its peak after Christmas. People chase the last tables, final release tiers and late tickets right up to 31 December.",
         "Sell your remaining tickets and late sittings while demand is at its highest."),
    ]
    cards = "".join(
        f'''<div class="card season-card"><span class="season-step">{i + 1}</span><div class="loc">{m}</div><h3>{t}</h3><p>{d}</p>
<p class="season-win">✦ {w}</p></div>''' for i, (m, t, d, w) in enumerate(months)
    )
    return f"""<section id="season"><div class="wrap">
<div class="section-head"><span class="eyebrow">The NYE search season</span>
<h2>Manchester books New Year's Eve in <span class="grad">three months</span></h2>
<p>Every year, searches like "new years eve Manchester", "NYE Manchester" and "new years eve dinner Manchester" climb from October and peak in the final weeks of December. That's when people choose a venue and buy tickets. If your event isn't in front of them then, they book somewhere else.</p></div>
<div class="season-bar" aria-hidden="true"><span style="--h:34%">Oct</span><span style="--h:62%">Nov</span><span style="--h:100%">Dec</span></div>
<p class="muted" style="text-align:center;font-size:.8rem;margin:-6px 0 30px">Shows the typical seasonal pattern of search interest, not exact volumes.</p>
<div class="grid">{cards}</div>
<div class="band" style="margin-top:40px">
<div><h2>One listing. The whole season.</h2><p>With Manchester NYE dinners and skyline parties typically £75–£250 a head, a few bookings covers your £{p} listing. Everything after that is profit, with zero commission.</p></div>
<a class="btn" href="#form">Claim your spot →</a></div>
</div></section>"""


def list_band():
    return f"""<section><div class="wrap"><div class="band">
<div><h2>Selling NYE tickets in Manchester?</h2><p>October to December is when Manchester searches for its New Year's Eve plans. Get your event in front of them for £{P} flat, with no commission.</p></div>
<a class="btn" href="/list-your-event/">List your event →</a></div></div></section>"""


def item_list(events, name):
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "numberOfItems": len(events),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{URL}/events/{e['slug']}/", "name": e["name"]}
            for i, e in enumerate(events)
        ],
    }


def breadcrumbs(*pairs):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": URL + p} for i, (n, p) in enumerate(pairs)
        ],
    }


# --------------------------------------------------------------------------------------
# Content: FAQ, timeline, where to see in the new year
# --------------------------------------------------------------------------------------
FAQ = [
    (f"Are there fireworks in Manchester on New Year's Eve {Y}?",
     f"Manchester City Council has run free midnight fireworks for the last three New Year's Eves: at Castlefield Bowl in 2023, then at St Peter's Square in 2024 and 2025, launched from the roof of Central Library. In 2025 the show lasted about eight minutes and more than 20,000 people celebrated across St Peter's Square and Albert Square. The council has not yet confirmed plans for {Y}. We'll update our <a href=\"/manchester-fireworks-new-years-eve/\">fireworks page</a> as soon as it does."),
    ("What time are the Manchester New Year's Eve fireworks?",
     "At midnight. In 2025 the free St Peter's Square event opened at 10pm with a DJ-led countdown, the fireworks and laser show started on the stroke of midnight, and the square closed at about 12:30am. Arrive early, because entry stops once the square is full."),
    ("What are the best New Year's Eve parties in Manchester?",
     f"For clubbing, The Warehouse Project at Depot Mayfield is the big one, with Defected and Glitterbox confirmed for {Y}. Albert's Schloss, Diecast, Refuge, Bongo's Bingo at Albert Hall and Freight Island's Little Disco are the big themed parties. For skyline views, look at 20 Stories, Cloud 23 and Claude's Skyview Bar. See all <a href=\"/new-years-eve-parties-manchester/\">NYE parties in Manchester</a>."),
    ("Where can I have New Year's Eve dinner in Manchester?",
     "Spinningfields and Deansgate have the biggest choice: 20 Stories, Australasia, Sexy Fish, Louis and James Martin all run NYE menus, with prices from about £75 to £500 a head. Chotto Matte, Lucky Cat and The Cut &amp; Craft are close to St Peter's Square. See our <a href=\"/new-years-eve-dinner-manchester/\">NYE dinners in Manchester</a> list."),
    ("Is there anything free to do in Manchester on New Year's Eve?",
     "Yes. In 2025 the St Peter's Square fireworks and the Albert Square fair (with its giant Ferris wheel) were both free to enter, with rides charged separately. Freight Island's Little Disco and Crazy Pedro's Bridge Street also offered free entry. Look for the \"Free\" filter in our directory."),
    ("Are trams running on New Year's Eve in Manchester?",
     "In 2025 Metrolink ran trams every 12 minutes on New Year's Eve, with the last trams leaving the city centre at about 1am, and no trams ran through St Peter's Square after 9pm because of the event. Bee Network buses ran a Saturday timetable with some late journeys. Check tfgm.com for the official 2026 timetable closer to the date."),
    ("What should I wear and bring on New Year's Eve in Manchester?",
     "Dress for cold and probably rain: late-December nights in Manchester are usually only a few degrees above freezing. At the 2025 city events bags had to be A4 or smaller, glass was banned and everyone was searched on entry. Many parties and restaurants have dress codes, so check before you go."),
    ("What are the best family-friendly NYE options in Manchester?",
     "Daytime countdowns are the easiest: LEGOLAND Discovery Centre's NYE party, Raver Tots at Freight Island, Our Kids Social at MediaCity and Noon Year's Eve at Albert's Schloss. In 2025 the St Peter's Square fireworks were alcohol-free and family-friendly, but they happen at midnight and the square is standing only. See <a href=\"/family-new-years-eve-manchester/\">family NYE in Manchester</a>."),
    ("Are the Manchester Christmas Markets open on New Year's Eve?",
     "Mostly not. In 2025 the main Christmas Markets closed on 22 December, but the Albert Square Ferris wheel, fairground rides and stalls, and the Cathedral Gardens ice rink, stayed open until 4 January."),
    ("Is NYE in Manchester an official council website?",
     "No. NYE in Manchester is an independent guide and event directory. The free city centre events are run by Manchester City Council. We bring together official event information and bookable parties, club nights and dinners so you can plan the whole night in one place."),
    ("How do I list my New Year's Eve event on NYE in Manchester?",
     f"It's a one-off £{P} fee with no commission. Your event gets its own optimised page, a place in our directory and category pages, and a direct link to your booking page. <a href=\"/list-your-event/\">List your event here</a>."),
]


def faq_html(items):
    return "".join(f"<details><summary>{escape(q)}</summary><p>{a}</p></details>" for q, a in items)


def faq_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items
        ],
    }


TIMELINE = [
    ("Morning", "Family parties start: LEGOLAND, Our Kids Social and, later, Raver Tots. In 2025 Albert Square opened at 10am."),
    ("1:00pm", "In 2025 city centre road closures around St Peter's Square, Peter Street and Oxford Street started from the afternoon."),
    ("About 4:00pm", "Sunset. It's dark, cold and often wet from here, so plan to be indoors or wrapped up."),
    ("Early evening", "Early dinner sittings, concerts at The Bridgewater Hall and Manchester Cathedral, and warm-up parties."),
    ("9:00pm", "In 2025 trams stopped running through St Peter's Square. Use Deansgate-Castlefield, Piccadilly Gardens or Market Street instead."),
    ("10:00pm", "The free St Peter's Square countdown opened in 2025. Late dinner sittings begin and the clubs fill up."),
    ("Midnight", f"Fireworks and lasers from the Central Library roof (2024 and 2025) and countdowns across the city to welcome {NY}."),
    ("12:30am – 4:00am", "The squares close and the clubs keep going. In 2025 the last trams left the city centre at about 1am, so book a taxi or plan your route home."),
]


def timeline_html():
    return '<div class="timeline">' + "".join(
        f'<div class="tl"><b>{t}</b><p>{d}</p></div>' for t, d in TIMELINE
    ) + "</div>"


VANTAGE = [
    ("St Peter's Square", "City centre", "Fireworks and lasers from the Central Library roof", "free",
     "2024 and 2025 format: opened 10pm, alcohol-free, standing only, closes when full. 2026 TBC"),
    ("Albert Square", "City centre", "Ferris wheel, food and drink stalls", "free",
     "2025: open 10am to 12:30am, rides charged. No walk-through to St Peter's Square"),
    ("Cloud 23, Beetham Tower", "Deansgate", "23rd-floor views over the whole city", "paid",
     "Ticketed NYE packages with a table all night"),
    ("20 Stories", "Spinningfields", "19th-floor rooftop terrace, 360-degree skyline", "paid",
     f"Midnight Masquerade confirmed for {Y}, from £79.50"),
    ("Claude's Skyview Bar", "St Michael's, Jackson's Row", "High-up bar above Chotto Matte", "paid",
     "Sold on fireworks views in 2025 (£125pp)"),
    ("Cathedral Gardens", "Victoria", "Ice rink and food stalls", "check",
     "Stayed open over New Year in 2025; check NYE session times"),
]
PILL = {
    "free": '<span class="pill free">Free</span>',
    "free-t": '<span class="pill free">Free · ticket</span>',
    "paid": '<span class="pill paid">Paid ticket</span>',
    "check": '<span class="pill af">Check entry</span>',
}


def vantage_table(rows=None):
    rows = rows or VANTAGE
    body = "".join(
        f"<tr><td><b>{n}</b></td><td>{a}</td><td>{v}</td><td>{PILL[t]}</td><td class='muted'>{note}</td></tr>"
        for n, a, v, t, note in rows
    )
    return f"""<div class="table-wrap"><table><thead><tr><th>Where</th><th>Area</th><th>What you'll see</th><th>Entry</th><th>Good to know</th></tr></thead>
<tbody>{body}</tbody></table></div>"""


# --------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------
DIR_SUB = "Filter by type, area or budget. Every listing shows what's included, the price and a direct booking link. Prices marked \"2025 price, TBC\" are last year's."


def page_home():
    featured = [e for e in EVENTS if e.get("featured")]
    rest = [e for e in EVENTS if not e.get("featured")]
    ordered = featured + rest
    n = len(EVENTS)
    body = f"""
<section class="hero"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap">
<span class="eyebrow">Thursday 31 December {Y} · Manchester</span>
<h1>New Year's Eve {Y}<br><span class="grad">in Manchester</span></h1>
<p class="lead">The best NYE events in Manchester in one place: club nights, rooftop and skyline bars, NYE dinners, family countdowns and the city's free fireworks. Compare, choose and book your night to welcome {NY}.</p>
{countdown()}
<p class="cd-note">until midnight in Manchester</p>
<div class="cta-row"><a class="btn btn-primary" href="#directory">Browse {n} NYE events</a><a class="btn btn-ghost" href="/manchester-fireworks-new-years-eve/">Fireworks &amp; where to watch</a></div>
</div></section>

<div class="wrap"><div class="facts">
<div class="fact"><b>Midnight</b><span>Free city fireworks at St Peter's Square in 2024 &amp; 2025 (2026 TBC)</span></div>
<div class="fact"><b>20,000+</b><span>people at the city centre squares on NYE 2025</span></div>
<div class="fact"><b>4am</b><span>when the big club nights finish</span></div>
<div class="fact"><b>{n}</b><span>parties, club nights, dinners &amp; family events</span></div>
</div></div>

{directory(ordered, f"Every Manchester NYE {Y} event in one directory", DIR_SUB)}

{list_band()}

<section class="alt"><div class="wrap two">
<div><h2>Your NYE {Y} in Manchester, <span class="grad">hour by hour</span></h2>
<p class="muted">Timings are based on the 2025 city events. Manchester City Council and TfGM confirm the {Y} plans closer to the night. Use this to plan when to eat, move and get home.</p>
<a class="btn btn-ghost" href="/plan-your-night/">Full planning guide →</a></div>
{timeline_html()}
</div></section>

<section><div class="wrap">
<div class="section-head"><h2>Where to see in the new year</h2><p>The free city centre squares and the skyline bars with the best views at midnight.</p></div>
{vantage_table()}
<p style="text-align:center;margin-top:24px"><a class="btn btn-ghost" href="/manchester-fireworks-new-years-eve/">Fireworks guide →</a></p>
</div></section>

<section class="alt"><div class="wrap">
<div class="section-head"><h2>Find your kind of NYE</h2></div>
<div class="grid">
<div class="card"><h3><a href="/new-years-eve-dinner-manchester/">🍽️ NYE dinners in Manchester</a></h3><p>From £27.50 daytime set menus to a £500 black-tie soirée in Spinningfields.</p><a href="/new-years-eve-dinner-manchester/">Browse dinners →</a></div>
<div class="card"><h3><a href="/new-years-eve-parties-manchester/">🎉 NYE parties &amp; rooftops</a></h3><p>Albert's Schloss, 20 Stories, Cloud 23, Diecast, Refuge and Canal Street.</p><a href="/new-years-eve-parties-manchester/">Browse parties →</a></div>
<div class="card"><h3><a href="/manchester-nye-club-nights/">🎧 NYE club nights</a></h3><p>The Warehouse Project, Hidden, Gorilla, Dandy and more, mostly until 4am.</p><a href="/manchester-nye-club-nights/">Browse club nights →</a></div>
<div class="card"><h3><a href="/family-new-years-eve-manchester/">👨‍👩‍👧 Family-friendly NYE</a></h3><p>Daytime countdowns, family raves and the free city squares.</p><a href="/family-new-years-eve-manchester/">Browse family events →</a></div>
</div></div></section>

<section id="faq"><div class="wrap">
<div class="section-head"><h2>New Year's Eve in Manchester {Y}: FAQ</h2></div>
<div class="faq">{faq_html(FAQ)}</div>
</div></section>
"""
    return layout(
        "/",
        f"New Year's Eve Manchester {Y}: NYE Parties, Events & Dinners | NYE in Manchester",
        f"Plan New Year's Eve {Y} in Manchester: live countdown, {n} NYE parties, club nights, dinners, rooftop bars and family events, plus fireworks news, transport and prices in £.",
        body,
        schema=[item_list(ordered, f"Manchester New Year's Eve {Y} events"), faq_schema(FAQ),
                {"@context": "https://schema.org", "@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/",
                 "logo": URL + "/favicon.svg", "email": CONFIG["contact_email"]}],
    )


CATEGORY_PAGES = [
    {
        "path": "/new-years-eve-dinner-manchester/",
        "filter": lambda e: "dining" in e["categories"] or "fine-dining" in e["categories"],
        "title": f"New Year's Eve Dinner Manchester {Y}: NYE Restaurants & Set Menus",
        "h1": f"New Year's Eve dinners in Manchester {Y}",
        "desc": f"The best New Year's Eve dinners in Manchester {Y}: NYE set menus, tasting menus, skyline restaurants and dinner-and-party packages in Spinningfields, Deansgate and beyond, with prices in £.",
        "intro": "A long dinner is the most comfortable way to see in the new year in Manchester: warm, seated and close to the party. Early sittings are cheaper and leave time to move on. Late sittings and dinner-and-dance packages take you right through to midnight.",
        "tips": ["Book early. Window tables at 20 Stories and Cloud 23 sell out first.", "Early sittings are usually the best value and free up the rest of your night.", "Check whether the price includes the party afterwards or just dinner.", "Look at the dress code: several venues ask for black tie or no trainers."],
    },
    {
        "path": "/new-years-eve-parties-manchester/",
        "filter": lambda e: "party" in e["categories"] or "rooftop" in e["categories"],
        "title": f"NYE Parties Manchester {Y}: Best New Year's Eve Parties & Rooftop Bars",
        "h1": f"The best New Year's Eve parties in Manchester {Y}",
        "desc": f"Manchester's best New Year's Eve parties for {Y}: Albert's Schloss, 20 Stories, Cloud 23, Diecast, Refuge, Canal Street and budget bar parties, with prices, inclusions and tickets.",
        "intro": "From skyline bars on the 23rd floor to warehouse carnivals and Canal Street, these are the best NYE parties in Manchester. Some include dinner and drinks, others are cheap bar parties where you pay as you go.",
        "tips": ["Many parties release tickets in tiers, so the first release is the cheapest.", "Check whether drinks are included or pay-as-you-go.", "Most parties are 18+ (Albert's Schloss is 21+) with ID checks.", "Note last entry times. Some venues stop letting people in at 10:30pm."],
    },
    {
        "path": "/manchester-nye-club-nights/",
        "filter": lambda e: "club" in e["categories"] or "gay-village" in e["categories"],
        "title": f"Manchester NYE Club Nights {Y}: Warehouse Project, Hidden & More",
        "h1": f"Manchester New Year's Eve club nights {Y}",
        "desc": f"Manchester NYE club nights for {Y}: The Warehouse Project at Depot Mayfield, Hidden, Gorilla, Dandy, Canal Street and the Gay Village, with line-ups and ticket prices.",
        "intro": "Manchester is one of the best clubbing cities in Europe, and New Year's Eve is its biggest night. Expect warehouse stages until 4am, Gay Village parties and underground clubs. Tickets for the big nights usually go on sale in the autumn.",
        "tips": ["Sign up for presale alerts: the cheapest tiers go fast.", "Plan your route home before you go out. Trams finished at about 1am in 2025.", "Bring photo ID, even if you look older than 25.", "Check last entry times and bag policies on your ticket."],
    },
    {
        "path": "/family-new-years-eve-manchester/",
        "filter": lambda e: "family" in e["categories"],
        "title": f"Family New Year's Eve Manchester {Y}: Kid-Friendly NYE Events",
        "h1": f"Family-friendly New Year's Eve in Manchester {Y}",
        "desc": f"Kid-friendly ways to celebrate New Year's Eve {Y} in Manchester: daytime countdown parties, family raves, LEGOLAND, MediaCity and the free city centre squares.",
        "intro": "Manchester's best family NYE plans happen in daylight: countdown parties with balloon drops, family raves and silent discos, all finished by teatime. In 2025 the city's midnight fireworks at St Peter's Square were alcohol-free and family-friendly, but they're late and standing only.",
        "tips": ["Daytime countdowns sell out, so book as soon as tickets are released.", "Bring ear defenders for babies and toddlers at raves and fireworks.", "Wrap up warm and pack waterproofs if you'll be outdoors.", "Agree on a meeting point in case anyone gets separated in the crowds."],
    },
]


def page_category(c):
    events = [e for e in EVENTS if c["filter"](e)]
    events.sort(key=lambda e: (not e.get("featured"), e["price_from"] if e["price_from"] is not None else 1e9))
    tips = "".join(f"<li>{t}</li>" for t in c["tips"])
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">NYE {Y} · Manchester</span><h1>{c['h1']}</h1>
<p class="lead">{c['intro']}</p>{countdown(mini=True)}</div></section>
<section style="padding-bottom:0"><div class="wrap two">
<div class="panel"><h2 style="font-size:1.5rem">Booking tips</h2><ul class="ticks">{tips}</ul></div>
<div><h2 style="font-size:1.5rem">{len(events)} options, compared</h2><p class="muted">Every listing shows a "from" price and what's included. Prices are per person in pounds and based on published packages. Where {Y} prices aren't out yet we show the 2025 price, so always confirm the current price with the venue.</p>
<a class="btn btn-primary" href="/list-your-event/">Add your venue: £{P}</a></div>
</div></section>
{directory(events, c['h1'], 'Filter and sort to find your night.')}
{list_band()}"""
    return layout(
        c["path"], c["title"] + " | NYE in Manchester", c["desc"], body,
        schema=[item_list(events, c["h1"]), breadcrumbs(("Home", "/"), (c["h1"], c["path"]))],
    )


def page_event(e):
    path = f"/events/{e['slug']}/"
    inc = "".join(f"<li>{escape(x)}</li>" for x in e["includes"])
    cats = ", ".join(CATEGORY_LABELS.get(c, c) for c in e["categories"])
    related = [x for x in EVENTS if x["slug"] != e["slug"] and (x["area"] == e["area"] or set(x["categories"]) & set(e["categories"]))][:3]
    offer = {"@type": "Offer", "url": e["url"], "priceCurrency": CONFIG["currency"], "availability": "https://schema.org/InStock",
             "validFrom": f"{Y}-01-01"}
    if e["price_from"] is not None:
        offer["price"] = e["price_from"]
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": f"{e['name']} – New Year's Eve {Y}",
        "description": e["blurb"] + " Includes: " + "; ".join(e["includes"]) + ".",
        "startDate": f"{Y}-12-31",
        "endDate": f"{NY}-01-01",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "image": [f"{URL}/og.png"],
        "location": {
            "@type": "Place", "name": e["venue"],
            "address": {"@type": "PostalAddress", "streetAddress": e["venue"].split(",", 1)[-1].strip() if "," in e["venue"] else e["venue"],
                        "addressLocality": "Salford" if "Salford" in e["area"] or "Salford" in e["suburb"] else "Trafford" if e["area"] == "Trafford" else "Manchester",
                        "addressRegion": "Greater Manchester", "addressCountry": "GB"},
        },
        "organizer": {"@type": "Organization", "name": e["venue"].split(",")[0], "url": e["url"]},
        "offers": offer,
    }
    body = f"""
<section class="event-hero"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/#directory">NYE events</a> › {escape(e['name'])}</nav>
<span class="eyebrow">New Year's Eve {Y} · {escape(e['suburb'])}</span>
<h1 style="font-size:clamp(2rem,5vw,3.4rem)">{escape(e['name'])}</h1>
<p class="lead muted" style="font-size:1.15rem;max-width:760px">{escape(e['blurb'])}</p>
</div></section>
<section style="padding-top:10px"><div class="wrap event-layout">
<div>
<div class="panel"><h2 style="font-size:1.5rem">What's included</h2><ul class="ticks">{inc}</ul></div>
<div class="prose" style="margin-top:30px">
<h2 style="font-size:1.5rem">About {escape(e['name'])}</h2>
<p>{escape(e['name'])} is at {escape(e['venue'])} in {escape(e['suburb'])} ({escape(e['area'])}). It's one of the {escape(cats.lower())} options for New Year's Eve {Y} in Manchester. At midnight: <b>{escape(e['fireworks'])}</b>. Age: <b>{escape(e['age'])}</b>.</p>
<p>Planning the rest of your night? Check the <a href="/plan-your-night/">timeline and how to get home</a> or read our guide to <a href="/manchester-fireworks-new-years-eve/">the city's fireworks and where to watch</a>.</p>
<p class="notice">Details are based on the venue's published NYE information and can change. Prices marked "2025 price, TBC" are from last year. Confirm the price, times and inclusions with {escape(e['venue'].split(',')[0])} before booking. Are you the venue? <a href="/list-your-event/">Claim and upgrade this listing</a>.</p>
</div></div>
<aside class="side panel">
<div class="price" style="font-size:2rem">{"Free" if e['price_from']==0 else money(e['price_from']) if e['price_from'] else "TBA"}<small>{escape(e['price_text'])}</small></div>
<dl><dt>Date</dt><dd>Thursday 31 December {Y}</dd><dt>Time</dt><dd>{escape(e['time'])}</dd>
<dt>Where</dt><dd>{escape(e['venue'])}</dd><dt>At midnight</dt><dd>🎆 {escape(e['fireworks'])}</dd><dt>Age</dt><dd>{escape(e['age'])}</dd></dl>
<a class="btn btn-primary" style="width:100%;justify-content:center" href="{e['url']}" target="_blank" rel="noopener sponsored">Book with the venue →</a>
<div style="margin-top:20px">{countdown(mini=True)}</div>
</aside>
</div></section>
<section class="alt"><div class="wrap"><div class="section-head"><h2>You might also like</h2></div>
<div class="grid">{''.join(card(x, i) for i, x in enumerate(related))}</div></div></section>
{list_band()}"""
    return layout(
        path,
        (f"{e['name']} {Y}" if "NYE" in e["name"] or "New Year" in e["name"] else f"{e['name']} NYE {Y}")
        + f" – {e['suburb']} | NYE in Manchester",
        f"{e['name']} New Year's Eve {Y} in {e['suburb']}, Manchester: {e['price_text']}. {e['blurb']}"[:300],
        body, og_type="article", active="/#directory",
        schema=[schema, breadcrumbs(("Home", "/"), ("NYE events", "/#directory"), (e["name"], path))],
    )


def page_fireworks():
    vp = [e for e in EVENTS if "free" in e["categories"] or "rooftop" in e["categories"]]
    faq = [FAQ[0], FAQ[1], FAQ[4], FAQ[6], FAQ[8]]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">NYE {Y} · Fireworks &amp; where to watch</span>
<h1>Manchester fireworks on New Year's Eve {Y}</h1>
<p class="lead">Manchester City Council has put on free midnight fireworks every New Year's Eve since 2023: at Castlefield Bowl for NYE 2023, then at St Peter's Square for NYE 2024 and NYE 2025. Here's what happened last year, what we know about {Y}, and the best places to be at midnight.</p></div></section>
<section><div class="wrap prose">
<h2>Is there a Manchester fireworks display for NYE {Y}?</h2>
<p><b>Not confirmed yet.</b> Manchester City Council announced the 2025 plans in December 2025, so the {Y} details may not appear until late in the year. We'll update this page as soon as they're published.</p>
<h2>What happened on NYE 2025</h2>
<ul>
<li><b>St Peter's Square:</b> a free, alcohol-free, family-friendly countdown from 10pm, hosted by BBC Radio Manchester with a live DJ. An eight-minute fireworks and laser show launched from the roof of Central Library at midnight, with confetti cannons and a soundtrack of Manchester classics. Standing only, with bag searches, and entry stopped once the square was full.</li>
<li><b>Albert Square:</b> open from 10am to 12:30am with the UK's biggest mobile Ferris wheel, fairground rides, food, drink and craft stalls. Free to enter, with rides charged.</li>
<li><b>More than 20,000 people</b> celebrated across the two squares, according to the council.</li>
<li>There was <b>no direct walk-through</b> between the two squares, and getting into one did not guarantee entry to the other.</li>
</ul>
<p>Source: <a href="https://www.manchester.gov.uk/info/500357/christmas_in_manchester/9086/new_years_eve_in_manchester" target="_blank" rel="noopener">Manchester City Council</a>.</p>
</div></section>
<section class="alt"><div class="wrap">
<div class="section-head"><h2>Where to see in the new year</h2><p>Free squares in the city centre and ticketed skyline bars high above them.</p></div>
{vantage_table()}
</div></section>
{directory(vp, "Free events and skyline bars for midnight", "The free squares, plus ticketed rooftop and high-rise bars with views over the city at midnight.", show_filters=False)}
<section class="alt"><div class="wrap prose">
<h2>Tips for the city centre squares</h2>
<p><b>Arrive early.</b> St Peter's Square is standing only and closes once it's full.</p>
<p><b>Pack light.</b> In 2025 bags had to be A4 size or smaller, glass was banned and only guide dogs were allowed in St Peter's Square.</p>
<p><b>Accessibility.</b> In 2025 there was an accessible viewing area on the Metrolink platform (first come, first served), accessible toilets, and limited accessible parking on Dickinson Street and George Street.</p>
<p><b>Trams.</b> In 2025 no trams ran through St Peter's Square after 9pm. See <a href="/plan-your-night/#transport">getting home</a>.</p>
<h2>What to bring</h2>
<ul><li>Warm layers, a hat and gloves</li><li>A waterproof: rain is common in late December</li><li>Charged phone and a power bank</li><li>Ear defenders for small children</li><li>A small bag only, and no glass</li></ul>
</div></section>
<section id="faq"><div class="wrap"><div class="section-head"><h2>Fireworks FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>
{list_band()}"""
    return layout(
        "/manchester-fireworks-new-years-eve/",
        f"Manchester Fireworks New Year's Eve {Y}: St Peter's Square & Where to Watch | NYE in Manchester",
        f"Are there fireworks in Manchester on New Year's Eve {Y}? What happened at St Peter's Square in 2025, what's confirmed for {Y}, and the best free and skyline spots at midnight.",
        body, schema=[faq_schema(faq), item_list(vp, "Free events and skyline bars for midnight in Manchester"),
                      breadcrumbs(("Home", "/"), ("Fireworks", "/manchester-fireworks-new-years-eve/"))],
    )


def page_plan():
    faq = [FAQ[1], FAQ[5], FAQ[6], FAQ[8]]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">Planning guide</span>
<h1>Plan your Manchester NYE {Y}</h1>
<p class="lead">The run sheet for the night, trams, trains, buses and taxis, road closures, weather, accessibility and staying safe.</p>
{countdown(mini=True)}</div></section>
<section><div class="wrap two" style="align-items:start">
<div><h2>The night's schedule</h2><p class="muted">Times are based on the 2025 city events. Manchester City Council and TfGM confirm the {Y} plans in December.</p></div>
{timeline_html()}
</div></section>
<section class="alt" id="transport"><div class="wrap prose">
<h2>Getting there and getting home</h2>
<p><b>Metrolink trams.</b> In 2025 trams ran every 12 minutes on New Year's Eve and the last trams left the city centre at about 1am. No trams ran through St Peter's Square after 9pm while the event was on. A planned tram strike on 31 December 2025 was called off after a deal was agreed, but check for any industrial action before you travel.</p>
<p><b>Bee Network buses.</b> In 2025 buses ran a Saturday timetable on New Year's Eve, with most routes running to their normal finishing times and some extra late journeys.</p>
<p><b>Trains.</b> Late trains from Piccadilly, Victoria, Oxford Road and Deansgate are limited on New Year's Eve and there are usually no overnight services. Check your last train on National Rail Enquiries before you head out.</p>
<p><b>Taxis.</b> Demand peaks after midnight and after 4am when the clubs close. Use licensed black cabs from official ranks or book a licensed private hire car in advance. In 2025 the Peter Street rank outside The Midland was closed for the event.</p>
<ul><li>Plan your journey on <a href="https://tfgm.com" rel="noopener" target="_blank">tfgm.com</a> and check the special NYE timetables in December.</li>
<li>Have a back-up stop in mind. Walking to Deansgate-Castlefield, Market Street or Piccadilly Gardens can be quicker than queuing.</li>
<li>Staying out past 1am? Book a taxi, a hotel room or a late club ticket rather than relying on the last tram.</li></ul>
<h2 id="roads">Road closures &amp; parking</h2>
<p>In 2025 roads around St Peter's Square, Peter Street and Oxford Street closed from about 1pm on 31 December until about 2am on 1 January, with parking suspended on several city centre streets from 27 December. Driving into the centre is not recommended. If you must drive, park outside the closure area and finish the trip on foot or by tram.</p>
<h2 id="weather">Weather</h2>
<p>Expect cold, dark and often wet weather. The sun sets at around 4pm on 31 December, and nights in late December are usually only a few degrees above freezing. Pack a waterproof and warm layers, especially for outdoor events and taxi queues.</p>
<h2 id="accessibility">Accessibility</h2>
<p>In 2025 St Peter's Square had an accessible viewing area on the Metrolink platform, accessible toilets and limited accessible parking on Dickinson Street and George Street. Spaces were limited and first come, first served. Many venues in our directory have step-free access, but contact the venue to confirm.</p>
<h2>Safety &amp; wellbeing</h2>
<ul><li>Agree on a meeting point with your group.</li><li>Keep your phone charged and know your route home.</li><li>Follow police and staff directions. The squares close when full.</li><li>Look after your mates, drink water and pace yourself.</li><li>In an emergency call 999. For non-emergencies call 101.</li></ul>
</div></section>
<section id="faq"><div class="wrap"><div class="section-head"><h2>Planning FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>
{list_band()}"""
    return layout(
        "/plan-your-night/",
        f"Manchester NYE {Y} Planning Guide: Trams, Transport & Timings | NYE in Manchester",
        f"Manchester New Year's Eve {Y} planning guide: the schedule for the night, Metrolink trams, Bee Network buses, trains and taxis, road closures, weather, accessibility and safety.",
        body, schema=[faq_schema(faq), breadcrumbs(("Home", "/"), ("Plan your night", "/plan-your-night/"))],
    )


def page_list():
    p = P
    has_pay = "YOUR_" not in CONFIG["payment_link"]
    form_sub = (f"Fill this in, then pay £{p} securely. We'll publish your page and email you the link." if has_pay
                else f"Fill this in and we'll email you a £{p} invoice within one business day. Your page goes live once it's paid.")
    submit_label = f"Continue to payment: £{p} →" if has_pay else "Send my listing request →"
    cats = "".join(f'<option value="{k}">{v}</option>' for k, v in CATEGORY_LABELS.items() if k not in ("budget", "free"))
    faq = [
        (f"What do I get for £{p}?", "A dedicated event page built for search, with Google Event structured data. You also get a listing in our main directory and the matching category pages (dinners, parties, club nights, family), a direct link to your own booking page, and edits until 31 December."),
        ("Why should I list now rather than in December?", f"Search interest in New Year's Eve in Manchester builds from October and peaks in the final weeks of December. Listing early means your page is live and indexed by Google for the whole season, not just the last-minute rush. New pages can take days or weeks to rank, so the earlier you're in, the more of the season you capture. It's the same £{p} whenever you list."),
        ("Do you take commission on bookings?", "No. Guests book directly with you through your own link, and you keep 100% of every ticket."),
        ("Is VAT included?", f"The £{p} price is the total you pay. We'll send a receipt or invoice with your listing confirmation."),
        ("How long does my listing stay live?", f"Your listing stays live until New Year's Day {NY}, then rolls into our archive. Previous listers get first right to renew for next year."),
        ("How fast will my listing go live?", "Usually within one business day of payment. We'll email you the link."),
        ("Can I update prices or details?", "Yes. Email us any changes (sold-out tiers, price releases, new acts) and we'll update your page."),
    ]
    body = f"""
<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}
<div class="wrap"><span class="eyebrow">For venues, promoters &amp; restaurants</span>
<h1>List your New Year's Eve event</h1>
<p class="lead">October, November and December are when Manchester searches for its New Year's Eve plans. Put your NYE {Y} event in front of people typing "new years eve Manchester", "NYE Manchester", "new years eve dinner Manchester" and "Manchester NYE parties" while they're choosing where to spend the night.</p>
{countdown(mini=True)}
<p class="cd-note" style="margin-top:0">left to sell. The NYE search season is on now.</p>
<div class="cta-row"><a class="btn btn-primary" href="#form">List my event: £{p}</a><a class="btn btn-ghost" href="#season">Why now?</a></div></div></section>
{season_section(p)}
<section><div class="wrap two" style="align-items:start">
<div>
<h2>Why list with <span class="grad">NYE in Manchester</span>?</h2>
<ul class="ticks">
<li><b>High-intent visitors.</b> People only visit a NYE guide when they're about to book.</li>
<li><b>Your own SEO page.</b> Each event gets a dedicated page with Google Event schema, which can make it eligible for event rich results.</li>
<li><b>Listed where people browse.</b> You appear in the main directory plus every matching category: dinners, parties, club nights and family.</li>
<li><b>Zero commission.</b> Guests click straight through to your booking page.</li>
<li><b>Updates until NYE.</b> Change prices, add tiers or mark sold-out tiers whenever you like.</li>
<li><b>Our name is the search.</b> NYE in Manchester is built around the exact phrases people type into Google, so every page targets them.</li>
<li><b>Countdown traffic.</b> Interest builds from October and peaks in December, right when you're selling.</li>
</ul>
</div>
<div class="pricing">
<span class="eyebrow">NYE {Y} listing</span>
<div class="amount"><sup>£</sup>{p}</div>
<p class="muted">GBP · one-off · no commission</p>
<ul class="ticks">
<li>Dedicated event page + Google Event schema</li>
<li>Directory &amp; category page placement</li>
<li>Direct "Book" button to your site</li>
<li>Unlimited edits until 31 Dec {Y}</li>
<li>Live within 1 business day</li>
</ul>
<a class="btn btn-primary" href="#form" style="width:100%;justify-content:center">List my event →</a>
</div>
</div></section>
<section class="alt" id="form"><div class="wrap" style="max-width:860px">
<div class="section-head"><h2>Your event details</h2><p>{form_sub}</p></div>
<form class="listing panel" data-endpoint="{CONFIG['form_endpoint']}" data-payment="{CONFIG['payment_link']}" data-email="{CONFIG['contact_email']}">
<div><label for="f-name">Event name *</label><input id="f-name" name="event_name" required></div>
<div><label for="f-venue">Venue *</label><input id="f-venue" name="venue" required></div>
<div><label for="f-suburb">Area / neighbourhood *</label><input id="f-suburb" name="area" required placeholder="e.g. Spinningfields"></div>
<div><label for="f-cat">Type *</label><select id="f-cat" name="category" required>{cats}</select></div>
<div><label for="f-price">Price from (£ per person)</label><input id="f-price" name="price_from" inputmode="decimal" placeholder="e.g. 45"></div>
<div><label for="f-time">Times</label><input id="f-time" name="times" placeholder="e.g. 8pm – 3am"></div>
<div><label for="f-fw">At midnight</label><select id="f-fw" name="midnight"><option>Midnight countdown</option><option>Skyline views at midnight</option><option>Daytime countdown</option><option>Early evening, finishes before midnight</option></select></div>
<div><label for="f-age">Age</label><select id="f-age" name="age"><option>18+</option><option>21+</option><option>All ages</option><option>Family-friendly</option></select></div>
<div class="full"><label for="f-url">Booking URL *</label><input id="f-url" name="booking_url" type="url" required placeholder="https://"></div>
<div class="full"><label for="f-desc">Description &amp; inclusions *</label><textarea id="f-desc" name="description" required placeholder="What makes your night special? Food, drinks, DJs, views…"></textarea></div>
<div><label for="f-contact">Contact name *</label><input id="f-contact" name="contact_name" required></div>
<div><label for="f-email">Email *</label><input id="f-email" name="email" type="email" required></div>
<div><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel"></div>
<div><label for="f-company">Company name</label><input id="f-company" name="company"></div>
<input type="hidden" name="_subject" value="New NYE in Manchester listing request (£{p})">
<input type="hidden" name="_template" value="table"><input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
<div class="full"><button class="btn btn-primary" type="submit">{submit_label}</button>
<p class="form-status muted" aria-live="polite" style="margin:12px 0 0"></p></div>
</form>
</div></section>
<section><div class="wrap"><div class="section-head"><h2>Listing FAQ</h2></div><div class="faq">{faq_html(faq)}</div></div></section>"""
    service = {
        "@context": "https://schema.org", "@type": "Service", "name": f"NYE {Y} event listing",
        "provider": {"@type": "Organization", "name": CONFIG["site_name"], "url": URL + "/"},
        "areaServed": "Greater Manchester, England",
        "offers": {"@type": "Offer", "price": p, "priceCurrency": CONFIG["currency"], "url": URL + "/list-your-event/"},
    }
    return layout(
        "/list-your-event/",
        f"List Your New Year's Eve Event in Manchester – £{p} | NYE in Manchester",
        f"Promote your Manchester New Year's Eve {Y} party, club night or dinner. £{p} flat fee, no commission: a dedicated SEO event page, directory placement and a direct booking link.",
        body, schema=[service, faq_schema(faq), breadcrumbs(("Home", "/"), ("List your event", "/list-your-event/"))],
    )


def page_404():
    body = f"""<section class="hero small"><canvas id="fw" aria-hidden="true"></canvas>{SKYLINE}<div class="wrap">
<h1>This page fizzled out</h1><p class="lead">The page you're after isn't here, but the countdown still is.</p>{countdown()}
<div class="cta-row"><a class="btn btn-primary" href="/">Back to all NYE events</a></div></div></section>"""
    return layout("/404.html", "Page not found | NYE in Manchester", "Page not found.", body).replace(
        'content="index,follow', 'content="noindex,follow')


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#07061a"/><g stroke-linecap="round" stroke-width="4"><path d="M32 32 32 8" stroke="#ffc94d"/><path d="M32 32 53 20" stroke="#ff4fa3"/><path d="M32 32 53 44" stroke="#8b5cff"/><path d="M32 32 32 56" stroke="#41e3ff"/><path d="M32 32 11 44" stroke="#ffc94d"/><path d="M32 32 11 20" stroke="#ff4fa3"/></g><circle cx="32" cy="32" r="5" fill="#fff"/></svg>"""

OG_HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700&family=Playfair+Display:wght@800&display=swap" rel="stylesheet">
<style>body{{margin:0;width:1200px;height:630px;background:radial-gradient(ellipse at 50% 120%,#2a1a6b,transparent 60%),radial-gradient(ellipse at 85% 0%,#3a0f4d,transparent 55%),#07061a;color:#fff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.t{{position:absolute;left:70px;top:90px;right:70px}}h1{{font-family:'Playfair Display',serif;font-size:84px;margin:0;line-height:1}}
.g{{background:linear-gradient(120deg,#ffc94d,#ff4fa3 50%,#8b5cff);-webkit-background-clip:text;color:transparent}}
p{{font-size:34px;color:#cfc9ff;margin:24px 0 0}}.b{{display:inline-block;margin-top:30px;padding:12px 26px;border-radius:99px;background:linear-gradient(120deg,#ffc94d,#ff4fa3);color:#14062b;font-weight:700;font-size:26px}}
.s{{position:absolute;bottom:0;left:0;width:100%}}.dot{{position:absolute;border-radius:50%}}</style></head><body>
<div class="t"><h1>NYE <span class="g">in Manchester</span></h1><p>Parties · Club nights · Dinners · Fireworks<br>31 December {Y} · Greater Manchester</p><span class="b">Countdown to {NY} →</span></div>
{SKYLINE.replace('class="skyline"', 'class="s"')}
<script>for(let k=0;k<4;k++){{const cx=880+k*95,cy=270+(k%2)*90,c=['#ffc94d','#ff4fa3','#8b5cff','#41e3ff'][k];for(let i=0;i<48;i++){{const a=i/48*6.283,r=30+Math.random()*40,d=document.createElement('div');d.className='dot';d.style.cssText=`left:${{cx+Math.cos(a)*r}}px;top:${{cy+Math.sin(a)*r}}px;width:4px;height:4px;background:${{c}};box-shadow:0 0 8px ${{c}}`;document.body.appendChild(d)}}}}</script>
</body></html>"""


def build():
    if OUT.exists():
        og_keep = (OUT / "og.png").read_bytes() if (OUT / "og.png").exists() else None
        shutil.rmtree(OUT)
    else:
        og_keep = None
    OUT.mkdir()
    pages = {"/": page_home(), "/manchester-fireworks-new-years-eve/": page_fireworks(),
             "/plan-your-night/": page_plan(), "/list-your-event/": page_list()}
    for c in CATEGORY_PAGES:
        pages[c["path"]] = page_category(c)
    for e in EVENTS:
        pages[f"/events/{e['slug']}/"] = page_event(e)
    for path, html in pages.items():
        f = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html)
    (OUT / "404.html").write_text(page_404())
    shutil.copy(ROOT / "src" / "style.css", OUT / "style.css")
    shutil.copy(ROOT / "src" / "main.js", OUT / "main.js")
    (OUT / "favicon.svg").write_text(FAVICON)
    (OUT / "og.html").write_text(OG_HTML)
    if og_keep:
        (OUT / "og.png").write_bytes(og_keep)
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /og.html\n\nSitemap: {URL}/sitemap.xml\n")
    prio = lambda p: "1.0" if p == "/" else "0.6" if p.startswith("/events/") else "0.8"
    sm = "".join(
        f"<url><loc>{URL}{p}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{prio(p)}</priority></url>\n"
        for p in pages
    )
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n')
    print(f"Built {len(pages)} pages into {OUT}")


if __name__ == "__main__":
    build()
