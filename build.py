#!/usr/bin/env python3
"""Build the Outerfab site: python3 build.py [--slots] [--strict]

Reads src/, writes dist/. Standard library only, so Cloudflare Pages can run it
(build command `python3 build.py`, output directory `dist`, root directory `website`).

  --slots   render labelled image-slot placeholders for photographs that do not exist yet
  --strict  exit non-zero on warnings (dead internal links, budget overruns)
  --noindex private preview: noindex on every page, X-Robots-Tag header, robots.txt disallows all, no sitemap.
            Also on when NOINDEX=1. Never use it for the live site (see DEPLOY.md).

Configuration lives in site.json (public values only: form IDs and form actions).
Environment overrides: SITE_URL, FORMSPARK_FORM_ID, CF_BEACON_TOKEN.
"""
import datetime, gzip, hashlib, html, json, os, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC, DIST = ROOT / "src", ROOT / "dist"
LOGO = ROOT / "brand" / "logo" / "logo-horizontal-dark.svg"
CONF = json.loads((ROOT / "site.json").read_text()) if (ROOT / "site.json").exists() else {}
SITE_URL = os.environ.get("SITE_URL", "https://outerfab.com").rstrip("/")
FORMSPARK = os.environ.get("FORMSPARK_FORM_ID", CONF.get("formspark_id", ""))
SZOSS_FORM = os.environ.get("SZOSS_FORMSPARK_FORM_ID", CONF.get("szoss_formspark_id", ""))
NEWSLETTER_FORM = os.environ.get("NEWSLETTER_FORMSPARK_FORM_ID", CONF.get("newsletter_formspark_id", ""))
BEACON = os.environ.get("CF_BEACON_TOKEN", "")
SLOTS = "--slots" in sys.argv
STRICT = "--strict" in sys.argv
NOINDEX = "--noindex" in sys.argv or os.environ.get("NOINDEX") == "1"
TODAY = datetime.date.today().isoformat()
warnings = []

# Photograph slots: file name in src/assets/img/, pixel size, alt text, and the brief for whoever shoots it.
SLOT_SPECS = {
    "hero": (1800, 1200, "A wire-bonded die on a printed circuit board, viewed close enough to see the bond wires.",
             "hero: an actual Outerfab wire-bonded die on its printed circuit board, close view showing bond wires and board pads; 3:2, 1800 x 1200; no generated imagery"),
    "die_macro": (1200, 1200, "A single custom die seen from above on a black background, pads and edge sharp.",
                  "die macro: one custom die, top down, filling 70% of the frame on black; 1:1, 1200 x 1200; pads and die edge sharp"),
    "bonded_board": (1600, 900, "A finished chip-on-board with bond wires visible under raking light and clear glob-top.",
                     "bonded board: a finished board on black, wires visible under raking light, glob-top clear; 16:9, 1600 x 900; serial number legible if possible"),
    "wafer_detail": (1500, 1000, "A diced wafer on tape showing singulated die.",
                     "wafer detail: close crop of a diced wafer on tape or a waffle pack, singulated die visible; 3:2, 1500 x 1000"),
    "tape_reel": (1500, 1000, "Die in the pockets of carrier tape, seen from above.",
                  "tape and reel: die in carrier tape pockets, top down; 3:2, 1500 x 1000"),
    "test_setup": (1500, 1000, "The test board with a panel on it.",
                   "test setup: the test board with a panel on it; 3:2, 1500 x 1000; no faces, no untidy bench"),
}
RATIO = {"hero": "3-2", "die_macro": "1-1", "bonded_board": "16-9", "wafer_detail": "3-2", "tape_reel": "3-2", "test_setup": "3-2"}
CAPTIONS = {
    "hero": "", "die_macro": "A custom die, top view.", "bonded_board": "A bonded board with clear glob-top.",
    "wafer_detail": "Singulated die on tape.", "tape_reel": "Die in carrier tape.", "test_setup": "The test board.",
}


