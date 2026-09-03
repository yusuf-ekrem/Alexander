#!/usr/bin/env python3
"""Static site generator for alexandercaldwell.com.

No third-party dependencies. Run `python3 build.py` from the repository root.

Inputs
  content/posts/*.html   one file per article: a small metadata header, a line
                         containing only `---`, then the article body as HTML.
  assets/                copied as-is (style.css, favicon.svg, photos, og-image.jpg).

Outputs (written next to this file)
  index.html, 404.html, sitemap.xml, robots.txt
  about/, blog/, terms/, privacy/            -> index.html in each
  <category>/                                -> category listing
  <category>/<slug>/                         -> article page
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POSTS_DIR = ROOT / "content" / "posts"

SITE_URL = "https://alexandercaldwell.com"
SITE_NAME = "Alexander Caldwell"
TAGLINE = "Payroll & personal finance insights"
SITE_DESCRIPTION = (
    "Plain-English guides on pay stubs, payroll, taxes, paychecks, W-2 and 1099 forms "
    "from payroll expert Alexander Caldwell."
)
AUTHOR_NAME = "Alexander Caldwell"
AUTHOR_TITLE = "Financial Expert"
AUTHOR_PHOTO = "/assets/alexander-caldwell.jpg"       # 400x400
AUTHOR_PHOTO_SM = "/assets/alexander-caldwell-sm.jpg" # 192x192, for small avatars
OG_IMAGE = "/assets/og-image.jpg"                     # 1200x630
FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
    "&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap"
)
CREDENTIALS = [
    "12+ years in payroll management",
    "B.S. Finance, University of California, Berkeley",
    "Payroll and tax compliance for businesses of all sizes",
    "Payroll solutions specialist at Online Pay Stub",
]
TRUST = [
    ("12+", "years of payroll experience"),
    ("UC Berkeley", "bachelor's degree in finance"),
    ("7", "topic areas, plain-English guidance"),
    ("All sizes", "of businesses served, startups to enterprises"),
]
AUTHOR_BIO_SHORT = (
    "Financial expert specializing in payroll management, with over 12 years of "
    "experience helping businesses and employees keep their financial records accurate."
)
AUTHOR_BIO = [
    "Alexander Caldwell is a financial expert specializing in payroll management, with "
    "over 12 years of experience in the industry. He earned his bachelor's degree in "
    "finance from the University of California, Berkeley.",
    "Throughout his career, Alexander has worked with businesses of all sizes, helping "
    "them streamline payroll processes and ensure compliance with tax regulations.",
    "At Online Pay Stub, he is dedicated to providing accurate and reliable payroll "
    "solutions, making it easier for employees and businesses to manage their financial "
    "records efficiently.",
]

# Menu order is the order of this list.
CATEGORIES = [
    ("paystubs", "Paystubs", "How to read, check and keep your pay stubs."),
    ("payroll", "Payroll", "Running payroll correctly, on time and in compliance."),
    ("tax", "Tax", "Withholding, filing and the taxes that touch your paycheck."),
    ("finance", "Finance", "Budgeting, saving and planning around your income."),
    ("paycheck", "Paycheck", "Gross pay, net pay and everything in between."),
    ("w-2-form", "W-2 Form", "Understanding and using your annual wage statement."),
    ("1099-forms", "1099 Forms", "Independent contractor income and the forms behind it."),
]
CATEGORY_BY_SLUG = {slug: (name, desc) for slug, name, desc in CATEGORIES}

SOCIAL = [
    ("X", "https://x.com/alexandercaldw"),
    ("Medium", "https://medium.com/@alexander-caldwell"),
    ("TikTok", "https://www.tiktok.com/@alexandercaldwellops"),
    ("Tumblr", "https://www.tumblr.com/blog/alexandercaldwell"),
    ("Pinterest", "https://www.pinterest.com/alexandercaldwellfinance/"),
]

# Slug -> inline SVG icon (24x24 viewBox, currentColor).
SOCIAL_ICONS = {
    "X": '<path d="M18.9 2H22l-7.2 8.2L23 22h-6.6l-5.2-6.8L5.3 22H2.1l7.7-8.8L1.5 2h6.8l4.7 6.2L18.9 2Zm-1.2 18h1.8L7.2 3.9H5.3L17.7 20Z"/>',
    "Medium": '<path d="M13.5 12a6.4 6.4 0 1 1-12.8 0 6.4 6.4 0 0 1 12.8 0Zm7 0c0 3.3-1.4 6-3.2 6s-3.2-2.7-3.2-6 1.4-6 3.2-6 3.2 2.7 3.2 6Zm2.8 0c0 3-.5 5.4-1.1 5.4S21 15 21 12s.5-5.4 1.1-5.4 1.2 2.4 1.2 5.4Z"/>',
    "TikTok": '<path d="M16.6 5.8A4.3 4.3 0 0 1 15.5 3h-3.2v13.1a2.7 2.7 0 1 1-2.7-2.7c.3 0 .6 0 .8.1V10.2a6 6 0 1 0 5.1 5.9V9.6a7.5 7.5 0 0 0 4.4 1.4V7.8a4.4 4.4 0 0 1-3.3-2Z"/>',
    "Tumblr": '<path d="M14.6 21c-3.2 0-5-2-5-4.8v-5.6H7.4V7.7c2.5-.8 3.3-2.9 3.5-4.7h2.9v4.4h3.4v3.2h-3.4v4.9c0 1.3.7 1.9 1.8 1.9.6 0 1.3-.2 1.8-.4l.9 2.9c-1 .6-2.5 1.1-3.7 1.1Z"/>',
    "Pinterest": '<path d="M12 2a10 10 0 0 0-3.6 19.3c-.1-.8-.2-2 0-2.9l1.2-5s-.3-.6-.3-1.5c0-1.4.8-2.4 1.8-2.4.9 0 1.3.6 1.3 1.4 0 .9-.5 2.1-.8 3.3-.2 1 .5 1.8 1.5 1.8 1.8 0 3.1-1.9 3.1-4.6 0-2.4-1.7-4-4.2-4-2.8 0-4.5 2.1-4.5 4.3 0 .9.3 1.8.7 2.3.1.1.1.2.1.3l-.3 1.1c0 .2-.1.2-.3.1-1.2-.6-2-2.4-2-3.8 0-3.1 2.3-6 6.5-6 3.4 0 6.1 2.4 6.1 5.7 0 3.4-2.1 6.1-5.1 6.1-1 0-1.9-.5-2.3-1.1l-.6 2.4c-.2.9-.8 2-1.2 2.6A10 10 0 1 0 12 2Z"/>',
}

TODAY = dt.date.today()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def esc(text: str) -> str:
    return html.escape(text, quote=True)


def url(path: str) -> str:
    """Absolute URL for a site-relative path such as '/tax/'."""
    return SITE_URL + path


def strip_tags(markup: str) -> str:
    return re.sub(r"<[^>]+>", " ", markup)


def reading_time(markup: str) -> int:
    words = len(strip_tags(markup).split())
    return max(1, round(words / 220))


def fmt_date(d: dt.date) -> str:
    return d.strftime("%B %-d, %Y")


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", strip_tags(text).lower()).strip("-")
    return text or "section"


def add_heading_ids(markup: str) -> tuple[str, list[tuple[str, str]]]:
    """Give every <h2> an id and return (markup, [(id, text), ...])."""
    headings: list[tuple[str, str]] = []
    used: set[str] = set()

    def repl(m: re.Match) -> str:
        text = m.group(2)
        base = slugify(text)
        hid, n = base, 2
        while hid in used:
            hid, n = f"{base}-{n}", n + 1
        used.add(hid)
        headings.append((hid, html.unescape(strip_tags(text)).strip()))
        return f'<h2 id="{hid}"{m.group(1)}>{text}</h2>'

    return re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, markup, flags=re.S), headings


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Content loading
# --------------------------------------------------------------------------- #

class Post:
    def __init__(self, meta: dict, body: str, source: Path):
        missing = [k for k in ("title", "slug", "category", "date", "description") if k not in meta]
        if missing:
            raise SystemExit(f"{source.name}: missing metadata {', '.join(missing)}")
        if meta["category"] not in CATEGORY_BY_SLUG:
            raise SystemExit(f"{source.name}: unknown category '{meta['category']}'")
        self.title = meta["title"]
        self.slug = meta["slug"]
        self.category = meta["category"]
        self.date = dt.date.fromisoformat(meta["date"])
        self.description = meta["description"]
        self.body = body.strip()
        self.minutes = reading_time(self.body)

    @property
    def category_name(self) -> str:
        return CATEGORY_BY_SLUG[self.category][0]

    @property
    def path(self) -> str:
        return f"/{self.category}/{self.slug}/"


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for source in sorted(POSTS_DIR.glob("*.html")):
        raw = source.read_text(encoding="utf-8")
        if "\n---\n" not in raw:
            raise SystemExit(f"{source.name}: metadata header must end with a '---' line")
        head, body = raw.split("\n---\n", 1)
        meta: dict[str, str] = {}
        for line in head.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip().lower()] = value.strip()
        posts.append(Post(meta, body, source))
    seen: set[str] = set()
    for p in posts:
        if p.path in seen:
            raise SystemExit(f"duplicate post path {p.path}")
        seen.add(p.path)
    posts.sort(key=lambda p: (p.date, p.title), reverse=True)
    return posts


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #

def nav_links(current: str) -> str:
    items = [("/", "Home"), ("/about/", "About")]
    items += [(f"/{slug}/", name) for slug, name, _ in CATEGORIES]
    out = []
    for href, label in items:
        active = ' aria-current="page"' if href == current else ""
        out.append(f'<a href="{href}"{active}>{esc(label)}</a>')
    return "\n        ".join(out)


def social_links(with_icons: bool = True) -> str:
    out = []
    for name, href in SOCIAL:
        icon = (
            f'<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="currentColor">'
            f"{SOCIAL_ICONS[name]}</svg>"
            if with_icons
            else ""
        )
        out.append(
            f'<a href="{href}" rel="me noopener" target="_blank" title="{esc(name)}">'
            f'{icon}<span>{esc(name)}</span></a>'
        )
    return "\n          ".join(out)


def brand(extra_class: str = "") -> str:
    cls = f"brand {extra_class}".strip()
    return f"""<a href="/" class="{cls}" aria-label="{esc(SITE_NAME)} home">
        <span class="brand-mark" aria-hidden="true">AC</span>
        <span class="brand-text">
          <span class="brand-name">{esc(SITE_NAME)}</span>
          <span class="brand-tag">{esc(TAGLINE)}</span>
        </span>
      </a>"""


def header(current: str) -> str:
    return f"""  <a class="skip-link" href="#main">Skip to content</a>
  <div class="topbar">
    <div class="container topbar-inner">
      <span class="topbar-tagline">Independent guidance on pay stubs, payroll and paycheck taxes</span>
      <div class="topbar-social" aria-label="Social profiles">
          {social_links()}
      </div>
    </div>
  </div>
  <header class="site-header">
    <div class="container header-inner">
      {brand()}
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">
        <span class="nav-toggle-bar"></span>
        <span class="sr-only">Menu</span>
      </button>
      <nav id="primary-nav" class="nav" aria-label="Primary">
        {nav_links(current)}
      </nav>
    </div>
  </header>
