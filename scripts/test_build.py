"""Checks the editing paths used for frequent publication and news updates."""

import copy
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

import build


class PageInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag in ("a", "link", "img", "script"):
            url = attributes.get("href") or attributes.get("src")
            if url:
                self.links.append(url)


class SiteBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.content = self.root / "content"
        self.content.mkdir()
        self.site = build.load_json("site.json", build.ROOT / "content")
        self.papers = build.load_json("publications.json", build.ROOT / "content")
        self.news = build.load_json("news.json", build.ROOT / "content")

    def generate(self):
        for filename, data in [("site.json", self.site), ("publications.json", self.papers), ("news.json", self.news)]:
            (self.content / filename).write_text(json.dumps(data), encoding="utf-8")
        output = self.root / "dist"
        build.build(output, self.content)
        page = (output / "index.html").read_text(encoding="utf-8")
        inspector = PageInspector()
        inspector.feed(page)
        self.assertEqual(len(inspector.ids), len(set(inspector.ids)), "Duplicate HTML IDs")
        for url in inspector.links:
            if url.startswith("#"):
                self.assertIn(url[1:], inspector.ids, f"Unresolved anchor: {url}")
            elif url.startswith("assets/"):
                self.assertTrue((output / url).is_file(), f"Missing asset: {url}")
        return page, inspector

    def test_default_content_and_assets(self):
        page, _ = self.generate()
        self.assertEqual(page.count('class="publication-card'), len(self.papers))
        self.assertIn('"@type": "Person"', page)
        self.assertIn("to=sithu31296%40gmail.com", page)
        self.assertTrue((self.root / "dist" / "mvpocc" / "index.html").is_file())

    def test_each_section_can_be_removed_without_broken_links(self):
        for section in self.site["sections"]:
            with self.subTest(section=section["id"]):
                section["enabled"] = False
                _, inspector = self.generate()
                self.assertNotIn(section["id"], inspector.ids)
                section["enabled"] = True

    def test_sections_can_be_reordered(self):
        self.site["sections"].reverse()
        _, inspector = self.generate()
        positions = [inspector.ids.index(section["id"]) for section in self.site["sections"]]
        self.assertEqual(positions, sorted(positions))

    def test_new_paper_adds_card_and_filter_year(self):
        paper = copy.deepcopy(self.papers[0])
        paper.update(id="new-paper", title="New research paper", year=2027)
        self.papers.append(paper)
        page, inspector = self.generate()
        self.assertIn("new-paper", inspector.ids)
        self.assertIn('<option value="2027">2027</option>', page)
        self.assertLess(page.index('id="new-paper"'), page.index('id="dgsfm"'))

    def test_new_news_item_is_sorted_and_archive_is_created(self):
        self.news.append({"id": "new-update", "date": "2027-01-15", "category": "News", "title": "New update", "text": "An update without a link."})
        page, _ = self.generate()
        self.assertIn("15 Jan 2027", page)
        self.assertIn("Earlier updates (1)", page)
        self.assertLess(page.index('id="new-update"'), page.index('id="dgsfm-accv-2026"'))

    def test_content_is_escaped(self):
        self.papers[0]["title"] = '<script>alert("unsafe")</script>'
        page, _ = self.generate()
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn('<script>alert("unsafe")</script>', page)

    def test_invalid_edit_fails_before_publishing(self):
        self.papers.append(copy.deepcopy(self.papers[0]))
        with self.assertRaises(ValueError):
            self.generate()
        self.papers.pop()
        self.papers[0]["image"] = "assets/images/missing.png"
        with self.assertRaises(ValueError):
            self.generate()

    def test_executable_links_are_rejected(self):
        self.papers[0]["links"][0]["url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            self.generate()

    def test_service_entries_are_rendered_once_with_roles_and_years(self):
        self.site["service"].append({"role": "Area Chair", "venues": ["New Conference 2027", "Workshop"]})
        page, _ = self.generate()
        count = sum(len(item["venues"]) for item in self.site["service"])
        self.assertEqual(page.count('class="service-cell"'), count)
        self.assertIn('New Conference <span class="service-year">2027</span>', page)
        self.assertIn('class="service-role">Area Chair</span>', page)
        self.assertNotIn('class="service-copy"', page)

    def test_invalid_service_scroll_speed_is_rejected(self):
        section = next(item for item in self.site["sections"] if item["id"] == "service")
        section["scroll_speed"] = 0
        with self.assertRaises(ValueError):
            self.generate()

    def test_email_button_uses_current_address_and_can_use_mail_app(self):
        self.site["email"] = "research+contact@example.org"
        page, _ = self.generate()
        self.assertIn("to=research%2Bcontact%40example.org", page)
        self.assertIn('<span>Email me:</span><span>research+contact@example.org</span>', page)
        self.assertEqual(page.count('class="button email-button"'), 1)
        self.site["email_client"] = "mailto"
        page, _ = self.generate()
        self.assertIn('href="mailto:research+contact@example.org"', page)


if __name__ == "__main__":
    unittest.main()