def parse(text):
    """Split '---' front matter (key: value lines) from the body."""
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def fill(template, values, where):
    def sub(match):
        key = match.group(1)
        if key not in values:
            raise SystemExit("unresolved placeholder {{%s}} in %s" % (key, where))
        return values[key]
    return re.sub(r"\{\{(\w+)\}\}", sub, template)


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def logo_svg():
    svg = LOGO.read_text().strip()
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg, count=2)  # width/height attributes break CSS sizing
    return svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)


def photo(slot, wrap=True):
    """A real photograph if one exists, a labelled placeholder with --slots, otherwise nothing."""
    w, h, alt, brief = SLOT_SPECS[slot]
    img = SRC / "assets" / "img"
    found = {ext: (img / ("%s.%s" % (slot, ext))).exists() for ext in ("avif", "webp", "jpg")}
    if any(found.values()):
        srcs = "".join('<source type="image/%s" srcset="/assets/img/%s.%s">' % ("jpeg" if e == "jpg" else e, slot, e)
                       for e in ("avif", "webp") if found[e])
        fallback = "jpg" if found["jpg"] else ("webp" if found["webp"] else "avif")
        eager = 'fetchpriority="high"' if slot == "hero" else 'loading="lazy" decoding="async"'
        pic = '<picture>%s<img src="/assets/img/%s.%s" width="%d" height="%d" alt="%s" %s></picture>' % (srcs, slot, fallback, w, h, html.escape(alt), eager)
    elif SLOTS:
        pic = '<div class="slot r-%s" aria-hidden="true">image slot<br>%s</div>' % (RATIO[slot], html.escape(brief).replace(": ", "<br>", 1))
    else:
        return ""
    cap = CAPTIONS[slot]
    return '<figure class="photo">%s%s</figure>' % (pic, ("<figcaption>%s</figcaption>" % cap) if cap else "") if wrap else pic


def hero_media():
    p = photo("hero", wrap=False)
    if p:
        return p
    fig = (SRC / "partials" / "fig-hero.svg").read_text().strip()
    return '<figure class="fig-dark">%s<figcaption>A bare die (orange) wire-bonded, pad to finger, onto a board.</figcaption></figure>' % fig


def crumbs_for(path, by_path):
    """[(name, url)] from Home to this page, skipping levels that have no page."""
    parts = [p for p in path.strip("/").split("/") if p]
    trail = [("Home", "/")]
    for i in range(1, len(parts) + 1):
        p = "/" + "/".join(parts[:i]) + "/"
        if p in by_path:
            trail.append((by_path[p]["name"], p))
    return trail


# Structured data. Every person and organisation named on the site is defined once in entities() and referred
# to by @id everywhere else, so the same thing is the same node on every page (entity consolidation).
# @ids of entities use the production domain even in preview builds, so they never change with the build host.
ENTITY_BASE = "https://outerfab.com"
ORG_ID = ENTITY_BASE + "/#org"
SZOSS_EVENT_ID = ENTITY_BASE + "/events/szoss/#event"


# Entities that already have a canonical @id elsewhere keep it, so other sites and this one describe the same node.
CANONICAL_IDS = {"org": ORG_ID, "szoss": SZOSS_EVENT_ID,
                 "stephan-boekelmann": "https://maxclerkwell.tech/#person",  # also used by nabla-b.engineering
                 "stuart-childs": "https://saladss.github.io/#person"}


def eid(slug):
    return CANONICAL_IDS.get(slug, ENTITY_BASE + "/#" + slug)


def ref(slug):
    return {"@id": eid(slug)}


