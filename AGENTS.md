# AGENTS.md — working on this repository

Guidance for any automated coding assistant or human contributor. It is
tool-neutral: nothing here depends on a particular editor, agent, or vendor.

---

## 1. What this repository is

A **bilingual (English / Ukrainian) sailing course** that takes a complete
beginner in **Halifax, Nova Scotia, Canada** from no experience to the
qualifications needed to skipper a sailboat — the legally required Canadian
Pleasure Craft Operator Card (PCOC), and the Sail Canada skill certifications
that clubs, insurers and charter companies actually ask for.

- **Content:** 21 numbered modules, a course map, a ~400-term bilingual
  glossary, and four appendices. Roughly 100,000 words of Markdown.
- **Output:** a static website — one interactive single-page app plus a
  condensed quick-reference card — generated from that Markdown.
- **Audience:** one adult learner, their partner, and a child. The tone is
  direct, practical, and unsentimental.

The course is a **study aid, not an authority**. See §7.

---

## 2. Golden rules

Break these and you will silently ship a broken or stale site.

1. **Markdown is the only source of truth.** Never hand-edit
   `web/course.html` or anything in `docs/` — those are generated and your
   changes will be overwritten on the next build.
2. **`README.md` and `COURSE_MAP.md` are build inputs**, not just repo
   documentation. They are rendered into the site. Editing either requires a
   rebuild.
3. **Always rebuild and commit `docs/` in the same commit as a content
   change.** The deployed site is the committed `docs/`, not the Markdown.
4. **Never invent a regulation, price, phone number, channel number or chart
   number.** See §7.
5. **Preserve the bilingual pairing.** Every substantive English passage has a
   Ukrainian counterpart. Do not add English-only content to a bilingual
   section.

---

## 3. Commands

```bash
# Rebuild everything (the normal command — use this one)
python3 web/build.py --pages

# Rebuild only the embeddable fragment, skipping the docs/ site
python3 web/build.py
```

Requires **Python 3** only — standard library, no third-party packages, no
package manager, no lockfile, no network access.

There is no test suite. §6 describes how to verify a change.

---

## 4. Repository map

```
AGENTS.md                 This file.
README.md                 Course overview. ALSO A BUILD INPUT.
COURSE_MAP.md             Syllabus, hour estimates, season plan. ALSO A BUILD INPUT.
glossary.md               ~400 EN/UA term pairs. Source of the flashcard tool.
modules/00..20-*.md       The 21 course modules, read in numeric order.
appendix/*.md             Halifax resources, checklists, logbook & drills, links.

web/build.py              The build script. Markdown -> HTML.
web/app-template.html     App shell: CSS, markup, and the five interactive tools.
                          Edit this to change app behaviour or styling.
web/deck-card.html        The quick-reference card. Hand-written, NOT generated.
web/course.html           GENERATED. Body fragment, for embedding in a host that
                          supplies its own <head>.
web/README.md             Build documentation.

docs/                     GENERATED — the deployed site. Do not hand-edit.
  index.html                The course app as a standalone page.
  deck.html                 The deck card as a standalone page.
  robots.txt                Asks crawlers not to index.
  .nojekyll                 Serve files verbatim; do not run Jekyll.

.github/workflows/pages.yml  Deploys docs/ to GitHub Pages.
```

---

## 5. Content conventions

The build infers meaning from Markdown patterns. Follow them or content will
be mis-tagged.

### Bilingual language markers

A paragraph that begins with a language marker opens a **language run**;
following paragraphs inherit it until the next marker, a heading, or a `---`
rule.

```markdown
**🇨🇦 EN** — English prose here. Following paragraphs stay English.

**🇺🇦 UA** — Український текст. Наступні абзаци залишаються українськими.
```

- A bold lead-in is preserved: `**🇨🇦 EN — Critical:**` renders as
  **Critical:**. The marker is stripped; the lead-in survives.
- A leading emoji is preserved: `**⚠️ 🇨🇦 EN — …**` keeps the ⚠️.
- The markers themselves never appear in the built site — the app's language
  toggle and typography carry that signal instead.
