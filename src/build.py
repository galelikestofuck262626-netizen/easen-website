# -*- coding: utf-8 -*-
"""
EASEN static site builder.

    python src/build.py            # full build (pages, images, sitemaps)
    python src/build.py --no-img   # skip image derivative generation (uses existing ones)

Source of truth:
    src/i18n/<lang>.json      UI + page copy (en is the fallback for missing keys)
    src/templates/*.html      Jinja2 templates
    src/assets/site.css|js    design system + runtime (copied to /assets/)
    src/content/              original long-form sources (landing pages, insights)
    data/*.json               products / cases / settings (edited by /admin/)

Outputs (all committed): /<lang>/..., root English entry pages (canonical -> /en/),
/assets/, /images/_r/ (resized webp), sitemaps, robots.txt.
The legacy generators (gen_i18n.py / seo_build.py) are retired; do not run them.
"""
import argparse, copy, hashlib, html, json, os, re, shutil, sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DOMAIN = "https://chinaeasen.com"
LANGS = ["en", "zh", "fr", "es", "de", "ar"]
CATS = ["restaurant", "cafe", "outdoor", "hotel"]
TYPES = ["chair", "booth", "table"]
OWN_CASES = {"1006", "1007", "1008", "1009"}
YEAR = date.today().year
TODAY = date.today().isoformat()

S = {
    "email": "chinaeasen@outlook.com",
    "phone": "+86 150 1164 1080",
    "tel": "+8615011641080",
    "wa": "8615011641080",
    "wechat": "easen_furniture",
    "domain": DOMAIN,
}

# ---- curated imagery (all first-party files already in /images) ----
HERO = "/images/cases/beijing-sichuan/cover1006-2.jpg"
# home hero photo wall: 3 drifting columns of first-party project shots (portrait)
HERO_WALL = [
    ["/images/cases/beijing-sichuan/cover1006-2.jpg", "/images/cases/guangzhou-chio/cover1007-14.jpg", "/images/cases/hanzhong-hotpot/cover1009-1.jpg", "/images/cases/hangzhou-sichuan/cover1008-2.jpg"],
    ["/images/cases/guangzhou-chio/cover1007-11.jpg", "/images/cases/beijing-sichuan/cover1006-5.jpg", "/images/cases/hanzhong-hotpot/cover1009-4.jpg", "/images/cases/guangzhou-chio/cover1007-8.jpg"],
    ["/images/cases/hangzhou-sichuan/cover1008-1.jpg", "/images/cases/hanzhong-hotpot/cover1009-3.jpg", "/images/cases/guangzhou-chio/cover1007-15.jpg", "/images/cases/beijing-sichuan/cover1006-8.jpg"],
]
INTRO_IMG = "/images/factory/factory-13.jpg"
CTA_IMG = "/images/cases/beijing-sichuan/cover1006-6.jpg"
ABOUT_HERO = "/images/factory/factory-9.jpg"
ABOUT_STORY = "/images/factory/factory-12.jpg"
CONTACT_IMG = "/images/cases/guangzhou-chio/cover1007-4.jpg"
FACTORY_POSTER = "/images/factory/factory-11.jpg"
FACTORY_POSTER2 = "/images/factory/factory-3.jpg"
FACTORY_STRIP = ["/images/factory/factory-2.jpg", "/images/factory/factory-6.jpg", "/images/factory/factory-8.jpg", "/images/factory/factory-10.jpg"]
FACTORY_ALL = ["/images/factory/factory-%d.jpg" % i for i in (2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13)]
AI_BEFORE = "/images/services/restaurant.jpg"
AI_AFTER = "/images/cases/hangzhou-sichuan/cover1008.jpg"
CAT_HERO = {
    "restaurant": "/images/cases/hangzhou-sichuan/cover1008-1.jpg",
    "cafe": "/images/cases/guangzhou-chio/cover1007-4.jpg",
    "outdoor": "/images/services/outdoor.jpg",
    "hotel": "/images/services/hotel.jpg",
}
CAT_IMG = dict(CAT_HERO)
HOTEL_IMGS = ["/images/services/hotel.jpg", "/images/cases/guangzhou-chio/cover1007-5.jpg", "/images/cases/guangzhou-chio/cover1007-8.jpg", "/images/services/cafe.jpg"]
FEATURE_IDX = {"1006": [0, 2, 7], "1007": [4, 1, 5], "1009": [0, 2, 3], "1008": [0, 1, 2]}
INSIGHTS = [
    {"key": "project", "file": "insight-project-cafe.html", "img": "/images/cases/cafe/cafe-4.jpg"},
    {"key": "quality", "file": "insight-quality-compliance.html", "img": "/images/factory/factory-4.jpg"},
    {"key": "guide", "file": "insight-furniture-guide.html", "img": "/images/cases/beijing-sichuan/cover1006-8.jpg"},
]
INSIGHT_LANGS = ["en", "zh"]
LANDING = {
    # file: (group, kicker, hero image)
    "commercial-furniture-manufacturer-china.html": ("Manufacturing", "Manufacturer", "/images/factory/factory-13.jpg"),
    "contract-furniture-manufacturer.html": ("Manufacturing", "Contract / FF&E", "/images/factory/factory-12.jpg"),
    "hospitality-furniture-china.html": ("Manufacturing", "Hospitality", "/images/cases/guangzhou-chio/cover1007-3.jpg"),
    "custom-booth-seating.html": ("Products", "Booth seating", "/images/cases/beijing-sichuan/cover1006-7.jpg"),
    "banquette-seating-manufacturer.html": ("Products", "Banquettes", "/images/cases/hangzhou-sichuan/cover1008.jpg"),
    "restaurant-chairs-manufacturer.html": ("Products", "Chairs", "/images/factory/factory-2.jpg"),
    "restaurant-tables-manufacturer.html": ("Products", "Tables", "/images/cases/beijing-sichuan/cover1006-3.jpg"),
    "fine-dining-restaurant-furniture.html": ("Venues", "Fine dining", "/images/cases/beijing-sichuan/cover1006-4.jpg"),
    "fast-food-restaurant-furniture.html": ("Venues", "Fast casual & QSR", "/images/services/restaurant.jpg"),
    "cafe-furniture-manufacturer.html": ("Venues", "Cafés", "/images/services/cafe.jpg"),
    "bar-furniture-manufacturer.html": ("Venues", "Bars & lounges", "/images/cases/guangzhou-chio/cover1007-9.jpg"),
    "hotel-furniture-manufacturer-china.html": ("Venues", "Hotels", "/images/services/hotel.jpg"),
    "outdoor-restaurant-furniture.html": ("Venues", "Outdoor dining", "/images/services/outdoor.jpg"),
}
CITY_EN = {"北京": "Beijing, China", "广州": "Guangzhou, China", "杭州": "Hangzhou, China", "汉中": "Hanzhong, China", "佛山": "Foshan, China", "南京": "Nanjing, China",
           "上海": "Shanghai, China", "新加坡": "Singapore", "纽约": "New York, USA", "伦敦": "London, UK", "东京": "Tokyo, Japan", "悉尼": "Sydney, Australia",
           "香港": "Hong Kong", "蒙特利尔": "Montreal, Canada", "巴黎": "Paris, France", "迈阿密": "Miami, USA", "雅加达": "Jakarta, Indonesia",
           "洛杉矶": "Los Angeles, USA", "米兰": "Milan, Italy", "迪拜": "Dubai, UAE", "巴塞罗那": "Barcelona, Spain", "首尔": "Seoul, Korea",
           "曼谷": "Bangkok, Thailand", "墨尔本": "Melbourne, Australia", "马尔代夫": "Maldives", "柏林": "Berlin, Germany", "旧金山": "San Francisco, USA", "巴厘岛": "Bali, Indonesia"}