def entities():
    """slug -> (node, names to look for in page text). Facts come from the pages of this site."""
    def org(slug, name, url, **extra):
        return dict({"@type": "Organization", "@id": eid(slug), "name": name, "url": url, "sameAs": [url]}, **extra)
    return {
        "org": ({"@type": "Organization", "@id": ORG_ID, "name": "Outerfab", "url": ENTITY_BASE + "/",
                 "logo": {"@type": "ImageObject", "url": ENTITY_BASE + "/assets/logo-512.png", "width": 512, "height": 512},
                 "description": "Post-fab services for small silicon batches, including die preparation, chip-on-board bonding, optional testing, packing and fulfilment.",
                 "email": "bonding@outerfab.com",
                 "contactPoint": {"@type": "ContactPoint", "contactType": "sales and technical enquiries", "email": "bonding@outerfab.com", "availableLanguage": "en"},
                 "address": {"@type": "PostalAddress", "addressLocality": "Shenzhen", "addressCountry": "CN"},
                 "founder": [ref("giovanni-schirinzi"), ref("stuart-childs"), ref("stephan-boekelmann")],
                 "areaServed": ["Europe", "United States", "Asia-Pacific"],
                 "sameAs": ["https://github.com/outerfab"]}, []),
        "giovanni-schirinzi": ({"@type": "Person", "@id": eid("giovanni-schirinzi"), "name": "Giovanni Schirinzi",
                                "jobTitle": "Co-founder", "description": "Supply chain, product development and marketing.",
                                "email": "giovanni@outerfab.com", "worksFor": ref("org"), "url": ENTITY_BASE + "/about/"}, ["Giovanni Schirinzi"]),
        "stuart-childs": ({"@type": "Person", "@id": eid("stuart-childs"), "name": "Stuart Childs",
                           "jobTitle": ["Co-founder, Outerfab", "Production Manager, Tiny Tapeout"],
                           "description": "Production, operations and technical project management.",
                           "email": "stuart@outerfab.com", "worksFor": [ref("org"), ref("tiny-tapeout")], "url": "https://saladss.github.io/",
                           "sameAs": ["https://www.linkedin.com/in/pleased", ENTITY_BASE + "/about/"]}, ["Stuart Childs"]),
        "stephan-boekelmann": ({"@type": "Person", "@id": eid("stephan-boekelmann"), "name": "Stephan Bökelmann",
                                "alternateName": ["Stephan Boekelmann", "MaxClerkwell"], "jobTitle": "Co-founder",
                                "description": "Wire bonding, process development and tooling. Physicist, engineer and KiCad community contributor.",
                                "email": "stephan@outerfab.com", "worksFor": ref("org"), "url": "https://maxclerkwell.tech/",
                                "sameAs": ["https://www.wikidata.org/wiki/Q141502495", "https://orcid.org/0000-0002-2119-0064",
                                           "https://github.com/maxclerkwell", ENTITY_BASE + "/about/"]}, ["Stephan Bökelmann"]),
        "tim-ansell": ({"@type": "Person", "@id": eid("tim-ansell"), "name": "Tim Ansell", "alternateName": "mithro",
                        "jobTitle": "Founder, wafer.space", "worksFor": ref("wafer-space"),
                        "sameAs": ["https://mith.ro", "https://github.com/mithro"]}, ["Tim Ansell"]),
        "biwei-xie": ({"@type": "Person", "@id": eid("biwei-xie"), "name": "Biwei Xie",
                       "jobTitle": ["Associate Professor", "ECOS Open Silicon lead"], "worksFor": ref("ict-cas")}, ["Biwei Xie"]),
        "tiny-tapeout": (org("tiny-tapeout", "Tiny Tapeout", "https://tinytapeout.com/"), ["Tiny Tapeout"]),
        "wafer-space": (org("wafer-space", "wafer.space", "https://wafer.space/", founder=ref("tim-ansell")), ["wafer.space"]),
        "crowd-supply": (org("crowd-supply", "Crowd Supply", "https://www.crowdsupply.com/"), ["Crowd Supply"]),
        "chaihuo": (org("chaihuo", "Chaihuo Maker Space", "https://www.chaihuo.org/", alternateName="柴火创客空间"), ["Chaihuo"]),
        "ict-cas": ({"@type": "Organization", "@id": eid("ict-cas"), "name": "Institute of Computing Technology, Chinese Academy of Sciences",
                     "alternateName": "ICT, CAS"}, ["Institute of Computing Technology"]),
        "szoss": ({"@type": "Event", "@id": SZOSS_EVENT_ID, "name": "1st Shenzhen Open Source Silicon Meetup",
                   "alternateName": ["SZOSS", "首届深圳开源芯片交流会"],
                   "startDate": "2026-11-11T16:00:00+08:00", "endDate": "2026-11-11T19:00:00+08:00",
                   "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                   "eventStatus": "https://schema.org/EventScheduled", "url": ENTITY_BASE + "/events/szoss/",
                   "description": "The first Shenzhen Open Source Silicon Meetup: an afternoon of technical exchange, silicon demos and conversation with researchers, open-source contributors and Shenzhen's hardware community.",
                   "image": ENTITY_BASE + "/assets/szoss/social.png", "inLanguage": "en",
                   "location": {"@type": "Place", "name": "Chaihuo Maker Space", "address": {"@type": "PostalAddress", "addressLocality": "Shenzhen", "addressRegion": "Guangdong", "addressCountry": "CN"}},
                   "organizer": ref("org"), "sponsor": ref("chaihuo"),
                   "performer": [ref("tim-ansell"), ref("biwei-xie"), ref("stephan-boekelmann"), ref("stuart-childs")],
                   "sameAs": ["https://events.outerfab.com/events/9e3aaaed-657f-4bb0-8c0d-db0ea9d1b2c3/"]}, ["Shenzhen Open Source Silicon Meetup", "SZOSS"]),
    }


