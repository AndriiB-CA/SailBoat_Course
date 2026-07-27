#!/usr/bin/env python3
"""
Build the interactive course app from the markdown source.

Reads every module and appendix, converts markdown to HTML, tags each block
with its language so the EN/UA toggle can collapse the page to one language,
extracts the glossary and the PCOC quiz into structured data, and emits a
single self-contained HTML file.

Usage:  python3 web/build.py
Output: web/course.html
"""

import json
import pathlib
import re
import html as htmllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "course.html"

# ---------------------------------------------------------------- structure

SECTIONS = [
    ("Start here", [
        ("readme",     "README.md",                          "Overview",                       "Огляд"),
        ("map",        "COURSE_MAP.md",                      "Course map & season plan",       "Карта курсу та план сезону"),
    ]),
    ("Stage 0–1 · Orientation & survival", [
        ("m00", "modules/00-orientation.md",                 "00 · Orientation",               "Орієнтація"),
        ("m01", "modules/01-safety-and-cold-water.md",       "01 · Safety & cold water",       "Безпека та холодна вода"),
    ]),
    ("Stage 2 · Understand the boat", [
        ("m02", "modules/02-how-a-sailboat-works.md",        "02 · How a sailboat works",      "Як працює вітрильник"),
        ("m03", "modules/03-boat-anatomy.md",                "03 · Boat anatomy & rigging",    "Будова судна"),
        ("m04", "modules/04-points-of-sail-and-trim.md",     "04 · Points of sail & trim",     "Курси та налаштування"),
        ("m05", "modules/05-manoeuvres.md",                  "05 · Manoeuvres",                "Маневри"),
        ("m06", "modules/06-knots-and-ropework.md",          "06 · Knots & ropework",          "Вузли"),
    ]),
    ("Stage 3 · Shore knowledge & the licence", [
        ("m07", "modules/07-rules-of-the-road.md",           "07 · Rules of the road",         "Правила розходження"),
        ("m08", "modules/08-buoys-and-lights.md",            "08 · Buoys & lights",            "Буї та вогні"),
        ("m09", "modules/09-weather-halifax.md",             "09 · Weather for Halifax",       "Погода Галіфаксу"),
        ("m10", "modules/10-charts-and-navigation.md",       "10 · Charts & navigation",       "Карти та навігація"),
        ("m11", "modules/11-vhf-radio.md",                   "11 · VHF radio & ROC(M)",        "VHF-радіо"),
        ("m12", "modules/12-pcoc-exam-prep.md",              "12 · PCOC exam prep",            "Підготовка до PCOC"),
    ]),
    ("Stage 4 · Practical seamanship", [
        ("m13", "modules/13-engine-and-docking.md",          "13 · Engine & docking",          "Двигун і швартування"),
        ("m14", "modules/14-emergencies-and-mob.md",         "14 · Emergencies & MOB",         "Аварії та людина за бортом"),
        ("m15", "modules/15-basic-cruising-practical.md",    "15 · Basic Cruising",            "Basic Cruising"),
    ]),
    ("Stage 5 · Cruising & mastery", [
        ("m16", "modules/16-intermediate-cruising.md",       "16 · Intermediate Cruising",     "Intermediate Cruising"),
        ("m17", "modules/17-halifax-cruising-grounds.md",    "17 · Cruising grounds",          "Райони плавання"),
        ("m18", "modules/18-ownership-and-mastery.md",       "18 · Ownership & mastery",       "Володіння та майстерність"),
    ]),
    ("Specialist tracks", [
        ("m19", "modules/19-buying-a-boat.md",               "19 · Buying a boat",             "Купівля судна"),
        ("m20", "modules/20-family-sailing.md",              "20 · Sailing with family",       "Плавання з родиною"),
    ]),
    ("Reference", [
        ("glossary",   "glossary.md",                        "Glossary EN ⇄ UA",               "Глосарій"),
        ("resources",  "appendix/halifax-resources.md",      "Halifax resources",              "Ресурси Галіфаксу"),
        ("checklists", "appendix/checklists.md",             "Checklists",                     "Контрольні листи"),
        ("drills",     "appendix/logbook-and-drills.md",     "Logbook & drills",               "Журнал і вправи"),
        ("links",      "appendix/links.md",                  "Vetted links",                   "Перевірені посилання"),
    ]),
]

# modules that count toward the progress bar
PROGRESS_IDS = [i for _, items in SECTIONS for (i, *_) in items if re.fullmatch(r"m\d\d", i)]

