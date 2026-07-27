# The web builds
# Веб-збірки

Everything here is generated from the markdown course. **The markdown is the
source of truth — never edit the generated HTML.**

Усе тут генерується з markdown-курсу. **Markdown — єдине джерело правди; ніколи
не редагуйте згенерований HTML.**

---

## Files

| Path | What it is |
|---|---|
| `build.py` | The build script. Renders the markdown into the app. |
| `app-template.html` | The app shell: CSS, markup, and all the interactive tools. Edit this to change the app. |
| `deck-card.html` | The hand-written quick-reference card. Not generated — edit directly. |
| `course.html` | **Generated.** The course app as a fragment, for publishing as a Claude Artifact (the host supplies the `<head>`). |
| `../docs/index.html` | **Generated.** The course app as a standalone page, for GitHub Pages. |
| `../docs/deck.html` | **Generated.** The deck card as a standalone page, for GitHub Pages. |
| `../docs/.nojekyll` | Tells GitHub Pages to serve the files as-is rather than running Jekyll. |
| `../docs/robots.txt` | **Generated.** Asks crawlers not to index the site. |

---

## Rebuilding

After editing **any** module, appendix, the glossary, the README, or the course
map:

```bash
python3 web/build.py --pages
```

That regenerates all three HTML outputs plus `robots.txt`. Then commit —
pushing to the default branch deploys the site automatically.

**`README.md` and `COURSE_MAP.md` are build inputs too**, so editing either of
those also needs a rebuild. The workflow warns you in its log if the committed
site has fallen behind the markdown.

Без `--pages` збирається лише `course.html` (варіант для артефакту). З `--pages`
додатково збирається окрема версія сайту в `docs/`.

No dependencies beyond the Python standard library.

---

## How the build works

1. **Reads the file list** from `SECTIONS` in `build.py`. To add a module,
   add a row there — that single list drives the sidebar, the ordering, the
   prev/next links, and the progress bar.
2. **Converts markdown to HTML** — headings, tables, lists, fenced code (the
   ASCII diagrams), blockquotes, emphasis, and links.
3. **Tags each block with its language.** A paragraph beginning
   `**🇨🇦 EN** — …` starts an English run; `**🇺🇦 UA** — …` starts a Ukrainian
   one. The marker itself is stripped, since the app's language toggle and
   typography carry that signal instead. Tables that are overwhelmingly
   Cyrillic are tagged Ukrainian; mixed and English tables stay visible in
   every mode, because the English terms are what you need on the water.
4. **Rewrites cross-references.** A link to another course file becomes in-app
   navigation instead of a dead link.
5. **Extracts structured data** — the glossary tables become flashcards, and
   the numbered questions and answers in module 12 become the practice exam.
6. **Fills the template** and writes the outputs.

---

## GitHub Pages

`.github/workflows/pages.yml` deploys `docs/` on every push to the default
branch, and can be run by hand from the repository's **Actions** tab
(*Deploy course site to GitHub Pages* → *Run workflow*).

Pages is already enabled for this repository (**Settings → Pages → Build and
deployment → Source: GitHub Actions**), so deploys are automatic and nothing
further is needed.

Worth knowing if you ever fork this or set it up elsewhere: **a workflow cannot
switch Pages on for itself.** The `configure-pages` step requests it with
`enablement: true`, but the workflow token is refused —
`Resource not accessible by integration` — so an admin has to flip that setting
once by hand first. The workflow prints those steps as an error annotation if it
hits that state, and also check **Settings → Actions → General** allows
workflows to run.

The site is served at:

- **<https://andriib-ca.github.io/SailBoat_Course/>** — the interactive course
- **<https://andriib-ca.github.io/SailBoat_Course/deck.html>** — the deck card

### Search engines are asked to stay away

The build writes `docs/robots.txt` (`Disallow: /`) and puts
`<meta name="robots" content="noindex, nofollow">` in every page, so compliant
crawlers should neither crawl nor index the site.

**This is a request, not access control.** Anyone with the URL can still read
the site, and scrapers that ignore `robots.txt` will too. The repository is
public as well, so the markdown remains readable — and indexable — on GitHub
itself regardless of what the Pages site says.

If you want the content genuinely private, the options are to make the
repository private (GitHub Pages on a private repository needs a paid plan) or
to generalise the personal details — module 20 refers to your daughter and her
age, and rewording it to "your child" costs nothing pedagogically.

Збірка створює `docs/robots.txt` (`Disallow: /`) і додає
`<meta name="robots" content="noindex, nofollow">` до кожної сторінки, тож
відповідні пошукові роботи не мають індексувати сайт. **Це прохання, а не
захист доступу** — будь-хто з посиланням усе одно може прочитати сайт, а
репозиторій публічний, тому markdown залишається доступним на GitHub.