def id_refs(node):
    """All @id references (objects that hold nothing but an @id) inside a node."""
    if isinstance(node, dict):
        if list(node) == ["@id"]:
            yield node["@id"]
        else:
            for v in node.values():
                yield from id_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from id_refs(v)


def schema_blocks(meta, body, canonical, trail, where=""):
    kinds = [k.strip() for k in meta.get("schema", "").split(",") if k.strip()]
    ents = entities()
    by_id = {node["@id"]: (slug, node) for slug, (node, _) in ents.items()}
    site_id, page_id = SITE_URL + "/#site", canonical + "#page"
    updated = meta.get("updated")
    text = strip_tags(body)
    graph, main = [], []

    if "event" in kinds:
        main.append(ref("szoss"))
    if "organization" in kinds or "about" in kinds:
        main.append(ref("org"))
    if "service" in kinds:
        graph.append({"@type": "Service", "@id": canonical + "#service", "name": meta.get("service_type", meta["title"]),
                      "serviceType": meta.get("service_type", ""), "description": meta.get("service_description", meta["description"]),
                      "provider": ref("org"), "url": canonical})
        main.append({"@id": canonical + "#service"})
    if "techarticle" in kinds:
        graph.append({"@type": "TechArticle", "@id": canonical + "#article", "headline": meta.get("name", meta["title"]),
                      "description": meta["description"],
                      **({"datePublished": meta["published"]} if meta.get("published") else {}),
                      **({"dateModified": updated} if updated else {}),
                      "author": ref("org"), "publisher": ref("org"),
                      "mainEntityOfPage": {"@id": page_id}, "inLanguage": "en"})
        main.append({"@id": canonical + "#article"})
    if "glossary" in kinds:
        terms = re.findall(r'<dt id="([^"]+)">(.*?)</dt>\s*<dd>(.*?)</dd>', body, re.S)
        graph.append({"@type": "DefinedTermSet", "@id": canonical + "#terms", "name": "Chip-on-board glossary", "publisher": ref("org"), "hasDefinedTerm": [
            {"@type": "DefinedTerm", "name": strip_tags(t), "description": strip_tags(d), "url": canonical + "#" + i,
             "inDefinedTermSet": {"@id": canonical + "#terms"}} for i, t, d in terms]})
        main.append({"@id": canonical + "#terms"})

    # the page itself: every page gets one
    types = [t for k, t in (("collection", "CollectionPage"), ("contact", "ContactPage"), ("about", "AboutPage")) if k in kinds] or ["WebPage"]
    page = {"@type": types, "@id": page_id, "name": meta.get("name", meta["title"]), "description": meta["description"],
            "url": canonical, "isPartOf": {"@id": site_id}, "inLanguage": "en", "publisher": ref("org")}
    if meta.get("published"):
        page["datePublished"] = meta["published"]
    if updated:
        page["dateModified"] = updated
    if "faq" in kinds:
        items = re.findall(r"<details><summary>(.*?)</summary>\s*<p>(.*?)</p></details>", body, re.S)
        page["@type"] = types + ["FAQPage"]
        page["mainEntity"] = [{"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in items]
        if main:
            page["about"] = main if len(main) > 1 else main[0]
    elif main:
        page["mainEntity"] = main if len(main) > 1 else main[0]
    if len(page["@type"]) == 1:
        page["@type"] = page["@type"][0]
    if meta["path"] == "/":
        graph.append({"@type": "ImageObject", "@id": SITE_URL + "/#home-photo", "contentUrl": SITE_URL + "/assets/img/home-wafer-1280.webp",
                      "width": 1280, "height": 721, "caption": "Close-up of the wafer.space Run 1 wafer with multiple silicon designs",
                      "creator": ref("tim-ansell"), "creditText": "Tim Ansell", "copyrightNotice": "Tim Ansell, wafer.space Run 1",
                      "license": "https://creativecommons.org/licenses/by/4.0/", "acquireLicensePage": "https://wafer.space/",
                      "about": ref("wafer-space")})
        page["primaryImageOfPage"] = {"@id": SITE_URL + "/#home-photo"}
    main_ids = {m["@id"] for m in main}
    mentions = [ref(slug) for slug, (node, names) in ents.items()
                if node["@id"] not in main_ids and any(n in text for n in names)]
    if mentions:
        page["mentions"] = mentions
    if len(trail) > 1:
        graph.append({"@type": "BreadcrumbList", "@id": canonical + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE_URL + u} for i, (n, u) in enumerate(trail)]})
        page["breadcrumb"] = {"@id": canonical + "#breadcrumb"}
    graph.insert(0, page)
    graph.insert(0, {"@type": "WebSite", "@id": site_id, "name": "Outerfab", "url": SITE_URL + "/", "publisher": ref("org"), "inLanguage": "en"})

    # pull in every entity that is referred to, so each @id is defined in the same document
    have = {n["@id"] for n in graph if "@id" in n}
    todo = [i for n in graph for i in id_refs(n)]
    while todo:
        i = todo.pop()
        if i in have or i not in by_id:
            continue
        slug, node = by_id[i]
        if slug == "org" and "organization" not in kinds and "about" not in kinds:
            node = {k: node[k] for k in ("@type", "@id", "name", "url", "logo", "sameAs")}  # short form away from home and about
        graph.append(node)
        have.add(i)
        todo.extend(id_refs(node))
    ids = [n["@id"] for n in graph if "@id" in n]
    for i in sorted(set(ids)):
        if ids.count(i) > 1:
            warnings.append("%s: structured data defines %s twice" % (where, i))
    for i in sorted({i for n in graph for i in id_refs(n)} - set(ids)):
        warnings.append("%s: structured data refers to %s, which is not defined on the page" % (where, i))
    return '<script type="application/ld+json">%s</script>' % json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def crumbs_html(trail):
    if len(trail) < 2:
        return ""
    items = "".join('<li><a href="%s">%s</a></li>' % (u, html.escape(n)) for n, u in trail[:-1])
    items += '<li aria-current="page">%s</li>' % html.escape(trail[-1][0])
    return '<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol>%s</ol></div></nav>' % items


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    shutil.copytree(SRC / "assets", DIST / "assets", dirs_exist_ok=True)
    event_assets = {}
    for asset in sorted((SRC / "assets" / "szoss").glob("*")):
        if asset.is_file():
            version = hashlib.sha256(asset.read_bytes()).hexdigest()[:8]
            old = "/assets/szoss/" + asset.name
            new = "/assets/szoss/" + asset.stem + "." + version + asset.suffix
            (DIST / old.lstrip("/")).rename(DIST / new.lstrip("/"))
            event_assets[old] = new

    css = (SRC / "assets" / "style.css").read_text()
    css_hash = hashlib.md5(css.encode()).hexdigest()[:8]
    css_file = "style.%s.css" % css_hash
    (DIST / "assets" / "style.css").rename(DIST / "assets" / css_file)
    quote_script = (SRC / "assets" / "quote-form.js").read_bytes()
    quote_script_file = "quote-form.%s.js" % hashlib.sha256(quote_script).hexdigest()[:8]
    (DIST / "assets" / "quote-form.js").rename(DIST / "assets" / quote_script_file)
    gz = len(gzip.compress(css.encode(), 9))
    if gz > 20 * 1024:
        warnings.append("CSS is %.1f KB gzipped, budget is 20 KB" % (gz / 1024))
    shutil.copy(SRC / "assets" / "favicon.ico", DIST / "favicon.ico")

    layout = (SRC / "layout.html").read_text()
    header_t = (SRC / "partials" / "header.html").read_text()
    footer_t = (SRC / "partials" / "footer.html").read_text()
    common = {"site_url": SITE_URL, "css_file": css_file, "logo_svg": logo_svg(), "hero_media": hero_media(),
              "szoss_action": "https://submit-form.com/" + SZOSS_FORM if SZOSS_FORM else "",
              "szoss_disabled": "" if SZOSS_FORM else "disabled",
              "szoss_availability": "" if SZOSS_FORM else '<p class="event-notice">Registration opens soon. Please check back shortly.<br><span lang="zh-Hans">报名即将开放，请稍后再来查看。</span></p>',
              "newsletter_action": "https://submit-form.com/" + NEWSLETTER_FORM if NEWSLETTER_FORM else "",
              "newsletter_disabled": "" if NEWSLETTER_FORM else "disabled",
              "newsletter_availability": "" if NEWSLETTER_FORM else "Signup is not available yet. Please try again later.",
              "contact_action": "https://submit-form.com/" + FORMSPARK,
              "contact_redirect": SITE_URL + "/contact/thanks/"}
    if not FORMSPARK:
        warnings.append("no Formspark form ID in site.json: contact forms will not submit")
    for slot in SLOT_SPECS:
        common["photo_" + slot] = photo(slot)
    for f in sorted((SRC / "partials").glob("*.html")):
        if f.stem not in ("header", "footer"):
            common[f.stem.replace("-", "_")] = fill(f.read_text(), common, f.name)
    for f in sorted((SRC / "partials").glob("fig-*.svg")):
        common["fig_" + f.stem[4:].replace("-", "_")] = f.read_text().strip()
    analytics = ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{"token": "%s"}\'></script>' % BEACON) if BEACON else ""

    pages = []
    for f in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse(f.read_text())
        for req in ("title", "description", "path"):
            if req not in meta:
                raise SystemExit("%s: front matter needs %s" % (f.name, req))
        meta.setdefault("name", meta["title"].split("—")[0].strip())
        path = meta["path"]
        canonical = SITE_URL + (path if path.endswith("/") or path.endswith(".html") else path + "/")
        pages.append(dict(meta=meta, body=body, path=path, canonical=canonical, file=f.name))
    by_path = {p["path"]: p["meta"] for p in pages}

    redirects = CONF.get("redirects", [])
    redirect_lines = []
    redirect_sources = set()
    for item in redirects:
        source, target = item["from"], item["to"]
        target_path, _, fragment = target.partition("#")
        if source.rstrip("/") in redirect_sources or source in by_path:
            warnings.append("redirect source duplicates a route: %s" % source)
        redirect_sources.add(source.rstrip("/"))
        if target_path not in by_path:
            warnings.append("redirect target is not built: %s" % target)
        redirect_lines.append("%s %s 301" % (source, target))
        if source.endswith("/"):
            redirect_lines.append("%s %s 301" % (source.rstrip("/"), target))
        else:
            redirect_lines.append("%s/ %s 301" % (source, target))
    (DIST / "_redirects").write_text("\n".join(redirect_lines) + "\n")
    # GitHub Pages ignores _redirects, so every redirect also gets a small page that forwards the visitor.
    for item in redirects:
        target = SITE_URL + item["to"]
        stub = DIST / item["from"].strip("/") / "index.html"
        stub.parent.mkdir(parents=True, exist_ok=True)
        stub.write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Moved</title>'
                        '<link rel="canonical" href="%s"><meta name="robots" content="noindex,follow">'
                        '<meta http-equiv="refresh" content="0; url=%s"></head>'
                        '<body><p>This page has moved to <a href="%s">%s</a>.</p></body></html>\n' % (target, target, target, html.escape(item["to"])))

    for p in pages:
        meta, body, path, canonical = p["meta"], p["body"], p["path"], p["canonical"]
        light = meta.get("theme") == "light"
        noindex = meta.get("noindex") == "true"
        top = path.strip("/").split("/")[0]
        cur = {"cur_" + k: (' aria-current="page"' if top == k else "") for k in ("services", "resources", "pricing", "about", "news")}
        trail = [] if (noindex or path == "/") else crumbs_for(path, by_path)
        body_html = fill(body, common, p["file"])
        body_html = body_html.replace("/assets/quote-form.js", "/assets/" + quote_script_file)
        body_html = re.sub(r'<div class="table-wrap([^\"]*)">', lambda m: '<div class="table-wrap%s" tabindex="0" role="region" aria-label="Scrollable table"><span class="scroll-cue">If columns are out of view, scroll horizontally</span>' % m.group(1), body_html)
        body_html = body_html.replace('<figure class="fig">', '<figure class="fig" tabindex="0" role="region" aria-label="Scrollable technical diagram"><span class="scroll-cue diagram-scroll-cue">Scroll horizontally to see the full diagram</span>')
        header = fill(header_t, dict(common, **cur), "header")
        footer = fill(footer_t, common, "footer")
        event = meta.get("schema") == "event" or meta.get("event") == "true"
        if event:
            header = common["event_header"]
            if path != "/events/szoss/":
                header = header.replace('href="#', 'href="/events/szoss/#')
        page = fill(layout, dict(
            common, robots=("noindex,nofollow" if NOINDEX else "noindex,follow" if noindex else "index,follow,max-image-preview:large"),
            title=html.escape(meta["title"]), description=html.escape(meta["description"]), canonical=canonical,
            color_scheme="light" if light else "dark", og_type=meta.get("type", "website"),
            schema=schema_blocks(meta, body, canonical, trail, p["file"]), body_class="theme-light" if light else "theme-dark",
            page_head=('<link rel="stylesheet" href="/assets/szoss/event.css">' if event else ""),
            header=header, crumbs=crumbs_html(trail), body=body_html, footer=footer, analytics=analytics), p["file"])
        if event:
            page = page.replace('/assets/og-image.png', '/assets/szoss/social.png').replace('Outerfab post-fab services for small silicon batches', 'SZOSS, 11 November 2026, Chaihuo Maker Space, Shenzhen')
        for old, new in event_assets.items():
            page = page.replace(old, new)
        out = DIST / meta.get("output", (path.strip("/") + "/index.html") if path != "/" else "index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        p.update(out=out, html=page, noindex=noindex)
        # per-page checks
        if len(re.findall(r"<h1[ >]", page)) != 1:
            warnings.append("%s: needs exactly one h1" % p["file"])
        if len(meta["description"]) > 160:
            warnings.append("%s: description is %d chars (max 160)" % (p["file"], len(meta["description"])))
        if len(meta["title"]) > 65:
            warnings.append("%s: title is %d chars (aim for 65 or fewer)" % (p["file"], len(meta["title"])))
        ids = re.findall(r'\sid="([^"]+)"', page)
        if len(ids) != len(set(ids)):
            warnings.append("%s: duplicate ids" % p["file"])
        for img in re.findall(r"<img\b[^>]*>", page):
            if " alt=" not in img or " width=" not in img or " height=" not in img:
                warnings.append("%s: img needs alt, width and height" % p["file"])
        for m in re.finditer(r"\[confirm\]", body):
            warnings.append("%s: '[confirm]' left in the page" % p["file"])
        if re.search(r"<h[2-4][^>]*>\s*</h", body):
            warnings.append("%s: empty heading" % p["file"])

    indexable = [p for p in pages if not p["noindex"]]
    built = {p["path"] for p in pages}
    # sitemap, robots, llms.txt
    urls = "".join("<url><loc>%s</loc>%s</url>" % (p["canonical"], "<lastmod>%s</lastmod>" % p["meta"]["updated"] if p["meta"].get("updated") else "") for p in indexable)
    if not NOINDEX:
        (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls)
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n" if NOINDEX else "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)
    lines = ["# Outerfab", "", "> Post-fab services for small silicon batches, including dicing, chip-on-board wire bonding, optional electrical testing, packing and fulfilment.", ""]
    groups = [("Services", "/services/"), ("Resources", "/resources/")]
    used = set()
    for title, prefix in groups:
        members = [p for p in indexable if p["path"].startswith(prefix)]
        lines += ["## " + title, ""] + ["- [%s](%s): %s" % (p["meta"]["name"], p["canonical"], p["meta"]["description"]) for p in members] + [""]
        used |= {p["path"] for p in members}
    rest = [p for p in indexable if p["path"] not in used]
    lines += ["## Company", ""] + ["- [%s](%s): %s" % (p["meta"]["name"], p["canonical"], p["meta"]["description"]) for p in rest]
    if not NOINDEX:
        (DIST / "llms.txt").write_text("\n".join(lines) + "\n")
    # Cloudflare Pages headers
    (DIST / "_headers").write_text(
        "/*\n" + ("  X-Robots-Tag: noindex, nofollow\n" if NOINDEX else "") + "  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: DENY\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
        "  Content-Security-Policy: default-src 'self'; script-src 'self' https://static.cloudflareinsights.com; "
        "connect-src 'self' https://cloudflareinsights.com https://submit-form.com; img-src 'self' data:; style-src 'self'; font-src 'self'; "
        "form-action 'self' https://submit-form.com; base-uri 'self'; frame-ancestors 'none'\n"
        "/assets/*\n  Cache-Control: public, max-age=604800\n/assets/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n")

    # internal link check
    pending = set()
    for p in pages:
        for asset in re.findall(r'(?:href|src|srcset)="(/assets/[^" ]+)', p["html"]):
            if not (DIST / asset.lstrip("/")).is_file():
                warnings.append("%s: missing local asset %s" % (p["file"], asset))
        for frag in re.findall(r'href="#([^" ]+)"', p["html"]):
            if ('id="%s"' % frag) not in p["html"]:
                warnings.append("%s: local fragment #%s has no target" % (p["file"], frag))
        for href in re.findall(r'href="(/[^"#?]*)', p["html"]):
            if href.startswith("/assets/") or href in built or href.endswith((".ico", ".txt", ".xml")):
                continue
            pending.add(href)
        for href, frag in re.findall(r'href="(/[^"#?]*)#([^"]+)"', p["html"]):
            target = next((q for q in pages if q["path"] == href), None)
            if target and ('id="%s"' % frag) not in target["html"]:
                warnings.append("%s: link to %s#%s has no target" % (p["file"], href, frag))
    pending = sorted(pending)
    for item in redirects:
        path, _, fragment = item["to"].partition("#")
        target = next((p for p in pages if p["path"] == path), None)
        if target and fragment and ('id="%s"' % fragment) not in target["html"]:
            warnings.append("redirect fragment has no target: %s" % item["to"])

    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    if NOINDEX:
        print("PRIVATE PREVIEW BUILD: noindex on every page, robots.txt disallows all, no sitemap. Do not publish this to the live domain.")
    print("built %d page(s) into %s (%d KB total, CSS %.1f KB, fonts %.1f KB)" % (
        len(pages), DIST.relative_to(ROOT.parent), total // 1024, len(css.encode()) / 1024,
        sum(f.stat().st_size for f in (DIST / "assets" / "fonts").glob("*.woff2")) / 1024))
    for w in warnings:
        print("warning:", w)
    if pending:
        print("links to pages not built yet (%d): %s" % (len(pending), ", ".join(pending)))
    if STRICT and (warnings or pending):
        sys.exit(1)


if __name__ == "__main__":
    main()
