#!/usr/bin/env python3
"""Build a portable, pre-rendered academic website using only Python's stdlib.

Content lives in content/*.json. Section markup lives in templates/sections/.
Run from any directory: python3 scripts/build.py
"""

import argparse
import html
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from string import Template
from urllib.parse import quote, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
SECTION_IDS = {"hero", "news", "research", "publications", "about", "service", "contact"}
ICONS = {
    "cube": '<path d="m40 8 28 16v32L40 72 12 56V24L40 8Zm0 32L12 24m28 16 28-16M40 40v32"/>',
    "scene": '<path d="M8 60h64M16 60V28h20v32m8 0V12h20v48M22 36h8m-8 8h8m20-24h8m-8 10h8m-8 10h8m-8 10h8"/>',
    "layers": '<path d="m40 10 30 17-30 17L10 27 40 10Zm-30 32 30 17 30-17M10 57l30 17 30-17"/>',
}


def escape(value):
    return html.escape(str(value), quote=True)


def load_json(name, content_dir):
    with (content_dir / name).open(encoding="utf-8") as source:
        return json.load(source)


def validate_url(url):
    """Reject executable schemes; allow web URLs, anchors, and relative files."""
    if not isinstance(url, str) or not url or url.startswith("//"):
        raise ValueError(f"Invalid URL: {url!r}")
    if urlparse(url).scheme not in ("https", "http", "mailto", ""):
        raise ValueError(f"Unsupported URL scheme: {url!r}")
    return url


def link(item, css=""):
    label, url = escape(item["label"]), escape(validate_url(item["url"]))
    return f'<a class="{css}" href="{url}">{label}</a>'


def render_template(name, values):
    source = (ROOT / "templates" / name).read_text(encoding="utf-8")
    return Template(source).substitute(values)


def validate_content(site, publications, news):
    """Fail before publishing if a common editing mistake would break the site."""
    validate_url(site["url"])
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", site["email"]):
        raise ValueError("site.email must be a valid email address")
    if site.get("email_client", "gmail") not in {"gmail", "mailto"}:
        raise ValueError("email_client must be gmail or mailto")
    ids = [section["id"] for section in site["sections"]]
    if len(ids) != len(set(ids)) or not set(ids) <= SECTION_IDS:
        raise ValueError("Section IDs must be unique and have a matching renderer")
    for section in site["sections"]:
        if not isinstance(section["enabled"], bool):
            raise ValueError("Section enabled values must be true or false")
        if section["id"] == "news" and section.get("visible_count", 3) < 1:
            raise ValueError("News visible_count must be at least 1")
        if section["id"] == "service":
            speed = section.get("scroll_speed", 36)
            if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not 0 < speed <= 200:
                raise ValueError("Service scroll_speed must be between 0 and 200 pixels per second")
    for collection in (publications, news):
        item_ids = [item["id"] for item in collection]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Publication and news IDs must be unique within their file")
        for item_id in item_ids:
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item_id):
                raise ValueError(f"Use lowercase hyphenated IDs: {item_id}")
    all_ids = ids + [item["id"] for item in publications + news] + ["main", "site-nav", "paper-search", "paper-year", "service-strip"] + [f"{section_id}-title" for section_id in SECTION_IDS]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Paper and news IDs must not collide with each other or section IDs")
    for paper in publications:
        if not isinstance(paper["year"], int):
            raise ValueError("Publication year must be an integer")
        for key in ("title", "venue", "description", "image_alt"):
            if not isinstance(paper[key], str) or not paper[key].strip():
                raise ValueError(f"Publication {paper['id']} needs {key}")
        if not paper["authors"] or not paper["links"]:
            raise ValueError("A publication needs authors and at least one link")
    image_paths = [site["portrait"]] + [paper["image"] for paper in publications]
    if site["hero"].get("artwork") and site["hero"].get("show_artwork", True):
        image_paths.append(site["hero"]["artwork"])
    for path in image_paths:
        resolved = (ROOT / path).resolve()
        if not resolved.is_relative_to(ROOT / "assets") or not resolved.is_file():
            raise ValueError(f"Image must be an existing file under assets/: {path}")
    for key, color in site["theme"].items():
        if not re.fullmatch(r"[a-z]+", key) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError("Theme colors must use six-digit hex values")
    for directory in site.get("static_directories", []):
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", directory) or directory in {"assets", "content", "templates", "scripts", "dist"}:
            raise ValueError(f"Static directories must be dedicated top-level project folders: {directory}")
        if not (ROOT / directory).is_dir():
            raise ValueError(f"Missing static project directory: {directory}")
    for item in news:
        format_news_date(item["date"])
        if item.get("url"):
            validate_url(item["url"])
    for group in [site["socials"], site["about"]["links"]] + [p["links"] for p in publications]:
        for item in group:
            validate_url(item["url"])


