# Sithu Aung · academic website

A modern academic portfolio with restrained typography, pastel colors, fine borders, and geometric details inspired by Rawfolio. Upright image frames, modest accents, and readable publication cards keep the presentation professional. It preserves the biography, five publications, project links, and reviewing information from the existing website. The news entries are publication milestones drawn from that content; their dates use years because announcement dates were not provided.

**No npm, framework, database, or third-party Python packages are needed.** Python 3.10+ builds ordinary HTML, CSS, and JavaScript. All content is readable without JavaScript. JavaScript adds the mobile menu, publication filters, and automatic scrolling for the reviewing strip. Fonts and images are hosted locally.

## Preview locally

```sh
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

Open <http://localhost:8000>. Stop the server with Ctrl+C. You can also open `dist/index.html` directly in a browser. Generated files live in `dist/`; edit source files and rebuild rather than editing that folder.

## Where to edit

The green role badge above the name is configured by `hero.badge` in `content/site.json`. Set it to an empty string to hide it; `theme.badgegreen` controls its color.

The introduction uses a large, transparent point-cloud reconstruction of buildings and roads behind the shadowed portrait. Set `hero.show_artwork` to `false` to return to the plain portrait, or set `hero.artwork` to replace the decorative background asset. The asset is `assets/images/reconstruction-pointcloud.png`; its generation prompt and provenance are recorded in `docs/hero-pointcloud-prompt.md`.

Academic background uses white cards with pastel status badges. Edit `about.cards` to change each card's label, title, institution, and theme color. Cards correspond in order to the existing `about.paragraphs`, which supply the biography text; `about.links` keeps names and affiliations linked. Cards stack vertically on mobile.

Contact has one email button showing the configured `email` address. By default, `email_client: "gmail"` opens Gmail's compose page in a new tab with the recipient filled in; visitors may need to sign in. Set `email_client` to `"mailto"` to use visitors' configured email apps instead.

| File | Purpose |
| --- | --- |
| `content/site.json` | Profile, biography, research topics, service, links, colors, section headings, order, visibility, and preserved project folders |
| `content/publications.json` | Papers, authors, venues, years, images, tags, and resource links |
| `content/news.json` | News and publication announcements |
| `templates/sections/*.html` | Independent section layouts |
| `templates/base.html` | Shared head, header, navigation, and footer |
| `assets/styles.css` | Typography, layout, and mobile styles |
| `assets/main.js` | Mobile menu, combined publication filters, and reviewing strip controls |
| `scripts/build.py` | Content validation and static HTML generation |
| `.github/workflows/pages.yml` | Checks, build, and GitHub Pages deployment |

## Add a paper

All publication cards share white backgrounds, borders, title sizes, and the same offset shadow geometry as the buttons; only the accent color changes for highlighted papers. Highlighted papers use pink shadows and badges; set `theme.highlight` and `theme.pink` in `content/site.json` to customize these colors.

Copy an object in `content/publications.json` and edit it. Add the preview image under `assets/images/`. For example:

```json
{
  "id": "new-paper",
  "title": "Full paper title",
  "authors": ["Sithu Aung", "Another Author"],
  "venue": "Conference 2027",
  "year": 2027,
  "featured": false,
  "image": "assets/images/new-paper.png",
  "image_alt": "A meaningful description of the paper preview",
  "description": "A short description of the contribution.",
  "tags": ["3D Vision"],
  "links": [
    {"label": "Paper", "url": "https://example.com/paper"},
    {"label": "Code", "url": "https://github.com/your-account/your-project"}
  ]
}
```

Papers appear in a single-column list with a preview on the left and details on the right; previews stack above the text on mobile. The conference name sits at the preview panel's top-left, the optional badge at its top-right, and tags at its bottom-left. The image remains unobstructed between them on a white background. Papers sort by year, newest first; within a year, they retain their order in the file. Set `featured` to `true` to emphasize a paper with a pink offset shadow and badge. Badges labeled `"Oral"`, `"Highlight"`, or `"Spotlight"` automatically receive the emphasized styling. Featured papers without a badge display `"Featured"`. Author names matching `site.name` are highlighted, including names with an equal-contribution `*`. Add any number of resource links, including a relative PDF or BibTeX file under `assets/`. There is no fixed paper limit; year filters update automatically.

## Add news

Add an object to `content/news.json`:

```json
{
  "id": "paper-accepted-2027",
  "date": "2027-01-15",
  "category": "Publication",
  "title": "Our new paper was accepted!",
  "text": "A sentence about the paper or event.",
  "url": "https://example.com/project"
}
```

The `url` is optional. Dates support `YYYY-MM-DD`, `YYYY-MM`, or `YYYY`. Updates sort newest first; items with equal dates retain file order. Set the news section's `visible_count` in `site.json` to control the initial list. Older items appear in an accessible expandable archive. Use a unique lowercase, hyphenated ID for every paper and news item.

## Remove, reorder, or add sections

The service and reviewing section shows conference names in a bordered white strip. Edit `site.service` to add venues or roles. Set the service section's `scroll_speed` to control speed in pixels per second (default: `36`, maximum: `200`). The compact strip scrolls automatically using a measured, seamless loop and has an explicit pause/resume button; hovering or focusing it does not interrupt playback. Short lists repeat to fill the available width; visual duplicates are hidden from assistive technology. With reduced-motion settings, the original entries are manually scrollable and a Start scrolling button lets visitors explicitly enable motion. With JavaScript disabled, the list remains manually scrollable.

In `site.json`, set a section's `enabled` to `false` to remove it and its navigation link. Move section objects to change the page order. Removing publications also updates the hero button so it does not link to a missing section. A section's optional `nav` controls its navigation label; omit it to leave the section off the menu. Set `show_filters` to `false` to hide publication search and year filters.

To introduce a new kind of section:

1. Add its JSON data to `site.json` or a new content file.
2. Add `templates/sections/your-section.html`.
3. Add its ID to `SECTION_IDS` and a matching data preparation branch in `render_section()` in `scripts/build.py`.
4. Add an entry to `site.sections` and styles to `assets/styles.css`.

Templates use Python's `$variable` syntax. Use `$$` for a literal dollar sign in template markup. Content is plain text and HTML-escaped during generation; use the configured link lists for linked biography names.

The agency reference's services become research interests, portfolio becomes publications, and blog becomes news. Biography and contact retain their role. No fictional client testimonials, agency claims, or nonfunctional contact form are included.

## Publish to sithu31296.github.io

The source is ready for the existing `sithu31296/sithu31296.github.io` repository. This workspace was empty and is not connected to that repository, so it has not been pushed or deployed.

1. Copy these source files into a checkout of the existing repository. Preserve any unrelated files or project subdirectories you still need. Commit on a branch and review the change.
2. In GitHub, open **Settings → Pages → Build and deployment → Source**, and select **GitHub Actions**. [GitHub's official instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) explain this setup.
3. Merge or push the source to the repository's default branch (`main` or `master`). The workflow validates content, builds `dist/`, and publishes it. Later content-only commits use the same workflow.
4. Check the workflow in the repository's **Actions** tab and visit <https://sithu31296.github.io/>.

Pull requests run checks and build without deploying. The workflow deploys only from the default branch. If that branch has another name, update `on.push.branches` in the workflow. No personal access token is needed for the workflow; it uses GitHub's provided deployment token.

**Existing project URLs:** your existing `mvpocc/` project page and its assets are included and copied into the build, preserving `/mvpocc/`. To retain additional project folders, add their top-level directory names to `site.static_directories`. The generator copies only the assets and project folders you configure. Separately hosted project repositories are unaffected. Keep `site.url` correct for canonical URLs, social previews, and the sitemap. Relative asset paths also work under a GitHub Pages project subpath.

## Verify updates

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build.py
```

Checks cover missing images, duplicate IDs, unsafe links, new publication years, news sorting and archives, section removal and reordering, escaping, local assets, and internal anchors. Before deploying visual changes, inspect desktop and mobile layouts in a browser. JavaScript syntax and filter/menu behavior were checked during implementation; browser visual QA could not run because computer-use permissions were unavailable.

## Assets and provenance

The portrait and paper previews were copied from the existing [Sithu Aung website](https://sithu31296.github.io/). The design takes inspiration from [Rawfolio](https://cloudy-beaver-926302.framer.app/) but does not copy its implementation or agency assets. Self-hosted Archivo Black and Hanken Grotesk fonts use the SIL Open Font License; licenses are included in `assets/fonts/`.