TYPE_ORDER = {"booth": 0, "chair": 1, "table": 2}
OLD_STYLE_PAGES = {"restaurant": ["restaurant-style-1", "restaurant-style-2"], "cafe": ["cafe-style-1"], "hotel": ["hotel-style-1"], "outdoor": ["outdoor-style-1"]}

# ------------------------------------------------------------------ utils
def rj(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Obj(dict):
    """dict with attribute access for templates (t.home.title)."""
    def __getattr__(self, k):
        try:
            v = self[k]
        except KeyError:
            raise AttributeError(k)
        return Obj(v) if isinstance(v, dict) and not isinstance(v, Obj) else v


def objify(d):
    if isinstance(d, dict):
        return Obj({k: objify(v) for k, v in d.items()})
    return d


WRITES = {}


def out(rel, text):
    rel = rel.lstrip("/")
    WRITES[rel] = text


def flush():
    changed = 0
    for rel, text in WRITES.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        if p.exists() and p.read_bytes() == data:
            continue
        p.write_bytes(data)
        changed += 1
    return changed


def fhash(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:10]

# ------------------------------------------------------------------ images
RES_DIR = "images/_r"
WIDTHS = {"product": [360, 720, 1000], "default": [640, 1280, 2000]}
_IMG = {}
DO_IMG = True


def _variant_path(src, w):
    stem = src.lstrip("/")
    stem = re.sub(r"^images/", "", stem)
    stem = re.sub(r"\.[A-Za-z0-9]+$", "", stem)
    return "/%s/%s-%d.webp" % (RES_DIR, stem, w)


def img(src):
    """-> dict(src, srcset, w, h). Generates webp variants for local images."""
    if not src:
        return Obj(src="", srcset="", w=None, h=None)
    if src in _IMG:
        return _IMG[src]
    local = ROOT / src.lstrip("/")
    if not src.startswith("/images/") or not local.exists():
        r = Obj(src=src, srcset="", w=None, h=None)
        _IMG[src] = r
        return r
    from PIL import Image, ImageOps
    kind = "product" if src.startswith("/images/products") else "default"
    with Image.open(local) as im0:
        W, H = ImageOps.exif_transpose(im0).size if hasattr(im0, "getexif") and im0.getexif().get(0x0112, 1) in (5, 6, 7, 8) else im0.size
    ws = [w for w in WIDTHS[kind] if w < W] or [W]
    if W > ws[-1] and len(ws) < len(WIDTHS[kind]):
        ws.append(min(W, WIDTHS[kind][len(ws)]))
    srcset = []
    im = None
    for w in ws:
        vp = _variant_path(src, w)
        vf = ROOT / vp.lstrip("/")
        if DO_IMG and (not vf.exists() or vf.stat().st_mtime < local.stat().st_mtime):
            if im is None:
                im = Image.open(local)
                im = ImageOps.exif_transpose(im)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGB")
                if im.mode == "RGBA":
                    bg = Image.new("RGB", im.size, (237, 231, 221))
                    bg.paste(im, mask=im.split()[3])
                    im = bg
            h = round(H * w / W)
            vf.parent.mkdir(parents=True, exist_ok=True)
            im.resize((w, h), Image.LANCZOS).save(vf, "WEBP", quality=78, method=5)
        if vf.exists():
            srcset.append("%s %dw" % (vp, w))
    if im is not None:
        im.close()
    mid = srcset[min(1, len(srcset) - 1)].split(" ")[0] if srcset else src
    r = Obj(src=mid, srcset=", ".join(srcset), w=W, h=H, full=src)
    _IMG[src] = r
    return r


def thumb(src):
    d = img(src)
    return d.srcset.split(" ")[0] if d.srcset else src

# ------------------------------------------------------------------ data
def load_data():
    products = [p for p in rj(ROOT / "data/products.json") if (p.get("status") or "online") == "online"]
    products = list(reversed(products))  # newest first (same order as the admin list)
    pi18n = rj(ROOT / "data/products-i18n.json")
    cases_all = rj(ROOT / "data/cases.json")
    cnt = {}
    for c in cases_all:
        cnt[c.get("cover_image")] = cnt.get(c.get("cover_image"), 0) + 1
    # placeholder cases reuse one stock photo for several "projects": keep them offline
    cases = [c for c in cases_all if c.get("cover_image") and cnt[c["cover_image"]] == 1 and c.get("status") not in ("hidden", "offline") and c.get("images")]
    for c in cases:
        c["own"] = str(c["id"]) in OWN_CASES
        c["feat"] = FEATURE_IDX.get(str(c["id"]), [0, 1, 2])
    return products, pi18n, cases


def code(p):
    if not p:
        return ""
    return p.get("sku") or ("EA-" + str(p["id"])[-5:])

# ------------------------------------------------------------------ urls
def u(L, path):
    return "/%s/%s" % (L, path)


def cat_url(c, L):
    return u(L, "products/%s/" % c)


def product_url(p, L):
    return u(L, "products/item/%s.html" % p["id"])


def case_url(c, L):
    return u(L, "cases/%s.html" % c["id"])


def insight_url(f, L):
    return u(L if L in INSIGHT_LANGS else "en", f)


def abs_url(path):
    return DOMAIN + path


def clean_path(path):
    return re.sub(r"index\.html$", "", path)

# ------------------------------------------------------------------ build
class Site:
    def __init__(self):
        self.products, self.pi18n, self.cases = load_data()
        self.T = {}
        en = rj(SRC / "i18n/en.json")
        for L in LANGS:
            f = SRC / ("i18n/%s.json" % L)
            self.T[L] = objify(deep_merge(en, rj(f) if f.exists() else {}))
        self.env = Environment(loader=FileSystemLoader(str(SRC / "templates")), autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
        self.pages = {}  # key -> {L: path}
        self.sitemap = []  # (path, key, lastmod, images)
        self.cat_count = {c: sum(1 for p in self.products if p["category"] == c) for c in CATS}
        self.case_cats = [c for c in CATS if any(x["category"] == c for x in self.cases)]
        self.case_count = {c: sum(1 for x in self.cases if x["category"] == c) for c in CATS}
        self.V = {}

    # ---- helpers exposed to templates
    def pname(self, p, L):
        if L == "zh":
            return p.get("title_zh") or p.get("title_en") or ""
        if L == "en":
            return p.get("title_en") or p.get("title_zh") or ""
        return (self.pi18n.get(str(p["id"])) or {}).get(L) or p.get("title_en") or p.get("title_zh") or ""

    def pdesc(self, p, L):
        return (p.get("desc_zh") if L == "zh" else p.get("desc_en")) or ""

    def cname(self, c, L):
        return (c.get("title_zh") if L == "zh" else c.get("title_en")) or c.get("title_en") or c.get("title_zh") or ""

    def cloc(self, c, L):
        loc = c.get("location") or ""
        if L == "zh":
            return loc
        return CITY_EN.get(loc, loc)

    def cdesc(self, c, L):
        return (c.get("desc_zh") if L == "zh" else c.get("desc_en")) or c.get("desc_en") or ""

    def cdesc_short(self, c, L, n=150):
        s = re.sub(r"\s+", " ", self.cdesc(c, L)).strip()
        s = re.sub(r"【[^】]*】", "", s)
        if L == "zh":
            n = int(n * 0.45)
        if len(s) <= n:
            return s
        return (s[:n] if L == "zh" else s[:n].rsplit(" ", 1)[0]).rstrip("，,;；:：.。 ") + "…"

    def cdesc_html(self, c, L):
        parts = [p.strip() for p in re.split(r"\n\s*\n", self.cdesc(c, L)) if p.strip()]
        outp = []
        for p in parts:
            m = re.match(r"^【([^】]+)】\s*(.*)$", p, re.S) or re.match(r"^(Solution|Result|Background|Challenge|Requirements?|Our solution|Outcome)s?:\s*(.*)$", p, re.S)
            if m:
                outp.append("<h3>%s</h3>" % html.escape(m.group(1)))
                p = m.group(2)
            p = p[:1].upper() + p[1:]
            outp.append("<p>%s</p>" % html.escape(p).replace("\n", "<br>"))
        return "\n".join(outp)

    def search_blob(self, p):
        tr = self.pi18n.get(str(p["id"])) or {}
        return " ".join([p.get("title_zh", ""), p.get("title_en", ""), code(p)] + list(tr.values())).lower()

    # ---- page registry
    def langs_for(self, key):
        return [L for L in LANGS if L in self.pages.get(key, {})]

    def reg(self, key, L, path):
        self.pages.setdefault(key, {})[L] = path

    def alternates(self, key):
        m = self.pages.get(key, {})
        alts = [{"hl": ("zh-Hans" if L == "zh" else L), "href": abs_url(clean_path(m[L]))} for L in LANGS if L in m]
        xd = m.get("en") or next(iter(m.values()))
        alts.append({"hl": "x-default", "href": abs_url(clean_path(xd))})
        return alts

    def lang_links(self, key, L):
        m = self.pages.get(key, {})
        res = []
        for x in LANGS:
            href = clean_path(m[x]) if x in m else "/%s/" % x
            res.append({"L": x, "href": href, "name": self.T[x]._name})
        return res

    def ctx(self, L):
        t = self.T[L]
        js_t = {
            "added_ai": t.products.added_ai, "add_ai": t.products.add_ai,
            "type": {k: t.type[k + "_one"] for k in TYPES},
            "catLong": {k: t.cat[k + "_long"] for k in CATS},
            "spec": {"code": t.products.spec_code, "dims": t.products.spec_dims, "material": t.products.spec_material, "moq": t.products.spec_moq, "lead": t.products.spec_lead,
                     "dims_v": t.products.dims_custom, "mat_v": t.products.mat_custom, "moq_v": t.products.moq_val, "lead_v": t.products.lead_val},
        }
        return dict(
            L=L, t=t, S=Obj(S), V=self.V, YEAR=YEAR, CATS=CATS, TYPES=TYPES,
            CAT_COUNT=self.cat_count, CAT_IMG=CAT_IMG, CAT_HERO=CAT_HERO,
            HERO=HERO, HERO_WALL=HERO_WALL, INTRO_IMG=INTRO_IMG, CTA_IMG=CTA_IMG, ABOUT_HERO=ABOUT_HERO, ABOUT_STORY=ABOUT_STORY,
            CONTACT_IMG=CONTACT_IMG, FACTORY_POSTER=FACTORY_POSTER, FACTORY_POSTER2=FACTORY_POSTER2,
            FACTORY_STRIP=FACTORY_STRIP, FACTORY_ALL=FACTORY_ALL, AI_BEFORE=AI_BEFORE, AI_AFTER=AI_AFTER,
            HOTEL_IMGS=HOTEL_IMGS, INSIGHTS=INSIGHTS, CASE_CATS=self.case_cats, CASE_COUNT=self.case_count,
            u=u, cat_url=cat_url, product_url=product_url, case_url=case_url, insight_url=insight_url,
            has_insight=lambda L_: L_ in INSIGHT_LANGS,
            img=img, thumb=thumb, code=code, pname=self.pname, pdesc=self.pdesc, cname=self.cname, cloc=self.cloc,
            cdesc_short=self.cdesc_short, cdesc_html=self.cdesc_html, search_blob=self.search_blob,
            jscfg={"L": L, "t": js_t, "builtP": [str(p["id"]) for p in self.products], "builtC": [str(c["id"]) for c in self.cases]},
        )

    def render(self, tpl, L, key, path, page, root_copy=True, **extra):
        """render one page for language L at /L/path; optionally an English root copy."""
        t = self.T[L]
        page = dict(page)
        page.setdefault("og_image", DOMAIN + "/images/og-image.jpg")
        page.setdefault("jsonld", [])
        page["canonical"] = abs_url(clean_path(path))
        page["alternates"] = self.alternates(key)
        page["langs"] = self.lang_links(key, L)
        c = self.ctx(L)
        c.update(extra)
        c["page"] = page
        html_ = self.env.get_template(tpl).render(**c)
        out(path, html_)
        if not page.get("noindex"):
            self.sitemap.append((clean_path(path), key, L))
        if root_copy and L == "en":
            rpage = dict(page)
            rel = path[len("/en/"):]
            rpage["root_redirect"] = clean_path("/" + rel).lstrip("/") or ""
            c2 = dict(c)
            c2["page"] = rpage
            out("/" + rel, self.env.get_template(tpl).render(**c2))

    def redirect(self, path, target):
        t = abs_url(target)
        out(path, '<!doctype html><html><head><meta charset="utf-8"><title>EASEN</title><link rel="canonical" href="%s"><meta name="robots" content="noindex, follow"><meta http-equiv="refresh" content="0; url=%s"><script>location.replace(%s)</script></head><body><a href="%s">%s</a></body></html>' % (t, target, json.dumps(target), target, t))

    # ---- structured data
    def org_ld(self, L):
        t = self.T[L]
        return {"@context": "https://schema.org", "@type": "Organization", "@id": DOMAIN + "/#org", "name": "EASEN", "alternateName": [t.brand.full, "宜森商业空间家具", "EASEN Commercial Furniture"],
                "url": DOMAIN + "/", "logo": DOMAIN + "/icon-512.png", "email": S["email"], "telephone": S["tel"], "foundingDate": "2016",
                "address": {"@type": "PostalAddress", "addressLocality": "Foshan", "addressRegion": "Guangdong", "streetAddress": "Lecong Town, Shunde District", "addressCountry": "CN"},
                "contactPoint": [{"@type": "ContactPoint", "contactType": "sales", "email": S["email"], "telephone": S["tel"], "availableLanguage": ["English", "Chinese"]}]}

    def crumbs_ld(self, items):
        return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(clean_path(p))} for i, (n, p) in enumerate(items)]}

    def make_serif_subset(self):
        """Subset Noto Serif SC SemiBold to the CJK characters that can appear in serif (heading) text."""
        dst = SRC / "assets/fonts/serif-sc.woff2"
        otf = ROOT.parent / "_fonts" / "NotoSerifSC-SemiBold.otf"
        chars = set()
        def walk(v):
            if isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, str):
                chars.update(v)
        walk(rj(SRC / "i18n/zh.json"))
        for p in self.products:
            chars.update(p.get("title_zh", ""))
        for c in self.cases:
            chars.update(c.get("title_zh", "") + (c.get("location") or ""))
            chars.update("".join(re.findall(r"【([^】]+)】", c.get("desc_zh") or "")))
        from bs4 import BeautifulSoup
        for f in (SRC / "content/insights/zh").glob("*.html"):
            s = BeautifulSoup(f.read_text(encoding="utf-8"), "html.parser")
            for h in s.find_all(["h1", "h2", "h3", "h4", "strong", "blockquote"]):
                chars.update(h.get_text())
        chars.update("0123456789，。、：；！？“”‘’（）《》·—…％+")
        text = "".join(sorted(c for c in chars if ord(c) > 0x2000))
        stamp = SRC / "assets/fonts/serif-sc.chars"
        if dst.exists() and stamp.exists() and stamp.read_text(encoding="utf-8") == text:
            return
        if not otf.exists():
            print("! serif-sc: source font missing (%s), keeping existing subset" % otf)
            return
        from fontTools import subset
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        font = subset.load_font(str(otf), opts)
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        subset.save_font(font, str(dst), opts)
        stamp.write_text(text, encoding="utf-8")
        print("serif-sc subset: %d chars, %d KB" % (len(text), dst.stat().st_size // 1024))

    # ---- builders
    def build(self):
        # css/js/fonts
        (ROOT / "assets/fonts").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / "assets/site.css", ROOT / "assets/site.css")
        shutil.copyfile(SRC / "assets/site.js", ROOT / "assets/site.js")
        for f in (SRC / "assets/fonts").glob("*.woff2"):
            shutil.copyfile(f, ROOT / "assets/fonts" / f.name)
        self.make_serif_subset()
        shutil.copyfile(SRC / "assets/fonts/serif-sc.woff2", ROOT / "assets/fonts/serif-sc.woff2")
        self.V.update(css=fhash(ROOT / "assets/site.css"), js=fhash(ROOT / "assets/site.js"), font=fhash(SRC / "assets/fonts/serif-sc.woff2"))

        # register page keys first (for hreflang)
        simple = ["index.html", "products.html", "cases.html", "about.html", "contact.html", "visualizer.html", "product.html", "case.html"]
        for L in LANGS:
            for f in simple:
                self.reg(f, L, u(L, f))
            for c in CATS:
                self.reg("cat:" + c, L, u(L, "products/%s/index.html" % c))
            for c in self.case_cats:
                self.reg("ccat:" + c, L, u(L, "case-%s.html" % c))
            for p in self.products:
                self.reg("p:%s" % p["id"], L, u(L, "products/item/%s.html" % p["id"]))
            for c in self.cases:
                self.reg("c:%s" % c["id"], L, u(L, "cases/%s.html" % c["id"]))
        for L in INSIGHT_LANGS:
            for it in INSIGHTS:
                self.reg(it["file"], L, u(L, it["file"]))
        for f in list(LANDING) + ["solutions.html"]:
            self.reg(f, "en", u("en", f))

        for L in LANGS:
            self.build_lang(L)
        self.build_landing()
        self.build_extras()

    def build_lang(self, L):
        t = self.T[L]
        home_items = [p for p in self.products if p["category"] == "restaurant" and len(p.get("images", [])) > 1][:8]
        featured = [c for c in self.cases if c["own"]][:3]
        # home
        self.render("index.html", L, "index.html", u(L, "index.html"),
                    {"title": t.home.title, "desc": t.home.desc, "over": True, "body_class": "over home",
                     "jsonld": [self.org_ld(L), {"@context": "https://schema.org", "@type": "WebSite", "name": "EASEN", "url": DOMAIN + "/", "inLanguage": L}]},
                    FEATURED=featured, HOME_PRODUCTS=home_items)
        # products (all)
        type_count = {ty: sum(1 for p in self.products if p.get("type") == ty) for ty in TYPES}
        self.render("products.html", L, "products.html", u(L, "products.html"),
                    {"title": t.products.title, "desc": t.products.desc, "section": "products",
                     "jsonld": [self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.collection, u(L, "products.html"))])]},
                    LIST=sorted(self.products, key=lambda p: TYPE_ORDER.get(p.get("type"), 9)), cat=None, TYPE_COUNT=type_count)
        # category pages
        for c in CATS:
            lst = sorted([p for p in self.products if p["category"] == c], key=lambda p: TYPE_ORDER.get(p.get("type"), 9))
            tc = {ty: sum(1 for p in lst if p.get("type") == ty) for ty in TYPES}
            name = t.cat[c + "_long"]
            title = t.products.cat_title.replace("{cat}", name).replace("{cat_lower}", name.lower() if L in ("en",) else name)
            title = "%s | EASEN" % name if L not in ("zh",) else title
            if L == "en":
                title = {"restaurant": "Restaurant Furniture — Commercial Chairs, Booths & Tables | EASEN",
                         "cafe": "Café Furniture — Commercial Café Chairs & Tables | EASEN",
                         "outdoor": "Outdoor Restaurant Furniture — Patio Chairs & Tables | EASEN",
                         "hotel": "Hotel & Lounge Furniture — Made to Order | EASEN"}[c]
            ld = [self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.collection, u(L, "products.html")), (name, cat_url(c, L))])]
            if lst:
                ld.append({"@context": "https://schema.org", "@type": "ItemList", "name": name, "numberOfItems": len(lst),
                           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": abs_url(product_url(p, L)), "name": self.pname(p, L)} for i, p in enumerate(lst[:60])]})
            self.render("products.html", L, "cat:" + c, u(L, "products/%s/index.html" % c),
                        {"title": title, "desc": t.products["cat_lead_" + c][:158], "section": "products", "jsonld": ld,
                         "og_image": DOMAIN + img(CAT_HERO[c]).src},
                        LIST=lst, cat=c, TYPE_COUNT=tc)
        # product detail pages
        by_cat = {}
        for p in self.products:
            by_cat.setdefault((p["category"], p.get("type")), []).append(p)
        for p in self.products:
            nm = self.pname(p, L)
            ty = t.type[p.get("type", "chair") + "_one"]
            title = t.products.detail_title.replace("{name}", "%s %s" % (nm, code(p))).replace("{type}", ty)
            desc = t.products.detail_desc.replace("{name}", nm).replace("{type_lower}", ty.lower() if L != "de" else ty).replace("{type}", ty).replace("{cat}", t.cat[p["category"]])
            pool = [x for x in by_cat[(p["category"], p.get("type"))] if x is not p]
            i = self.products.index(p)
            rel = sorted(pool, key=lambda x: abs(self.products.index(x) - i))[:4]
            ld = [self.crumbs_ld([(t.nav.home, u(L, "")), (t.cat[p["category"] + "_long"], cat_url(p["category"], L)), (nm, product_url(p, L))]),
                  {"@context": "https://schema.org", "@type": "Product", "name": nm, "sku": code(p), "mpn": code(p), "brand": {"@type": "Brand", "name": "EASEN"},
                   "category": t.cat[p["category"] + "_long"], "image": [abs_url(i_) for i_ in p.get("images", [])],
                   "description": desc, "manufacturer": {"@id": DOMAIN + "/#org"}}]
            self.render("product.html", L, "p:%s" % p["id"], u(L, "products/item/%s.html" % p["id"]),
                        {"title": title, "desc": desc, "section": "products", "og_type": "product", "og_image": abs_url(img(p["main_image"]).src), "jsonld": ld},
                        root_copy=False, p=p, RELATED=rel)
        # dynamic fallback detail pages
        self.render("product.html", L, "product.html", u(L, "product.html"), {"title": t.products.h1 + " | EASEN", "desc": t.products.desc, "noindex": True, "section": "products"}, root_copy=False, p=None, RELATED=[])
        self.render("case.html", L, "case.html", u(L, "case.html"), {"title": t.cases.h1 + " | EASEN", "desc": t.cases.desc, "noindex": True, "section": "cases"}, root_copy=False, c=None, MORE=[])
        # cases list + category
        self.render("cases.html", L, "cases.html", u(L, "cases.html"),
                    {"title": t.cases.title, "desc": t.cases.desc, "section": "cases", "jsonld": [self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.projects, u(L, "cases.html"))])]},
                    LIST=self.cases, CASES=self.cases, cat=None)
        for c in self.case_cats:
            lst = [x for x in self.cases if x["category"] == c]
            self.render("cases.html", L, "ccat:" + c, u(L, "case-%s.html" % c),
                        {"title": t.cases.cat_title.replace("{cat}", t.cat[c]), "desc": t.cases.desc, "section": "cases"},
                        LIST=lst, CASES=self.cases, cat=c)
        for c in self.cases:
            nm = self.cname(c, L)
            more = [x for x in self.cases if x is not c and x["own"]][:3] if c["own"] else [x for x in self.cases if x is not c and x["category"] == c["category"]][:3]
            if len(more) < 3:
                more += [x for x in self.cases if x is not c and x not in more][: 3 - len(more)]
            self.render("case.html", L, "c:%s" % c["id"], u(L, "cases/%s.html" % c["id"]),
                        {"title": t.cases.detail_title.replace("{name}", nm), "desc": self.cdesc_short(c, L, 155), "section": "cases", "og_type": "article",
                         "og_image": abs_url(img(c["cover_image"]).src), "preload": img(c["cover_image"]),
                         "jsonld": [self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.projects, u(L, "cases.html")), (nm, case_url(c, L))])]},
                        root_copy=False, c=c, MORE=more)
        # about / contact / visualizer
        self.render("about.html", L, "about.html", u(L, "about.html"),
                    {"title": t.about.title, "desc": t.about.desc, "section": "about", "preload": img(ABOUT_HERO),
                     "jsonld": [self.org_ld(L), self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.about, u(L, "about.html"))])]})
        faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t.contact["fq%d" % i], "acceptedAnswer": {"@type": "Answer", "text": t.contact["fa%d" % i]}} for i in range(1, 6)]}
        self.render("contact.html", L, "contact.html", u(L, "contact.html"),
                    {"title": t.contact.title, "desc": t.contact.desc, "section": "contact", "jsonld": [faq, self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.contact, u(L, "contact.html"))])]})
        self.render("visualizer.html", L, "visualizer.html", u(L, "visualizer.html"),
                    {"title": t.ai.title, "desc": t.ai.desc, "section": "ai", "body_class": "page-ai",
                     "jsonld": [{"@context": "https://schema.org", "@type": "WebApplication", "name": "EASEN AI Furniture Preview", "url": abs_url(u(L, "visualizer.html")), "applicationCategory": "DesignApplication", "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}]})
        # insights
        if L in INSIGHT_LANGS:
            for it in INSIGHTS:
                self.build_insight(L, it)
        else:
            for it in INSIGHTS:
                self.redirect(u(L, it["file"]), "/en/" + it["file"])

    # ---- long-form (legacy content re-skinned)
    def _clean_fragment(self, el):
        from bs4 import BeautifulSoup
        for bad in el.find_all(["script", "style", "button", "noscript"]):
            bad.decompose()
        for tag in el.find_all(True):
            cls = " ".join(tag.get("class", []))
            keep = None
            if re.search(r"(^| )(grid|two-col)( |$)|grid-cols", cls):
                keep = "grid"
            elif re.search(r"(^| )(card|highlight-box|box)( |$)|bg-(white|neutral|amber|stone|gray|accent)|rounded-(xl|2xl)", cls) and tag.name == "div":
                keep = "card"
            elif re.search(r"(^| )cta( |$)", cls):
                keep = "cta"
            for a in ("class", "style", "onclick", "onmouseover", "onmouseout"):
                if a in tag.attrs:
                    del tag.attrs[a]
            if keep:
                tag["class"] = keep
            if tag.name == "img":
                src = tag.get("src", "")
                if src.startswith("/images/") and (ROOT / src.lstrip("/")).exists():
                    d = img(src)
                    tag["src"] = d.src
                    if d.srcset:
                        tag["srcset"] = d.srcset
                        tag["sizes"] = "(max-width:920px) 100vw, 880px"
                tag["loading"] = "lazy"
                tag["decoding"] = "async"
        # legacy list items carry their own bullet glyph; the new list style draws one
        for li in el.find_all("li"):
            first = next((x for x in li.descendants if isinstance(x, str) and x.strip()), None)
            if first is not None and re.match(r"^\s*[•·]\s*", first):
                first.replace_with(re.sub(r"^\s*[•·]\s*", "", str(first)))
        # drop unverified third-party client-brand claims
        doomed = []
        for tx in el.find_all(string=re.compile(r"Marriott|Hilton|IHG|Accor")):
            par = tx.find_parent(["li", "p"])
            if par is not None and par not in doomed:
                doomed.append(par)
        for par in doomed:
            if par.parent is not None:
                par.decompose()
        return el

    def _ld_from(self, soup):
        res = []
        for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                j = json.loads(s.string or "")
            except Exception:
                continue
            txt = json.dumps(j, ensure_ascii=False)
            if re.search(r"Marriott|Hilton|IHG|Accor", txt):
                continue
            res.append(j)
        return res

    def build_insight(self, L, it):
        from bs4 import BeautifulSoup
        t = self.T[L]
        src = SRC / "content/insights" / L / it["file"]
        soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")
        title = (soup.title.string or "").strip() if soup.title else t.insights["t_" + it["key"]]
        md = soup.find("meta", attrs={"name": "description"})
        desc = md["content"] if md else t.insights["p_" + it["key"]]
        art = soup.find("article")
        hero = art.find_previous("div", class_=re.compile("relative")) if art else None
        h1 = soup.find("h1")
        h1t = h1.get_text(" ", strip=True) if h1 else t.insights["t_" + it["key"]]
        sub = ""
        if h1:
            nxt = h1.find_next_sibling("p")
            sub = nxt.get_text(" ", strip=True) if nxt else ""
        body = self._clean_fragment(art)
        # remove trailing CTA blocks that link back to the old layout
        for a in body.find_all("a"):
            href = a.get("href", "")
            if href in ("index.html#contact", "../index.html#contact", "/index.html#contact", "#contact") or href.endswith("contact.html"):
                a["href"] = u(L, "contact.html")
            elif re.match(r"^(\.\./)?index\.html", href) or href in ("/", "../"):
                a["href"] = u(L, "")
        html_ = "".join(str(x) for x in body.contents)
        ld = [j for j in self._ld_from(soup) if isinstance(j, dict) and j.get("@type") not in ("BreadcrumbList",)]
        for j in ld:
            if j.get("@type") in ("Article", "BlogPosting") :
                j["mainEntityOfPage"] = abs_url(u(L, it["file"]))
        ld.append(self.crumbs_ld([(t.nav.home, u(L, "")), (t.nav.insights, u(L, it["file"])), (h1t, u(L, it["file"]))]))
        others = [x for x in INSIGHTS if x is not it]
        self.render("article.html", L, it["file"], u(L, it["file"]),
                    {"title": title, "desc": desc, "og_type": "article", "og_image": abs_url(img(it["img"]).src), "jsonld": ld},
                    art=Obj(h1=h1t, sub=sub, kicker=t.insights["k_" + it["key"]], html=Markup(html_), sections=None, anchors=None),
                    hero_img=it["img"], crumbs=[{"name": t.nav.insights, "href": u(L, it["file"])}],
                    related=[{"name": t.insights["t_" + x["key"]], "href": u(L, x["file"])} for x in others], related_title=t.nav.insights)

    def build_landing(self):
        from bs4 import BeautifulSoup
        L = "en"
        t = self.T[L]
        metas = []
        for f, (group, kicker, hero) in LANDING.items():
            soup = BeautifulSoup((SRC / "content/landing" / f).read_text(encoding="utf-8"), "html.parser")
            title = soup.title.string.strip()
            desc = soup.find("meta", attrs={"name": "description"})["content"]
            hdr = soup.body.find("header")
            h1 = hdr.find("h1").get_text(" ", strip=True)
            subp = hdr.find("p")
            sub = subp.get_text(" ", strip=True) if subp else ""
            nav = soup.body.find("nav")
            anchors = []
            if nav:
                for a in nav.find_all("a"):
                    if a.get("href", "").startswith("#"):
                        anchors.append({"id": a["href"][1:], "name": a.get_text(strip=True)})
            sections = []
            related = []
            for sec in soup.body.find_all("section", recursive=True):
                if sec.get("aria-label") == "Related solutions":
                    for a in sec.find_all("a"):
                        href = a.get("href", "")
                        if href.endswith(".html"):
                            related.append({"name": a.get_text(" ", strip=True).replace("→", "").strip(), "href": href if href.startswith("/") else "/en/" + href.split("/")[-1]})
                    continue
                cont = sec.find("div", class_="container") or sec
                cont = self._clean_fragment(cont)
                for a in cont.find_all("a"):
                    href = a.get("href", "")
                    if href.startswith("http://chinaeasen.com") or href.startswith("https://chinaeasen.com"):
                        a["href"] = re.sub(r"^https?://chinaeasen\.com", "", href)
                    if a["href"] in ("/contact.html", "contact.html", "/en/contact.html#form"):
                        a["href"] = "/en/contact.html"
                sections.append({"id": sec.get("id"), "html": Markup("".join(str(x) for x in cont.contents))})
            ld = [j for j in self._ld_from(soup)]
            ids = {a["id"] for a in anchors}
            anchors = [a for a in anchors if any(s["id"] == a["id"] for s in sections)]
            og = soup.find("meta", attrs={"property": "og:image"})
            ogi = og["content"] if og and (ROOT / re.sub(r"^https?://[^/]+/", "", og["content"])).exists() else DOMAIN + img(hero).src
            self.render("article.html", L, f, u(L, f),
                        {"title": title, "desc": desc, "section": "solutions", "og_image": ogi, "jsonld": ld},
                        root_copy=False,
                        art=Obj(h1=h1, sub=sub, kicker=kicker, html="", sections=sections, anchors=anchors),
                        hero_img=hero, crumbs=[{"name": "Solutions", "href": "/en/solutions.html"}],
                        related=related or [{"name": LANDING_NAME(x), "href": "/en/" + x} for x in LANDING if x != f][:6], related_title="More solutions")
            metas.append({"file": f, "group": group, "kicker": kicker, "h1": h1, "desc": desc})
        groups = []
        for g in ("Manufacturing", "Products", "Venues"):
            groups.append({"name": {"Manufacturing": "Manufacturing & FF&E", "Products": "By product", "Venues": "By venue"}[g], "entries": [m for m in metas if m["group"] == g]})
        self.render("solutions.html", L, "solutions.html", u(L, "solutions.html"),
                    {"title": "Commercial Furniture Solutions — Restaurant, Café, Bar & Hotel | EASEN", "desc": "Guides to EASEN custom commercial furniture by venue and product: booth seating, restaurant chairs and tables, café, bar, hotel and outdoor furniture made in Foshan, China.", "section": "solutions",
                     "jsonld": [self.crumbs_ld([("Home", "/en/"), ("Solutions", "/en/solutions.html")])]},
                    root_copy=False, GROUPS=groups)

    def build_extras(self):
        # 404 (root, English)
        t = self.T["en"]
        page = {"title": t.notfound.title, "desc": t.notfound.lead, "noindex": True, "canonical": DOMAIN + "/404.html", "alternates": [], "langs": self.lang_links("index.html", "en"), "og_image": DOMAIN + "/images/og-image.jpg", "jsonld": []}
        c = self.ctx("en")
        c["page"] = page
        out("/404.html", self.env.get_template("404.html").render(**c))
        # old style pages -> category
        for cat, pages in OLD_STYLE_PAGES.items():
            for pg in pages:
                self.redirect("/products/%s/%s/index.html" % (cat, pg), "/en/products/%s/" % cat)
        # root product-category entry pages (English copies) are produced by render(); add them explicitly
        for cat in CATS:
            src = WRITES.get("en/products/%s/index.html" % cat)
            if src:
                page_path = "products/%s/index.html" % cat
                out(page_path, src.replace('<script>document.documentElement', '<script>(function(){try{var s=localStorage.getItem(\'easen-lang\'),n=(navigator.language||\'\').toLowerCase(),l=s||(n.indexOf(\'zh\')===0?\'zh\':\'\');if(l&&l!==\'en\'&&/^(zh|fr|es|de|ar)$/.test(l))location.replace(\'/\'+l+\'/products/%s/\');}catch(e){}})();</script>\n<script>document.documentElement' % cat, 1))
        # sitemaps
        self.write_sitemaps()
        out("/robots.txt", "# EASEN — https://chinaeasen.com\nUser-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /temp-preview/\nDisallow: /tools/\nDisallow: /src/\nDisallow: /*/product.html\nDisallow: /*/case.html\n\nSitemap: %s/sitemap.xml\n" % DOMAIN)

    def write_sitemaps(self):
        groups = {"pages": [], "products": [], "cases": []}
        seen = set()
        for path, key, L in self.sitemap:
            if path in seen:
                continue
            seen.add(path)
            g = "products" if key.startswith("p:") else "cases" if key.startswith("c:") else "pages"
            groups[g].append((path, key))
        def urlset(items, with_img=False):
            x = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml"%s>' % (' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' if with_img else "")]
            for path, key in items:
                x.append("<url><loc>%s</loc><lastmod>%s</lastmod>" % (html.escape(abs_url(path)), TODAY))
                for a in self.alternates(key):
                    x.append('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (a["hl"], html.escape(a["href"])))
                if with_img:
                    ims = []
                    if key.startswith("p:"):
                        p = next(p for p in self.products if "p:%s" % p["id"] == key)
                        ims = p.get("images", [])
                    elif key.startswith("c:"):
                        c = next(c for c in self.cases if "c:%s" % c["id"] == key)
                        ims = c.get("images", [])[:10]
                    for im in ims:
                        x.append("<image:image><image:loc>%s</image:loc></image:image>" % html.escape(abs_url(im)))
                x.append("</url>")
            x.append("</urlset>\n")
            return "\n".join(x)
        out("/sitemap-pages.xml", urlset(groups["pages"]))
        out("/sitemap-products.xml", urlset(groups["products"], True))
        out("/sitemap-cases.xml", urlset(groups["cases"], True))
        idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for n in ("sitemap-pages.xml", "sitemap-products.xml", "sitemap-cases.xml", "video-sitemap.xml"):
            idx.append("  <sitemap><loc>%s/%s</loc><lastmod>%s</lastmod></sitemap>" % (DOMAIN, n, TODAY))
        idx.append("</sitemapindex>\n")
        out("/sitemap.xml", "\n".join(idx))
        out("/video-sitemap.xml", VIDEO_SITEMAP)


def LANDING_NAME(f):
    return f.replace(".html", "").replace("-", " ").title()


VIDEO_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
  <url>
    <loc>https://chinaeasen.com/en/</loc>
    <video:video>
      <video:thumbnail_loc>https://chinaeasen.com/images/factory/factory-11.jpg</video:thumbnail_loc>
      <video:title>Inside EASEN — commercial furniture production in Foshan</video:title>
      <video:description>EASEN's 10,000 m² production base in Lecong, Foshan: frames, upholstery, finishing and packing of restaurant and hospitality furniture.</video:description>
      <video:content_loc>https://chinaeasen.com/videos/factory-showcase-h264.mp4</video:content_loc>
      <video:family_friendly>yes</video:family_friendly>
      <video:live>no</video:live>
    </video:video>
  </url>
  <url>
    <loc>https://chinaeasen.com/en/about.html</loc>
    <video:video>
      <video:thumbnail_loc>https://chinaeasen.com/images/factory/factory-3.jpg</video:thumbnail_loc>
      <video:title>EASEN factory tour</video:title>
      <video:description>A walk through EASEN's commercial furniture factory in Foshan, China: materials, craftsmanship and quality control.</video:description>
      <video:content_loc>https://chinaeasen.com/videos/factory-tour.mp4</video:content_loc>
      <video:family_friendly>yes</video:family_friendly>
      <video:live>no</video:live>
    </video:video>
  </url>
</urlset>
"""


def main():
    global DO_IMG
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-img", action="store_true")
    a = ap.parse_args()
    DO_IMG = not a.no_img
    site = Site()
    site.build()
    n = flush()
    print("pages written: %d files (%d changed); products %d, cases %d, images %d" % (len(WRITES), n, len(site.products), len(site.cases), len(_IMG)))


if __name__ == "__main__":
    main()