"""


def footer() -> str:
    cat_links = "\n            ".join(
        f'<li><a href="/{slug}/">{esc(name)}</a></li>' for slug, name, _ in CATEGORIES
    )
    return f"""  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-about">
          {brand("brand-footer")}
          <p>{esc(AUTHOR_BIO_SHORT)}</p>
          <p class="small">Educational content only. Nothing on this site is legal, tax or financial advice; confirm current rules with the IRS or a qualified professional.</p>
        </div>
        <nav class="footer-col" aria-label="Footer">
          <p class="footer-heading">Site</p>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/about/">About</a></li>
            <li><a href="/blog/">All articles</a></li>
            <li><a href="/terms/">ToS</a></li>
            <li><a href="/privacy/">Privacy</a></li>
          </ul>
        </nav>
        <nav class="footer-col" aria-label="Topics">
          <p class="footer-heading">Topics</p>
          <ul>
            {cat_links}
          </ul>
        </nav>
        <div class="footer-col footer-social">
          <p class="footer-heading">Follow</p>
          <ul>
            {"".join(f'<li>{a}</li>' for a in social_links().split(chr(10)))}
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; {TODAY.year} {esc(SITE_NAME)}. All rights reserved.</span>
        <span><a href="/terms/">Terms of Service</a> &middot; <a href="/privacy/">Privacy Policy</a></span>
      </div>
    </div>
  </footer>
  <script>
    (function () {{
      var btn = document.querySelector(".nav-toggle");
      var nav = document.getElementById("primary-nav");
      if (!btn || !nav) return;
      btn.addEventListener("click", function () {{
        var open = nav.classList.toggle("is-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      }});
    }})();
  </script>
"""


def page(
    *,
    title: str,
    description: str,
    path: str,
    body: str,
    current: str = "",
    og_type: str = "website",
    jsonld: dict | None = None,
    noindex: bool = False,
    canonical: bool = True,
) -> str:
    full_title = SITE_NAME if path == "/" else f"{title} · {SITE_NAME}"
    robots = '\n  <meta name="robots" content="noindex">' if noindex else ""
    canon = f'\n  <link rel="canonical" href="{url(path)}">' if canonical else ""
    ld = ""
    if jsonld:
        ld = (
            '\n  <script type="application/ld+json">\n'
            + json.dumps(jsonld, indent=2, ensure_ascii=False)
            + "\n  </script>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(full_title)}</title>
  <meta name="description" content="{esc(description)}">{robots}{canon}
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS_URL}">
  <link rel="stylesheet" href="/assets/style.css">
  <meta property="og:type" content="{og_type}">
  <meta property="og:url" content="{url(path)}">
  <meta property="og:title" content="{esc(full_title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:site_name" content="{esc(SITE_NAME)}">
  <meta property="og:image" content="{url(OG_IMAGE)}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Portrait of {esc(AUTHOR_NAME)} with the site name and tagline">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{url(OG_IMAGE)}">
  <meta name="twitter:site" content="@alexandercaldw">
  <meta name="theme-color" content="#1b2532">{ld}
</head>
<body>
{header(current)}
  <main id="main" class="site-main">
{body}
  </main>
{footer()}</body>
</html>
"""


def person_ld() -> dict:
    return {
        "@type": "Person",
        "@id": url("/#person"),
        "name": AUTHOR_NAME,
        "jobTitle": AUTHOR_TITLE,
        "description": AUTHOR_BIO_SHORT,
        "url": url("/about/"),
        "image": url(AUTHOR_PHOTO),
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "University of California, Berkeley"},
        "worksFor": {"@type": "Organization", "name": "Online Pay Stub"},
        "sameAs": [href for _, href in SOCIAL],
    }


def website_ld() -> dict:
    return {
        "@type": "WebSite",
        "@id": url("/#website"),
        "url": url("/"),
        "name": SITE_NAME,
        "description": SITE_DESCRIPTION,
        "inLanguage": "en",
        "image": url(OG_IMAGE),
        "publisher": {"@id": url("/#person")},
    }


def graph(*nodes: dict) -> dict:
    return {"@context": "https://schema.org", "@graph": list(nodes)}


def breadcrumb_ld(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url(path)}
            for i, (name, path) in enumerate(items)
        ],
    }


# --------------------------------------------------------------------------- #
# Components
# --------------------------------------------------------------------------- #

def post_card(p: Post, heading: str = "h3") -> str:
    return f"""        <article class="card">
          <a class="card-category" href="/{p.category}/">{esc(p.category_name)}</a>
          <{heading} class="card-title"><a href="{p.path}">{esc(p.title)}</a></{heading}>
          <p class="card-excerpt">{esc(p.description)}</p>
          <div class="card-meta">
            <time datetime="{p.date.isoformat()}">{fmt_date(p.date)}</time>
            <span aria-hidden="true">&middot;</span>
            <span>{p.minutes} min read</span>
          </div>
        </article>"""


def post_grid(posts: list[Post], heading: str = "h3") -> str:
    if not posts:
        return '        <p class="muted">No articles yet. Check back soon.</p>'
    return '      <div class="card-grid">\n' + "\n".join(post_card(p, heading) for p in posts) + "\n      </div>"


def category_grid(posts: list[Post]) -> str:
    counts = {slug: 0 for slug, _, _ in CATEGORIES}
    for p in posts:
        counts[p.category] += 1
    tiles = []
    for slug, name, desc in CATEGORIES:
        n = counts[slug]
        label = f"{n} article" if n == 1 else f"{n} articles"
        tiles.append(
            f"""        <a class="category-tile" href="/{slug}/">
          <span class="category-index">{len(tiles) + 1:02d}</span>
          <span class="category-name">{esc(name)}</span>
          <span class="category-desc">{esc(desc)}</span>
          <span class="category-count">{label}</span>
        </a>"""
        )
    return '      <div class="category-grid">\n' + "\n".join(tiles) + "\n      </div>"


def author_box() -> str:
    return f"""      <aside class="author-box" aria-label="About the author">
        <img class="avatar" src="{AUTHOR_PHOTO_SM}" width="72" height="72" alt="Portrait of {esc(AUTHOR_NAME)}" loading="lazy">
        <div>
          <p class="author-name">{esc(AUTHOR_NAME)}</p>
          <p class="author-title">{esc(AUTHOR_TITLE)}</p>
          <p>{esc(AUTHOR_BIO_SHORT)} <a href="/about/">Read more about Alexander</a>.</p>
        </div>
      </aside>"""


def breadcrumbs(items: list[tuple[str, str]]) -> str:
    parts = []
    for i, (name, path) in enumerate(items):
        if i == len(items) - 1:
            parts.append(f'<li aria-current="page">{esc(name)}</li>')
        else:
            parts.append(f'<li><a href="{path}">{esc(name)}</a></li>')
    return '      <nav class="breadcrumbs" aria-label="Breadcrumb"><ol>' + "".join(parts) + "</ol></nav>"


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #

def build_home(posts: list[Post]) -> str:
    featured = posts[0] if posts else None
    side = posts[1:4]
    rest = posts[1:7]
    creds = "\n            ".join(f"<li>{esc(c)}</li>" for c in CREDENTIALS)
    trust = "\n        ".join(
        f'<div class="trust-item"><span class="trust-value">{esc(v)}</span><span class="trust-label">{esc(l)}</span></div>'
        for v, l in TRUST
    )
    featured_html = ""
    if featured:
        side_items = "\n            ".join(
            f"""<li>
              <a class="card-category" href="/{q.category}/">{esc(q.category_name)}</a>
              <a class="mini-title" href="{q.path}">{esc(q.title)}</a>
              <div class="card-meta"><time datetime="{q.date.isoformat()}">{fmt_date(q.date)}</time><span aria-hidden="true">&middot;</span><span>{q.minutes} min read</span></div>
            </li>"""
            for q in side
        )
        featured_html = f"""    <section class="section container">
      <div class="section-head">
        <h2>Featured</h2>
        <a href="/blog/" class="more">All articles &rarr;</a>
      </div>
      <div class="featured">
        <article class="featured-main">
          <a class="card-category" href="/{featured.category}/">{esc(featured.category_name)}</a>
          <h3><a href="{featured.path}">{esc(featured.title)}</a></h3>
          <p>{esc(featured.description)}</p>
          <div class="card-meta">
            <span>By {esc(AUTHOR_NAME)}</span>
            <span aria-hidden="true">&middot;</span>
            <time datetime="{featured.date.isoformat()}">{fmt_date(featured.date)}</time>
            <span aria-hidden="true">&middot;</span>
            <span>{featured.minutes} min read</span>
          </div>
          <div class="actions"><a href="{featured.path}" class="button">Read the article</a></div>
        </article>
        <aside class="featured-side">
          <h4>Recently published</h4>
          <ul class="mini-list">
            {side_items}
          </ul>
        </aside>
      </div>
    </section>
"""
    body = f"""    <section class="hero">
      <div class="container hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">{esc(TAGLINE)}</p>
          <h1>Clarity on every paycheck, pay stub and tax form.</h1>
          <p class="lead">Practical, plain-English guidance on payroll, withholding, W-2 and 1099 forms from a finance professional with more than a decade in payroll management.</p>
          <div class="actions">
            <a href="/blog/" class="button">Browse the articles</a>
            <a href="/about/" class="button secondary">About Alexander</a>
          </div>
        </div>
        <div class="hero-card">
          <div class="hero-card-top">
            <img class="avatar avatar-lg" src="{AUTHOR_PHOTO}" width="96" height="96" alt="Portrait of {esc(AUTHOR_NAME)}">
            <div>
              <p class="author-name">{esc(AUTHOR_NAME)}</p>
              <p class="author-title">{esc(AUTHOR_TITLE)}</p>
            </div>
          </div>
          <ul class="cred-list">
            {creds}
          </ul>
        </div>
      </div>
    </section>

    <section class="trust" aria-label="Credentials">
      <div class="container trust-inner">
        {trust}
      </div>
    </section>

{featured_html}
    <section class="section section-alt">
      <div class="container">
        <div class="section-head">
          <h2>Latest articles</h2>
          <a href="/blog/" class="more">View all &rarr;</a>
        </div>
{post_grid(rest)}
      </div>
    </section>

    <section class="section container">
      <div class="section-head">
        <h2>Browse by topic</h2>
      </div>
{category_grid(posts)}
    </section>
"""
    return page(
        title=SITE_NAME,
        description=SITE_DESCRIPTION,
        path="/",
        current="/",
        body=body,
        jsonld=graph(person_ld(), website_ld()),
    )


def build_about() -> str:
    paragraphs = "\n".join(f"        <p>{esc(p)}</p>" for p in AUTHOR_BIO)
    body = f"""    <div class="container narrow">
{breadcrumbs([("Home", "/"), ("About", "/about/")])}
      <article class="prose">
        <header class="page-head">
          <img class="avatar avatar-lg" src="{AUTHOR_PHOTO}" width="96" height="96" alt="Portrait of {esc(AUTHOR_NAME)}">
          <h1>{esc(AUTHOR_NAME)}</h1>
          <p class="lead">{esc(AUTHOR_TITLE)}</p>
        </header>
{paragraphs}
        <h2>What you will find here</h2>
        <p>This blog collects the questions Alexander hears most often from employees, freelancers and business owners, answered in plain English. Every article is organised under one of seven topics:</p>
        <ul>
{chr(10).join(f'          <li><a href="/{slug}/">{esc(name)}</a> &mdash; {esc(desc)}</li>' for slug, name, desc in CATEGORIES)}
        </ul>
        <h2>Follow Alexander</h2>
        <div class="social-list">
          {social_links()}
        </div>
        <p class="muted small">The content on this site is for general information only and is not legal, tax or financial advice. Always check current IRS guidance or speak with a qualified professional about your own situation.</p>
      </article>
    </div>
"""
    return page(
        title="About",
        description="About Alexander Caldwell, a financial expert specializing in payroll management with over 12 years of experience.",
        path="/about/",
        current="/about/",
        body=body,
        og_type="profile",
        jsonld=graph(person_ld(), breadcrumb_ld([("Home", "/"), ("About", "/about/")])),
    )


def build_blog(posts: list[Post]) -> str:
    body = f"""    <div class="container">
{breadcrumbs([("Home", "/"), ("Blog", "/blog/")])}
      <header class="page-head">
        <h1>All articles</h1>
        <p class="lead">Every guide on the site, newest first.</p>
      </header>
{post_grid(posts, "h2")}
    </div>
"""
    return page(
        title="Blog",
        description="All personal finance, payroll and paycheck articles by Alexander Caldwell.",
        path="/blog/",
        body=body,
        jsonld=graph(breadcrumb_ld([("Home", "/"), ("Blog", "/blog/")])),
    )


def build_category(slug: str, name: str, desc: str, posts: list[Post]) -> str:
    mine = [p for p in posts if p.category == slug]
    body = f"""    <div class="container">
{breadcrumbs([("Home", "/"), (name, f"/{slug}/")])}
      <header class="page-head">
        <p class="eyebrow">Category</p>
        <h1>{esc(name)}</h1>
        <p class="lead">{esc(desc)}</p>
      </header>
{post_grid(mine, "h2")}
    </div>
"""
    ld = graph(
        {
            "@type": "CollectionPage",
            "@id": url(f"/{slug}/"),
            "url": url(f"/{slug}/"),
            "name": name,
            "description": desc,
            "isPartOf": {"@id": url("/#website")},
        },
        breadcrumb_ld([("Home", "/"), (name, f"/{slug}/")]),
    )
    return page(
        title=name,
        description=f"{desc} Articles on {name.lower()} by Alexander Caldwell.",
        path=f"/{slug}/",
        current=f"/{slug}/",
        body=body,
        jsonld=ld,
    )


def build_post(p: Post, posts: list[Post]) -> str:
    related = [q for q in posts if q.category == p.category and q.path != p.path][:3]
    if len(related) < 3:
        related += [q for q in posts if q.category != p.category and q not in related][: 3 - len(related)]
    crumbs = [("Home", "/"), (p.category_name, f"/{p.category}/"), (p.title, p.path)]
    article_html, headings = add_heading_ids(p.body)
    toc = ""
    if len(headings) >= 3:
        items = "".join(f'<li><a href="#{hid}">{esc(text)}</a></li>' for hid, text in headings)
        toc = f"""        <nav class="toc" aria-label="In this article">
          <p class="toc-title">In this article</p>
          <ol>{items}</ol>
        </nav>
"""
    body = f"""    <div class="container narrow">
{breadcrumbs(crumbs)}
      <article class="prose post">
        <header class="post-head">
          <a class="card-category" href="/{p.category}/">{esc(p.category_name)}</a>
          <h1>{esc(p.title)}</h1>
          <p class="lead">{esc(p.description)}</p>
          <div class="post-meta">
            <img class="avatar avatar-sm" src="{AUTHOR_PHOTO_SM}" width="36" height="36" alt="">
            <span>By <a href="/about/">{esc(AUTHOR_NAME)}</a></span>
            <span aria-hidden="true">&middot;</span>
            <time datetime="{p.date.isoformat()}">{fmt_date(p.date)}</time>
            <span aria-hidden="true">&middot;</span>
            <span>{p.minutes} min read</span>
          </div>
        </header>
{toc}{article_html}
      </article>
{author_box()}
    </div>
    <section class="section section-alt">
      <div class="container">
        <div class="section-head"><h2>Keep reading</h2></div>
{post_grid(related)}
      </div>
    </section>
"""
    ld = graph(
        {
            "@type": "BlogPosting",
            "@id": url(p.path),
            "mainEntityOfPage": url(p.path),
            "url": url(p.path),
            "headline": p.title,
            "description": p.description,
            "articleSection": p.category_name,
            "datePublished": p.date.isoformat(),
            "dateModified": p.date.isoformat(),
            "inLanguage": "en",
            "author": {"@id": url("/#person")},
            "publisher": {"@id": url("/#person")},
            "isPartOf": {"@id": url("/#website")},
            "wordCount": len(strip_tags(p.body).split()),
        },
        person_ld(),
        breadcrumb_ld(crumbs),
    )
    return page(
        title=p.title,
        description=p.description,
        path=p.path,
        current=f"/{p.category}/",
        body=body,
        og_type="article",
        jsonld=ld,
    )


LEGAL_UPDATED = dt.date(2026, 9, 2)


def build_terms() -> str:
    body = f"""    <div class="container narrow">
{breadcrumbs([("Home", "/"), ("Terms of Service", "/terms/")])}
      <article class="prose">
        <header class="page-head">
          <h1>Terms of Service</h1>
          <p class="muted">Last updated {fmt_date(LEGAL_UPDATED)}</p>
        </header>
        <p>Welcome to alexandercaldwell.com (the &ldquo;Site&rdquo;). By accessing or using the Site you agree to these Terms of Service. If you do not agree, please do not use the Site.</p>

        <h2>1. Informational purpose only</h2>
        <p>The Site publishes articles about personal finance, payroll, pay stubs, paychecks and tax forms. All content is provided for general educational purposes only. It is not legal, tax, accounting or financial advice, and it does not create a professional or advisory relationship of any kind. Tax rules change frequently and vary by jurisdiction; always confirm current requirements with the IRS, your state agency or a qualified professional before acting.</p>

        <h2>2. No guarantees</h2>
        <p>We work hard to keep articles accurate and up to date, but the Site is provided &ldquo;as is&rdquo; without warranties of any kind, express or implied. We do not guarantee that the content is complete, current or error-free, or that the Site will be available without interruption.</p>

        <h2>3. Intellectual property</h2>
        <p>Unless otherwise noted, all text, graphics and other material on the Site are owned by Alexander Caldwell and protected by copyright. You may read, share links to, and quote brief excerpts of articles with attribution. You may not republish full articles, scrape the Site, or use its content for commercial purposes without prior written permission.</p>

        <h2>4. Third-party links</h2>
        <p>Articles may link to external websites, including government resources and social media profiles. Those sites have their own terms and privacy practices, and we are not responsible for their content or availability.</p>

        <h2>5. Acceptable use</h2>
        <p>You agree not to use the Site in any way that is unlawful, that could damage or impair the Site, or that interferes with anyone else&rsquo;s use of it. Automated bulk access is not permitted except by search engine crawlers that respect our robots.txt.</p>

        <h2>6. Limitation of liability</h2>
        <p>To the fullest extent permitted by law, Alexander Caldwell shall not be liable for any direct, indirect, incidental or consequential damages arising out of your use of, or reliance on, the Site or its content.</p>

        <h2>7. Changes to these terms</h2>
        <p>We may update these Terms from time to time. The date at the top of this page shows when they were last revised. Continued use of the Site after a change means you accept the revised Terms.</p>

        <h2>8. Contact</h2>
        <p>Questions about these Terms can be sent through any of the social profiles listed in the footer.</p>
      </article>
    </div>
"""
    return page(
        title="Terms of Service",
        description="Terms of Service for alexandercaldwell.com.",
        path="/terms/",
        body=body,
        jsonld=graph(breadcrumb_ld([("Home", "/"), ("Terms of Service", "/terms/")])),
    )


def build_privacy() -> str:
    body = f"""    <div class="container narrow">
{breadcrumbs([("Home", "/"), ("Privacy Policy", "/privacy/")])}
      <article class="prose">
        <header class="page-head">
          <h1>Privacy Policy</h1>
          <p class="muted">Last updated {fmt_date(LEGAL_UPDATED)}</p>
        </header>
        <p>This Privacy Policy explains what information alexandercaldwell.com (the &ldquo;Site&rdquo;) collects and how it is used. The short version: the Site is a static blog, it does not ask you to create an account, and it does not sell personal information.</p>

        <h2>1. Information we collect</h2>
        <p>The Site does not have contact forms, comment sections or newsletter sign-ups, and it does not set its own tracking cookies. We therefore do not directly collect names, email addresses or other personal details from visitors.</p>
        <p>Like almost every website, the hosting provider that serves the Site may automatically record standard technical data in server logs, such as your IP address, browser type, the pages you request and the time of the request. This data is used only to operate and secure the Site and is not combined with other information to identify you.</p>

        <h2>2. Cookies and analytics</h2>
        <p>The Site itself does not use advertising or analytics cookies. If privacy-friendly, aggregate analytics are added in the future, this page will be updated to describe them.</p>

        <h2>3. Third-party services</h2>
        <p>Articles link to external websites, including the IRS and the social networks where Alexander publishes (X, Medium, TikTok, Tumblr and Pinterest). Clicking those links takes you to services governed by their own privacy policies, which we encourage you to read.</p>

        <h2>4. Children</h2>
        <p>The Site is intended for a general audience and does not knowingly collect information from children under 13.</p>

        <h2>5. Your rights</h2>
        <p>Depending on where you live, you may have rights to access, correct or delete personal data held about you. Because the Site collects so little, there is usually nothing to act on, but you can contact us through the social profiles in the footer with any request or question.</p>

        <h2>6. Changes to this policy</h2>
        <p>We may revise this Privacy Policy as the Site evolves. The date at the top of this page shows the latest revision.</p>
      </article>
    </div>
"""
    return page(
        title="Privacy Policy",
        description="Privacy Policy for alexandercaldwell.com.",
        path="/privacy/",
        body=body,
        jsonld=graph(breadcrumb_ld([("Home", "/"), ("Privacy Policy", "/privacy/")])),
    )


def build_404() -> str:
    body = """    <div class="container narrow">
      <header class="page-head">
        <p class="eyebrow">Error 404</p>
        <h1>Page not found</h1>
        <p class="lead">The page you were looking for doesn&rsquo;t exist or has moved.</p>
        <div class="actions">
          <a href="/" class="button">Back to home</a>
          <a href="/blog/" class="button secondary">Browse articles</a>
        </div>
      </header>
    </div>
"""
    return page(
        title="Page not found",
        description="The page you were looking for does not exist.",
        path="/404.html",
        body=body,
        noindex=True,
        canonical=False,
    )


def build_sitemap(entries: list[tuple[str, dt.date, str, str]]) -> str:
    rows = []
    for path, lastmod, freq, prio in entries:
        rows.append(
            "  <url>\n"
            f"    <loc>{url(path)}</loc>\n"
            f"    <lastmod>{lastmod.isoformat()}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{prio}</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def build_robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {url('/sitemap.xml')}\n"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def clean_output() -> None:
    """Remove previously generated directories so deleted posts disappear."""
    for name in ["about", "blog", "terms", "privacy", *[slug for slug, _, _ in CATEGORIES]]:
        target = ROOT / name
        if target.is_dir():
            shutil.rmtree(target)


def main() -> None:
    posts = load_posts()
    clean_output()

    newest = max([p.date for p in posts], default=TODAY)
    sitemap: list[tuple[str, dt.date, str, str]] = []

    write(ROOT / "index.html", build_home(posts))
    sitemap.append(("/", newest, "weekly", "1.0"))

    write(ROOT / "about" / "index.html", build_about())
    sitemap.append(("/about/", LEGAL_UPDATED, "monthly", "0.8"))

    write(ROOT / "blog" / "index.html", build_blog(posts))
    sitemap.append(("/blog/", newest, "weekly", "0.8"))

    for slug, name, desc in CATEGORIES:
        write(ROOT / slug / "index.html", build_category(slug, name, desc, posts))
        mine = [p.date for p in posts if p.category == slug]
        sitemap.append((f"/{slug}/", max(mine, default=newest), "weekly", "0.7"))

    for p in posts:
        write(ROOT / p.category / p.slug / "index.html", build_post(p, posts))
        sitemap.append((p.path, p.date, "monthly", "0.6"))

    write(ROOT / "terms" / "index.html", build_terms())
    sitemap.append(("/terms/", LEGAL_UPDATED, "yearly", "0.3"))
    write(ROOT / "privacy" / "index.html", build_privacy())
    sitemap.append(("/privacy/", LEGAL_UPDATED, "yearly", "0.3"))

    write(ROOT / "404.html", build_404())
    write(ROOT / "sitemap.xml", build_sitemap(sitemap))
    write(ROOT / "robots.txt", build_robots())

    print(f"Built {len(posts)} posts, {len(CATEGORIES)} categories, {len(sitemap)} URLs.")


if __name__ == "__main__":
    main()