def format_news_date(value):
    """Support exact dates, months, or years without inventing date precision."""
    for pattern, display in [(r"\d{4}-\d{2}-\d{2}", "%d %b %Y"), (r"\d{4}-\d{2}", "%b %Y"), (r"\d{4}", "%Y")]:
        if re.fullmatch(pattern, value):
            parse_format = {10: "%Y-%m-%d", 7: "%Y-%m", 4: "%Y"}[len(value)]
            return datetime.strptime(value, parse_format).strftime(display)
    raise ValueError(f"Use YYYY, YYYY-MM or YYYY-MM-DD for a news date: {value}")


def news_row(item, index):
    heading = escape(item["title"])
    if item.get("url"):
        heading = link({"label": item["title"], "url": item["url"]})
    return f'''<article class="news-row" id="{escape(item['id'])}">
      <span class="news-number" aria-hidden="true">{index:02d}</span>
      <div class="news-date"><time datetime="{escape(item['date'])}">{escape(format_news_date(item['date']))}</time><span class="label">{escape(item['category'])}</span></div>
      <div class="news-copy"><h3>{heading}</h3><p>{escape(item['text'])}</p></div>
    </article>'''


def publication_card(paper, name):
    authors = ", ".join(f"<strong>{escape(author)}</strong>" if author.rstrip("*") == name else escape(author) for author in paper["authors"])
    tags = "".join(f'<span>{escape(tag)}</span>' for tag in paper.get("tags", []))
    badge_label = paper.get("badge", "")
    highlighted = paper.get("featured") or badge_label.strip().casefold() in {"oral", "highlight", "spotlight"}
    if highlighted and not badge_label:
        badge_label = "Featured"
    badge = f'<span class="paper-badge">{escape(badge_label)}</span>' if badge_label else ""
    css = "publication-card featured" if highlighted else "publication-card"
    search = " ".join([paper["title"], paper["venue"], *paper["authors"], *paper.get("tags", [])])
    links = "".join(link(item, "button button-small") for item in paper["links"])
    return f'''<article class="{css}" id="{escape(paper['id'])}" data-year="{paper['year']}" data-search="{escape(search.lower())}">
      <div class="paper-image">
        <div class="paper-meta"><span>{escape(paper['venue'])}</span>{badge}</div>
        <div class="paper-preview"><img src="{escape(paper['image'])}" alt="{escape(paper['image_alt'])}" loading="lazy" decoding="async"></div>
        <div class="paper-tags">{tags}</div>
      </div>
      <div class="paper-content"><h3>{escape(paper['title'])}</h3><p class="paper-authors">{authors}</p><p class="paper-description">{escape(paper['description'])}</p><div class="paper-links">{links}</div></div>
    </article>'''


def linked_paragraph(text, links):
    """Link names in plain-text biography copy, without accepting arbitrary HTML."""
    by_label = {item["label"]: item for item in links}
    pattern = "|".join(re.escape(label) for label in sorted(by_label, key=len, reverse=True))
    parts, cursor = [], 0
    for match in re.finditer(pattern, text) if pattern else []:
        parts.extend([escape(text[cursor:match.start()]), link(by_label[match.group()])])
        cursor = match.end()
    parts.append(escape(text[cursor:]))
    return "<p>" + "".join(parts) + "</p>"


