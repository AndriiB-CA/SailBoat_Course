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

---

## Rebuilding

After editing **any** module, appendix, the glossary, the README, or the course
map:

```bash
python3 web/build.py --pages
```

That regenerates all three HTML outputs. Then commit — pushing to the default
branch deploys the site automatically.

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

The workflow's `configure-pages` step has `enablement: true`, so it turns Pages
on by itself on the first run. **If that step fails with a permissions error**,
enable it once by hand and re-run the workflow:

> Repository **Settings** → **Pages** → **Build and deployment** →
> **Source: GitHub Actions**

Also check **Settings → Actions → General** allows workflows to run.

The site is served at:

- **<https://andriib-ca.github.io/SailBoat_Course/>** — the interactive course
- **<https://andriib-ca.github.io/SailBoat_Course/deck.html>** — the deck card

### One thing to be aware of

This repository is **public**, so the Pages site is publicly reachable and can
be indexed by search engines. That matters because the course was written for
you specifically — module 20 is built around your partner and daughter and
refers to her age. If you would rather that not be searchable, either:

- keep the site but add a `docs/robots.txt` containing
  `User-agent: *` / `Disallow: /` (discourages indexing; does not hide the
  site), or
- generalise the wording in `modules/20-family-sailing.md` to "your child",
  rebuild, and commit, or
- make the repository private — note that GitHub Pages on a private repository
  requires a paid plan.

Цей репозиторій **публічний**, тож сайт доступний усім і може індексуватися
пошуковими системами. Модуль 20 написаний про вашу родину і згадує вік дочки.
Якщо цього не хочеться — додайте `docs/robots.txt`, узагальніть формулювання,
або зробіть репозиторій приватним (Pages для приватних репозиторіїв вимагає
платного плану).