# ---------------------------------------------------------------- utilities

CYR = re.compile(r"[Ѐ-ӿ]")
LAT = re.compile(r"[A-Za-z]")

def cyr_ratio(text):
    c, l = len(CYR.findall(text)), len(LAT.findall(text))
    return c / (c + l) if (c + l) else 0.0

_LEAD_EMOJI = r"(?:[\u2190-\u2BFF\U0001F000-\U0001F1E5\U0001F200-\U0001FAFF\uFE0F]\s*)*"
EN_MARK = re.compile(r"^\*\*" + _LEAD_EMOJI + r"(?:\U0001F1E8\U0001F1E6\s*)?EN\b")
UA_MARK = re.compile(r"^\*\*" + _LEAD_EMOJI + r"(?:\U0001F1FA\U0001F1E6\s*)?UA\b")

def esc(s):
    return htmllib.escape(s, quote=False)


# A leading "**🇨🇦 EN — …**" style language marker. An emoji such as ⚠️ may
# sit in front of the flag and is kept, since it carries meaning of its own.
_PRE   = r"(?P<pre>(?:[\u2190-\u2BFF\U0001F000-\U0001F1E5\U0001F200-\U0001FAFF\uFE0F]\s*)*)"
_FLAG  = r"(?:\U0001F1E8\U0001F1E6\s*|\U0001F1FA\U0001F1E6\s*)?"
MARKER_PLAIN = re.compile(r"^\*\*" + _PRE + _FLAG + r"(?:EN|UA)\.?\*\*\s*(?:[\u2014\u2013-]\s*)?")
MARKER_LEAD  = re.compile(r"^\*\*" + _PRE + _FLAG + r"(?:EN|UA)\s*[\u2014\u2013-]\s*(?P<rest>.+?)\*\*")
# "…EN — Fair winds. / 🇺🇦 UA — Попутного вітру." — a single bold run holding both
MARKER_PAIR  = re.compile(r"^\*\*" + _FLAG + r"EN\s*[\u2014\u2013-]\s*(?P<en>.+?)\s*/\s*"
                          + _FLAG + r"UA\s*[\u2014\u2013-]\s*(?P<ua>.+?)\*\*")


def strip_marker(text):
    """Remove a leading EN/UA language marker, keeping any bold lead-in."""
    m = MARKER_PAIR.match(text)
    if m:
        return ("**" + m.group("en") + "**" + text[m.end():])
    m = MARKER_LEAD.match(text)
    if m:
        pre = m.group("pre") or ""
        return "**" + pre + m.group("rest") + "**" + text[m.end():]
    m = MARKER_PLAIN.match(text)
    if m:
        pre = (m.group("pre") or "").strip()
        rest = text[m.end():]
        return (pre + " " + rest).strip() if pre else rest
    return text


# ------------------------------------------------------------ inline markdown

def inline(text):
    """Convert inline markdown to HTML.

    Code spans are swapped for placeholders first so that emphasis wrapping a
    code span (``**`Wk`**``) still pairs correctly, then restored at the end.
    """
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    s = re.sub(r"`([^`]+)`", stash, text)
    s = esc(s)

    def link(m):
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://", "mailto:")):
            return f'<a href="{htmllib.escape(target)}" target="_blank" rel="noopener">{label}</a>'
        base = target.split("#")[0]
        key = INTERNAL.get(pathlib.PurePosixPath(base).name)
        if key:
            return f'<a href="#/{key}" data-nav="{key}">{label}</a>'
        return label

    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)
    s = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", s)

    s = re.sub(r"\x00(\d+)\x00", lambda m: "<code>" + esc(codes[int(m.group(1))]) + "</code>", s)
    return s

# maps a markdown filename -> app section id, for internal links
INTERNAL = {}
for _, items in SECTIONS:
    for (sid, path, *_rest) in items:
        INTERNAL[pathlib.PurePosixPath(path).name] = sid

# ------------------------------------------------------------ block markdown

# "- [ ] item" and "- ☐ item" both mean a tickable checklist entry
CHECK_ITEM = r"^[-*]\s+(?:\[[ xX]\]|\u2610)\s+"