- A paragraph with no marker that is more than 50% Cyrillic is treated as
  Ukrainian anyway.

### Headings

Bilingual headings use ` / ` as the separator, and the build splits them so
each half can be shown independently:

```markdown
## 4.2 Port tack and starboard tack / Правий і лівий галс
```

A heading that is entirely Cyrillic is treated as the Ukrainian twin of the
heading above it.

### Tables

A table more than 35% Cyrillic is tagged Ukrainian and hides in
English-only mode. Mixed and English tables stay visible in **every** language
mode — deliberately, because the English terms are what a learner needs on the
water and with an English-speaking instructor.

### Checklists

Both of these become interactive, browser-persisted checkboxes:

```markdown
- [ ] A markdown task item
- ☐ A ballot-box item
```

### Cross-references

Link to another course file by relative path. The build rewrites it into
in-app navigation:

```markdown
See [Module 01](01-safety-and-cold-water.md) and [the glossary](../glossary.md).
```

A link whose target is not in `SECTIONS` renders as **plain text, silently** —
if a cross-reference stops working, check `SECTIONS` first.

### Fenced code blocks

Used for ASCII diagrams. Preserved verbatim and made horizontally scrollable.
Do not reflow or "tidy" them; the alignment is the diagram.

---

## 6. Verifying a change

No automated tests exist. Do this instead, in order.

**1. Rebuild and confirm the counts did not collapse.**

```bash
python3 web/build.py --pages
```

Expect roughly: `documents: 28`, `glossary: ~394 terms`, `quiz: 25 questions`.
A sudden drop means a parsing regression, not a content change.

**2. Confirm the build is deterministic.** Two consecutive builds must be
byte-identical:

```bash
python3 web/build.py --pages >/dev/null
a=$(sha256sum docs/index.html | cut -d' ' -f1)
python3 web/build.py --pages >/dev/null
b=$(sha256sum docs/index.html | cut -d' ' -f1)
[ "$a" = "$b" ] && echo reproducible || echo NOT REPRODUCIBLE
```

**3. Check for Markdown that leaked through the converter.**

```bash
grep -o '\*\*' docs/index.html | wc -l          # expect 0
grep -c '](.*\.md' docs/index.html              # expect 0
```

**4. Check every internal Markdown link resolves.**

```bash
python3 - <<'EOF'
import pathlib, re, urllib.parse
bad = 0
for p in sorted(pathlib.Path('.').rglob('*.md')):
    if '.git' in p.parts:
        continue
    fenced = False
    for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
        if line.lstrip().startswith('```'):      # skip example code
            fenced = not fenced
            continue
        if fenced:
            continue
        for m in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', line):
            t = m.group(1).split('#')[0]
            if not t or t.startswith(('http', 'mailto:')):
                continue
            if not (p.parent / urllib.parse.unquote(t)).exists():
                print('BROKEN', p, i, t)
                bad += 1
