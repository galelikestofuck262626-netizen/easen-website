# -*- coding: utf-8 -*-
"""Static QA for the built site.  python tools/check_site.py  (exit 1 on errors)

Checks every public HTML page for: broken internal links / images / srcset entries,
title + meta description + canonical + exactly one <h1>, hreflang reciprocity,
duplicate titles, placeholder text, CJK characters leaking into non-Chinese pages,
and that sitemap URLs resolve to files.
"""
import re, sys, json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "https://chinaeasen.com"
SKIP_DIRS = {"admin", "temp-preview", "tools", "src", "node_modules", ".git", "images", "videos", "assets", "data", "js"}
CJK = re.compile(r"[一-鿿]")
ALLOWED_CJK = {"中文", "宜森商业空间家具", "EASEN 网站新询盘", "感谢您联系宜森商业空间家具，我们已收到您的询盘，将在 24 小时内回复。", "询价"}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.imgs, self.h1, self.title, self.desc, self.canon, self.alts, self.text = [], [], 0, None, None, None, {}, []
        self._in_title = False
        self._skip = 0
        self.redirect = False

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("img", "source", "video"):
            if a.get("src"):
                self.imgs.append(a["src"])
            for part in (a.get("srcset") or "").split(","):
                part = part.strip().split(" ")[0]
                if part:
                    self.imgs.append(part)
            if a.get("poster"):
                self.imgs.append(a["poster"])
        if tag == "link":
            rel = a.get("rel", "")
            if rel == "canonical":
                self.canon = a.get("href")
            elif rel == "alternate" and a.get("hreflang"):
                self.alts[a["hreflang"]] = a.get("href")
            elif rel in ("stylesheet", "preload", "icon", "apple-touch-icon", "manifest") and a.get("href"):
                self.imgs.append(a["href"])
        if tag == "script" and a.get("src"):
            self.imgs.append(a["src"])
        if tag == "meta":
            if a.get("name") == "description":
                self.desc = a.get("content")
            if a.get("http-equiv") == "refresh":
                self.redirect = True
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
        if tag == "div" and a.get("data-video"):
            self.imgs.append(a["data-video"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, d):
        if self._in_title:
            self.title = (self.title or "") + d
        elif not self._skip:
            self.text.append(d)


def resolve(page_rel, href):
    if href.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
        return None
    u = urlparse(href)
    if u.scheme in ("http", "https"):
        if u.netloc not in ("chinaeasen.com", "www.chinaeasen.com"):
            return None
        path = u.path
    elif u.scheme:
        return None
    else:
        path = u.path
        if not path:
            return None
        if not path.startswith("/"):
            base = "/" + page_rel.rsplit("/", 1)[0] + "/" if "/" in page_rel else "/"
            path = base + path
    path = unquote(path)
    parts = []
    for seg in path.split("/"):
        if seg == "..":
            parts and parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    rel = "/".join(parts)
    return rel + ("/" if path.endswith("/") and rel else "")


def exists(rel):
    if rel in ("", "/"):
        return (ROOT / "index.html").exists()
    p = ROOT / rel.rstrip("/")
    if rel.endswith("/"):
        return (p / "index.html").exists()
    return p.is_file() or (p / "index.html").exists()


def main():
    errors, warns = [], []
    pages = [p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts[:-1]) & SKIP_DIRS)]
    titles = defaultdict(list)
    meta = {}
    for f in pages:
        rel = f.relative_to(ROOT).as_posix()
        s = f.read_text(encoding="utf-8")
        p = P(); p.feed(s)
        if p.redirect:
            continue
        lang = rel.split("/")[0] if rel.split("/")[0] in ("en", "zh", "fr", "es", "de", "ar") else "root"
        meta[rel] = p
        for h in p.links:
            r = resolve(rel, h)
            if r is not None and not exists(r):
                errors.append("%s: broken link %s" % (rel, h))
        for h in p.imgs:
            r = resolve(rel, h.split("?")[0])
            if r is not None and not exists(r):
                errors.append("%s: missing asset %s" % (rel, h))
        if not p.title or not p.title.strip():
            errors.append("%s: no <title>" % rel)
        if not p.desc:
            errors.append("%s: no meta description" % rel)
        if not p.canon:
            errors.append("%s: no canonical" % rel)
        if p.h1 != 1:
            errors.append("%s: %d <h1>" % (rel, p.h1))
        if re.search(r"XXXX|lorem ipsum|8613800000000", s, re.I) or "TODO" in s:
            errors.append("%s: placeholder text" % rel)
        if lang in ("en", "fr", "es", "de", "ar", "root"):
            txt = " ".join(p.text)
            hits = [m for m in re.findall(r"[一-鿿][一-鿿，。、：；！？（）·—]*", txt) if m.strip() not in ALLOWED_CJK]
            if hits:
                errors.append("%s: Chinese text on %s page: %s" % (rel, lang, " | ".join(sorted(set(h.strip() for h in hits))[:4])))
        if p.title and "noindex" not in s:
            titles[p.title.strip()].append(rel)
    # hreflang reciprocity
    for rel, p in meta.items():
        if not p.alts or not p.canon or not p.canon.startswith(DOMAIN):
            continue
        if not rel.startswith(("en/", "zh/", "fr/", "es/", "de/", "ar/")):
            continue
        for hl, href in p.alts.items():
            r = resolve(rel, href)
            if r is None or not exists(r):
                errors.append("%s: hreflang %s -> missing %s" % (rel, hl, href))
                continue
            tgt = r.rstrip("/") + ("/index.html" if r.endswith("/") or r in ("en", "zh") else "")
            tgt = tgt if tgt in meta else (r + "index.html" if (r + "index.html") in meta else tgt)
            q = meta.get(tgt)
            if q is not None and p.canon not in q.alts.values():
                errors.append("%s: hreflang not reciprocated by %s" % (rel, tgt))
    for t, rels in titles.items():
        langs = defaultdict(list)
        for r in rels:
            langs[r.split("/")[0] if "/" in r else "root"].append(r)
        for L, rs in langs.items():
            if len(rs) > 1 and L != "root":
                warns.append("duplicate title in %s (%d): %s — %s" % (L, len(rs), t, ", ".join(rs[:3])))
    # sitemaps
    for sm in ROOT.glob("sitemap*.xml"):
        for loc in re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8")):
            r = resolve("", loc)
            if r is not None and not exists(r):
                errors.append("%s: dead <loc> %s" % (sm.name, loc))
    print("pages checked: %d" % len(meta))
    for w in warns[:40]:
        print("WARN", w)
    for e in errors[:200]:
        print("ERR ", e)
    print("errors: %d, warnings: %d" % (len(errors), len(warns)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