def render_section(section, site, papers, news):
    """Each section has its own data preparation and independent HTML template."""
    values = {key: escape(value) for key, value in section.items() if isinstance(value, str)}
    values.update(name=escape(site["name"]), email=escape(site["email"]))
    values["socials"] = "".join(link(item, "button button-small button-secondary") for item in site["socials"])
    section_id = section["id"]
    if section_id == "hero":
        enabled = {s["id"] for s in site["sections"] if s["enabled"]}
        values["hero_contact_url"] = "#contact" if "contact" in enabled else f"mailto:{escape(site['email'])}"
        primary = {"label": "Explore my work", "url": "#publications"} if "publications" in enabled else {"label": "Email me", "url": f"mailto:{site['email']}"}
        values.update({key: escape(value) for key, value in site["hero"].items()})
        badge = site["hero"].get("badge", "")
        values["hero_badge"] = f'<p class="hero-badge">{escape(badge)}</p>' if badge else ""
        artwork = site["hero"].get("artwork", "")
        show_artwork = artwork and site["hero"].get("show_artwork", True)
        values["portrait_art_class"] = "hero-art has-artwork" if show_artwork else "hero-art"
        values["hero_artwork"] = f'<img class="hero-abstract" src="{escape(artwork)}" alt="" aria-hidden="true" width="1536" height="1024" decoding="async">' if show_artwork else ""
        values.update(hero_description=escape(site["hero"]["description"]), role=escape(site["role"]), portrait=escape(site["portrait"]), location=escape(site["location"]), hero_primary=link(primary, "button"))
    elif section_id == "news":
        rows = [news_row(item, i + 1) for i, item in enumerate(news)]
        count = section.get("visible_count", 3)
        values["news_items"] = "".join(rows[:count]) or '<p class="section-description">Updates will appear here.</p>'
        values["news_archive"] = f'<details class="news-archive"><summary>Earlier updates ({len(rows) - count}) <span aria-hidden="true">＋</span></summary><div class="news-list">{"".join(rows[count:])}</div></details>' if len(rows) > count else ""
    elif section_id == "research":
        cards = []
        for topic in site["research"]:
            if topic["color"] not in site["theme"]:
                raise ValueError("Research colors must name a theme color")
            icon = ICONS[topic["icon"]]
            cards.append(f'<article class="research-card" style="--card-color:var(--{escape(topic["color"])})"><div class="research-card-top"><svg viewBox="0 0 80 80" fill="none" aria-hidden="true">{icon}</svg><h3>{escape(topic["title"])}</h3></div><p>{escape(topic["description"])}</p></article>')
        values["research_cards"] = "".join(cards)
    elif section_id == "publications":
        values.update(section_description=escape(section.get("description", "")), paper_count=len(papers), publication_cards="".join(publication_card(p, site["name"]) for p in papers))
        values["scholar_url"] = escape(next((item["url"] for item in site["socials"] if item["label"] == "Google Scholar"), f"mailto:{site['email']}"))
        options = "".join(f'<option value="{year}">{year}</option>' for year in sorted({p["year"] for p in papers}, reverse=True))
        values["filters"] = f'<form class="publication-filters" role="search" aria-label="Filter publications" hidden><div class="search-field"><label for="paper-search">Search publications</label><input id="paper-search" type="search" placeholder="Title, author, or topic…" autocomplete="off"></div><div class="year-field"><label for="paper-year">Year</label><select id="paper-year"><option value="all">All years</option>{options}</select></div><button class="text-link reset-filter" type="reset">Clear filters <span aria-hidden="true">×</span></button></form>' if section.get("show_filters", True) else ""
    elif section_id == "about":
        cards = []
        metadata = site["about"].get("cards", [])
        for i, paragraph in enumerate(site["about"]["paragraphs"]):
            card = metadata[i] if i < len(metadata) else {}
            color = card.get("color", "blue")
            if color not in site["theme"]:
                raise ValueError("Academic card colors must name a theme color")
            badge = f'<span class="academic-badge">{escape(card["label"])}</span>' if card.get("label") else ""
            institution = f'<p class="academic-institution">{escape(card["institution"])}</p>' if card.get("institution") else ""
            body = linked_paragraph(paragraph, site["about"]["links"])
            cards.append(f'<article class="academic-card" style="--academic-color:var(--{escape(color)})">{badge}<h3>{escape(card.get("title", "Academic experience"))}</h3>{institution}<div class="academic-copy">{body}</div></article>')
        values["academic_cards"] = "".join(cards)
    elif section_id == "service":
        cells = []
        for item in site["service"]:
            for venue in item["venues"]:
                match = re.fullmatch(r"(.+)\s+(\d{4})", venue)
                name = escape(match[1]) if match else escape(venue)
                year = f'<span class="service-year">{escape(match[2])}</span>' if match else ""
                cells.append(f'<li class="service-cell"><span class="service-venue">{name} {year}</span><span class="service-role">{escape(item["role"])}</span></li>')
        values.update(service_items="".join(cells), scroll_speed=section.get("scroll_speed", 36))
    elif section_id == "contact":
        values["section_description"] = escape(section.get("description", ""))
        if site.get("email_client", "gmail") == "gmail":
            values["email_compose_url"] = escape(f'https://mail.google.com/mail/?view=cm&fs=1&to={quote(site["email"], safe="")}')
            values["email_target"] = 'target="_blank" rel="noopener noreferrer"'
            values["email_label"] = escape(f'Compose an email to {site["email"]} in Gmail (opens in a new tab)')
        else:
            values["email_compose_url"] = f'mailto:{escape(site["email"])}'
            values["email_target"] = ""
            values["email_label"] = escape(f'Compose an email to {site["email"]}')
    return render_template(f"sections/{section_id}.html", values)