print('broken links:', bad)
EOF
```

**5. Open `docs/index.html` in a real browser** and check, at minimum:
sidebar navigation, the EN / UA / both toggle in all three states, one
interactive tool, and the mobile layout. The browser console must be clean.
Screenshots catch layout and bilingual-concatenation problems that no
assertion will.

**6. Commit the regenerated `docs/` together with your Markdown change.**

---

## 7. Editorial policy — this is safety-critical content

People may act on this material on cold open water. Treat accuracy as the
primary requirement.

**Do not invent or "improve" any of the following. If you cannot verify it,
leave it alone or mark it clearly as unverified:**

- Legal or regulatory requirements (safety equipment, licensing, age limits)
- VHF channel numbers, distress procedures, radio phrasing
- Chart numbers, buoyage conventions, light characteristics
- Water temperatures, tidal ranges, cold-water survival timings
- Prices, phone numbers, course schedules, club programs

**The authoritative sources are named in the content and must stay named:**
Transport Canada's *Safe Boating Guide* (TP 511) for equipment and law, Sail
Canada for certification standards, the Canadian Hydrographic Service for
charts and tides, and the clubs themselves for programs and costs.

**Keep the hedges.** Where the text says "verify before relying on this",
"approximately", or "confirm with your provider", that wording is deliberate
and load-bearing. Removing it to make prose tighter makes the document less
safe and less honest.

**Canada-specific facts that are easy to get wrong:**

- Buoyage is **IALA Region B** — red to starboard when returning. This is the
  *opposite* of Europe. Do not "correct" it toward European convention.
- A sailboat under engine is legally a **power-driven vessel**, with no
  sailing right of way.
- The **PCOC** licenses the operator; the **Pleasure Craft Licence (PCL)**
  registers the hull. They are different documents.

---

## 8. Common tasks

### Edit existing content

Edit the Markdown, run `python3 web/build.py --pages`, commit both.

### Add a module

1. Create `modules/NN-slug.md`, following the bilingual conventions in §5.
2. Add a row to `SECTIONS` in `web/build.py`:
   `("mNN", "modules/NN-slug.md", "NN · English title", "Ukrainian title")`.
   That one list drives the sidebar, reading order, prev/next links and the
   progress bar.
3. Only ids matching `m\d\d` count toward the progress bar.
4. Add the module to the tables in `README.md` and `COURSE_MAP.md`.
5. Rebuild, verify per §6, commit.

### Add a glossary term

Add a row to the appropriate topic table in `glossary.md`. For the flashcard
tool to pick it up, the row needs an English term and a Ukrainian term that is
at least 45% Cyrillic. Two- and three-column tables are both supported; the
middle column is pronunciation.

### Change app behaviour or styling

Edit `web/app-template.html` — it holds all the CSS, markup and JavaScript,
including the five tools. Then rebuild.

The template contains placeholders the build substitutes:
`/*__DOCS__*/'{}'`, `/*__NAV__*/'[]'`, `/*__GLOSSARY__*/'[]'`,
`/*__QUIZ__*/'[]'`, `/*__PROGRESS__*/'[]'`, and the `<!--SITE_NAV-->` marker.
Leave them intact.

### Change the deck card

`web/deck-card.html` is hand-written, not generated. Edit it directly, then
rebuild so `docs/deck.html` picks up the change.

---

## 9. App architecture notes

`docs/index.html` is a single self-contained file, about 1.1 MB. That is
deliberate: no build tooling, no dependencies, no network requests, and it
works offline from a phone at a dock.

- **All content is embedded as JSON** and one section is injected into the DOM
  at a time, so the page stays responsive despite its size.
- **Progress, checkbox state, quiz scores and the logbook live in
  `localStorage`**, keyed `halifax-sailing-v1`. Every access is wrapped in
  `try`/`catch` and degrades to in-memory state, because some embedding
  contexts block storage. State is per-browser: it does not sync across
  devices and is lost if site data is cleared. That is why the logbook has an
  export.
- **Theme** follows `prefers-color-scheme`, with tokens redefined under
  `:root[data-theme="dark"]` / `[data-theme="light"]` so an explicit host
  setting wins in both directions.
- **No external resources.** No CDN, no web fonts, no analytics. Fonts are
  system stacks; the favicon is an inline SVG data URI. Keep it that way — it
  is what makes the file portable and private.

---

## 10. Deployment

`.github/workflows/pages.yml` publishes `docs/` to GitHub Pages on every push
to the default branch, and can be run manually from the Actions tab.

- The workflow **warns but does not fail** if committed `docs/` is behind the
  Markdown. Treat that warning as a bug in your commit.
- GitHub Pages must be enabled once by a repository admin
  (**Settings → Pages → Source: GitHub Actions**). A workflow token cannot
  enable it; the API refuses with `Resource not accessible by integration`.
- The site requests no indexing via `docs/robots.txt` and a `noindex` meta
  tag. That is a request to compliant crawlers, **not access control** — the
  repository is public and the content is readable by anyone with the URL.

Details in [`web/README.md`](web/README.md).