def split_row(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    return [c.strip() for c in line.split("|")]

def render_blocks(lines):
    """Convert a list of markdown lines into HTML, tagging language runs."""
    html = []
    lang = None          # current language run: 'en' | 'ua' | None
    i = 0
    n = len(lines)

    def tag(kind):
        return f' data-lang="{kind}"' if kind else ""

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # blank
        if not stripped:
            i += 1
            continue

        # horizontal rule -> resets the language run
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            html.append("<hr>")
            lang = None
            i += 1
            continue

        # fenced code (ASCII diagrams) -- never language-tagged
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            html.append('<div class="pre-wrap"><pre>' + esc("\n".join(buf)) + "</pre></div>")
            continue

        # raw HTML passthrough (<details> blocks in the PCOC module)
        if stripped.startswith("<") and not stripped.startswith("<span"):
            html.append(line)
            i += 1
            continue

        # headings -- bilingual, split on ' / '
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            lang = None
            parts = text.split(" / ")
            if len(parts) == 2 and cyr_ratio(parts[1]) > 0.3:
                a = f'<span data-lang="en">{inline(parts[0])}</span>'
                b = f'<span data-lang="ua">{inline(parts[1])}</span>'
                inner = a + '<span class="sep" data-lang="both"> / </span>' + b
            else:
                inner = inline(text)
            lvl = min(level + 1, 5)   # h1 in source -> h2 in app
            # a heading that is purely Cyrillic is the Ukrainian twin of the
            # heading above it, so it belongs to the UA language run
            hl = ' data-lang="ua"' if cyr_ratio(text) > 0.6 else ""
            html.append(f"<h{lvl}{hl}>{inner}</h{lvl}>")
            i += 1
            continue

        # tables
        if stripped.startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            if len(block) >= 2 and re.fullmatch(r"[|\s:-]+", block[1].strip()):
                head, body = block[0], block[2:]
            else:
                head, body = None, block
            raw = " ".join(block)
            tlang = "ua" if cyr_ratio(raw) > 0.35 else None
            t = [f'<div class="table-wrap"{tag(tlang)}><table>']
            if head:
                t.append("<thead><tr>" + "".join(
                    f"<th>{inline(c)}</th>" for c in split_row(head)) + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join(
                    f"<td>{inline(c)}</td>" for c in split_row(r)) + "</tr>")
            t.append("</tbody></table></div>")
            html.append("".join(t))
            continue

        # blockquote -- recurse on the inner content
        if stripped.startswith(">"):
            buf = []
            while i < n and (lines[i].strip().startswith(">") or
                             (lines[i].strip() and buf and not lines[i].strip().startswith(("|", "#", "-", "*")))):
                s = lines[i].strip()
                buf.append(re.sub(r"^>\s?", "", s))
                i += 1
            html.append('<blockquote class="callout">' + render_blocks(buf) + "</blockquote>")
            lang = None
            continue

        # checkbox list
        if re.match(CHECK_ITEM, stripped):
            items = []
            while i < n and re.match(CHECK_ITEM, lines[i].strip()):
                txt = re.sub(CHECK_ITEM, "", lines[i].strip())
                items.append(txt)
                i += 1
            blk = ['<ul class="checklist">']
            for it in items:
                ilang = "ua" if cyr_ratio(it) > 0.5 else None
                blk.append(f'<li{tag(ilang)}><label><input type="checkbox" class="ck">'
                           f"<span>{inline(it)}</span></label></li>")
            blk.append("</ul>")
            html.append("".join(blk))
            continue

        # ordered / unordered list
        m_ul = re.match(r"^[-*]\s+(.*)$", stripped)
        m_ol = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if m_ul or m_ol:
            ordered = bool(m_ol)
            pat = r"^\d+[.)]\s+(.*)$" if ordered else r"^[-*]\s+(.*)$"
            items = []
            while i < n:
                s = lines[i].strip()
                mm = re.match(pat, s)
                if mm:
                    items.append(mm.group(1))
                    i += 1
                elif s and lines[i].startswith(("  ", "\t")) and items:
                    items[-1] += " " + s          # continuation line
                    i += 1
                else:
                    break
            tagname = "ol" if ordered else "ul"
            blk = [f"<{tagname}>"]
            for it in items:
                ilang = "ua" if cyr_ratio(it) > 0.5 else (lang if lang else None)
                blk.append(f"<li{tag(ilang)}>{inline(it)}</li>")
            blk.append(f"</{tagname}>")
            html.append("".join(blk))
            continue

        # paragraph
        buf = [stripped]
        i += 1
        while i < n:
            s = lines[i].strip()
            if not s or s.startswith(("|", "#", ">", "-", "*", "```", "<")) or re.match(r"^\d+[.)]\s", s):
                break
            buf.append(s)
            i += 1
        para = " ".join(buf)
        if EN_MARK.match(para):
            lang = "en"
            para = strip_marker(para)
        elif UA_MARK.match(para):
            lang = "ua"
            para = strip_marker(para)
        plang = lang
        # a paragraph that is overwhelmingly Cyrillic is Ukrainian regardless
        if plang is None and cyr_ratio(para) > 0.5:
            plang = "ua"
        html.append(f"<p{tag(plang)}>{inline(para)}</p>")

    return "".join(html)


def strip_nav(lines):
    """Drop the prev/next navigation lines from the top and bottom of a module."""
    out = [l for l in lines
           if not re.match(r"^\[?[←→]|^\[.*\]\(.*\.md\)\s*\|", l.strip())]
    return out


def render_file(path):
    raw = (ROOT / path).read_text(encoding="utf-8")
    lines = strip_nav(raw.split("\n"))
    return render_blocks(lines), raw

# ------------------------------------------------------------ data extraction

def extract_glossary():
    """Pull EN / pronunciation / UA triples out of the glossary tables."""
    raw = (ROOT / "glossary.md").read_text(encoding="utf-8")
    terms, topic = [], ""
    for line in raw.split("\n"):
        s = line.strip()
        h = re.match(r"^##\s+\d+\.\s+(.*)$", s)
        if h:
            topic = h.group(1).split(" / ")[0].strip()
            continue
        if not s.startswith("|") or re.fullmatch(r"[|\s:-]+", s):
            continue
        cells = split_row(s)
        if len(cells) < 2:
            continue
        en = re.sub(r"[*`]", "", cells[0]).strip()
        if not en or en.lower() in ("english", "english command", "word", "term", "resource", ""):
            continue
        if len(cells) >= 3:
            say, ua = cells[1].strip(), re.sub(r"[*`]", "", cells[2]).strip()
        else:
            say, ua = "", re.sub(r"[*`]", "", cells[1]).strip()
        if say == "—":
            say = ""
        if not ua or ua == "—":
            continue
        # keep only genuine EN → UA pairs
        if cyr_ratio(en) > 0.4 or cyr_ratio(ua) < 0.45:
            continue
        terms.append({"en": en, "say": say, "ua": ua, "topic": topic})
    return terms


def extract_quiz():
    """Pull the 25 PCOC practice questions and their answers."""
    raw = (ROOT / "modules/12-pcoc-exam-prep.md").read_text(encoding="utf-8")
    qs, ans = {}, {}
    in_ans = False
    for line in raw.split("\n"):
        s = line.strip()
        if "<summary>" in s:
            in_ans = True
            continue
        if s.startswith("</details>"):
            in_ans = False
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if not m:
            continue
        num, text = int(m.group(1)), m.group(2)
        if in_ans:
            ans[num] = text
        elif num not in qs:
            qs[num] = text
    out = []
    for k in sorted(qs):
        if k in ans:
            out.append({"n": k, "q": inline(qs[k]), "a": inline(ans[k])})
    return out

# ---------------------------------------------------------------- assemble

def main():
    docs, nav = {}, []
    for group, items in SECTIONS:
        entry = {"group": group, "items": []}
        for (sid, path, ten, tua) in items:
            body, raw = render_file(path)
            docs[sid] = {"t_en": ten, "t_ua": tua, "html": body}
            entry["items"].append({"id": sid, "en": ten, "ua": tua})
        nav.append(entry)

    glossary = extract_glossary()
    quiz = extract_quiz()

    tpl = (ROOT / "web" / "app-template.html").read_text(encoding="utf-8")
    out = (tpl
           .replace("/*__DOCS__*/'{}'",     json.dumps(docs, ensure_ascii=False))
           .replace("/*__NAV__*/'[]'",      json.dumps(nav, ensure_ascii=False))
           .replace("/*__GLOSSARY__*/'[]'", json.dumps(glossary, ensure_ascii=False))
           .replace("/*__QUIZ__*/'[]'",     json.dumps(quiz, ensure_ascii=False))
           .replace("/*__PROGRESS__*/'[]'", json.dumps(PROGRESS_IDS)))

    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  {len(out.encode()):,} bytes")
    print(f"  documents : {len(docs)}")
    print(f"  glossary  : {len(glossary)} terms")
    print(f"  quiz      : {len(quiz)} questions")


if __name__ == "__main__":
    main()