def build(output_dir, content_dir=ROOT / "content"):
    site = load_json("site.json", content_dir)
    papers = load_json("publications.json", content_dir)
    news = load_json("news.json", content_dir)
    validate_content(site, papers, news)
    # Stable sorting preserves editorial order for papers/news with equal dates.
    papers = sorted(papers, key=lambda p: p["year"], reverse=True)
    news = sorted(news, key=lambda item: item["date"], reverse=True)
    enabled = [s for s in site["sections"] if s["enabled"]]
    navigation = "".join(link({"label": s["nav"], "url": f"#{s['id']}"}, "button button-small nav-contact" if s["id"] == "contact" else "nav-link") for s in enabled if s.get("nav"))
    structured = {"@context": "https://schema.org", "@type": "Person", "name": site["name"], "url": site["url"], "image": urljoin(site["url"], site["portrait"]), "jobTitle": site["role"], "sameAs": [item["url"] for item in site["socials"]]}
    values = {key: escape(site[key]) for key in ["name", "title", "description", "url"]}
    values.update(year=date.today().year, navigation=navigation, sections="\n".join(render_section(s, site, papers, news) for s in enabled), theme_paper=site["theme"]["paper"], theme_variables=" ".join(f"--{key}: {value};" for key, value in site["theme"].items()), portrait_url=escape(urljoin(site["url"], site["portrait"])), structured_data=json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c"))
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", output_dir / "assets", dirs_exist_ok=True)
    for directory in site.get("static_directories", []):
        shutil.copytree(ROOT / directory, output_dir / directory, dirs_exist_ok=True)
    (output_dir / "index.html").write_text(render_template("base.html", values), encoding="utf-8")
    (output_dir / ".nojekyll").touch()
    (output_dir / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {urljoin(site['url'], 'sitemap.xml')}\n", encoding="utf-8")
    (output_dir / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{escape(site["url"])}</loc></url></urlset>\n', encoding="utf-8")
    print(f"Built {len(enabled)} sections, {len(papers)} papers, {len(news)} news items → {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        build(args.output.resolve())
    except (ValueError, KeyError, FileNotFoundError) as error:
        parser.exit(1, f"Build failed: {error}\n")
