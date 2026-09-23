# -*- coding: utf-8 -*-
"""SEO 构建(幂等,可反复跑;产品/着陆页有变动后重跑一次即可)

  python tools/seo_build.py          写入
  python tools/seo_build.py --check  只报告会改哪些文件

做的事:
  1. en/ 下 13 个 B2B 着陆页: 补 hreflang(en + x-default) / FAQPage 结构化数据 /
     底部「相关方案」互链区块(每页链到其余着陆页 + 解决方案总览 + 产品 + 案例)
  2. 生成解决方案总览页 en/solutions.html(着陆页的入口 hub)
  3. products/<cat>/index.html: 把全部产品静态渲染进 .grid(无 JS 的爬虫也能读到
     产品名/图片/alt),并附 ItemList 结构化数据; js/products.js 渲染前会先清空
  4. sitemap-landing.xml(着陆页 + hub + 产品分类页) 与 sitemap-images.xml(产品图 + 案例图)
     gen_i18n.py 生成 sitemap.xml 索引时会自动带上这两个文件
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://chinaeasen.com"
CHECK = "--check" in sys.argv
ROOT_PAGES = {f for f in os.listdir(ROOT) if f.endswith(".html")}
CATS = {
    "restaurant": ("Restaurant Furniture", "餐厅家具", "restaurant"),
    "cafe": ("Café Furniture", "咖啡厅家具", "café"),
    "outdoor": ("Outdoor Furniture", "户外家具", "outdoor"),
}
TYPE_EN = {"chair": "chair", "booth": "booth seating", "table": "table", "sofa": "sofa", "stool": "bar stool"}
changed = []


def rd(p):
    with open(os.path.join(ROOT, p), "rb") as f:
        return f.read().decode("utf-8")


def wr(p, text):
    full = os.path.join(ROOT, p)
    old = open(full, "rb").read() if os.path.exists(full) else None
    raw = open(full, "rb").read().decode("utf-8") if old is not None else ""
    nl = "\r\n" if "\r\n" in raw else "\n"
    data = text.replace("\r\n", "\n").replace("\n", nl).encode("utf-8")
    if old == data:
        return
    changed.append(p)
    if not CHECK:
        with open(full, "wb") as f:
            f.write(data)


def put_block(text, name, block, anchor_re, before=True):
    """把 <!-- SEO:name:START -->...END 块写到锚点前/后;已有块则原地替换"""
    s, e = "<!-- SEO:%s:START -->" % name, "<!-- SEO:%s:END -->" % name
    full = s + block + e
    if s in text:
        return re.sub(re.escape(s) + ".*?" + re.escape(e), lambda _: full, text, count=1, flags=re.S)
    m = re.search(anchor_re, text)
    if not m:
        raise SystemExit("锚点找不到: %s" % anchor_re)
    i = m.start() if before else m.end()
    return text[:i] + full + "\n" + text[i:]


def strip_tags(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


# ---------------------------------------------------------------- 1. 着陆页
landing = sorted(f for f in os.listdir(os.path.join(ROOT, "en"))
                 if f.endswith(".html") and f not in ROOT_PAGES and f != "solutions.html")
info = {}
for f in landing:
    t = rd("en/" + f)
    h1 = strip_tags(re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S).group(1))
    desc = re.search(r'<meta name="description" content="([^"]*)"', t).group(1)
    info[f] = (h1, html.unescape(desc))


def faq_items(t):
    m = re.search(r'<section id="faq"[^>]*>(.*?)</section>', t, re.S)
    if not m:
        return []
    body = m.group(1)
    parts = re.split(r"<h[34][^>]*>(.*?)</h[34]>", body, flags=re.S)
    items = []
    for i in range(1, len(parts) - 1, 2):
        q = strip_tags(parts[i])
        a = strip_tags(parts[i + 1])
        if not q.endswith("?") or len(a) < 20:
            continue
        if len(a) > 700:
            a = a[:700].rsplit(" ", 1)[0] + " …"
        items.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    return items


def related_html(cur):
    links = "".join(
        '<a href="/en/%s" style="display:block;padding:14px 16px;background:#fff;border:1px solid #e5e7eb;'
        'border-radius:10px;color:#1a365d;text-decoration:none;font-weight:600;font-size:15px;line-height:1.4">%s</a>'
        % (f, html.escape(info[f][0])) for f in landing if f != cur)
    return (
        '\n<section style="padding:56px 20px;background:#f8f7f4" aria-label="Related solutions">'
        '<div style="max-width:1100px;margin:0 auto">'
        '<h2 style="font-size:1.8em;color:#1a365d;text-align:center;margin-bottom:28px">More Commercial Furniture Solutions from EASEN</h2>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">' + links + '</div>'
        '<p style="text-align:center;margin:28px 0 0;font-size:15px">'
        '<a href="/en/solutions.html" style="color:#c8a45c;font-weight:700">All solutions</a> · '
        '<a href="/en/products.html" style="color:#c8a45c;font-weight:700">Product catalog</a> · '
        '<a href="/en/cases.html" style="color:#c8a45c;font-weight:700">Project cases</a> · '
        '<a href="/en/" style="color:#c8a45c;font-weight:700">EASEN home</a></p>'
        '</div></section>\n')


for f in landing:
    p = "en/" + f
    t = rd(p)
    url = "%s/en/%s" % (DOMAIN, f)
    t = put_block(t, "HREFLANG",
                  '<link rel="alternate" hreflang="en" href="%s"/><link rel="alternate" hreflang="x-default" href="%s"/>'
                  % (url, url), r'<link rel="canonical"[^>]*>', before=False)
    faq = faq_items(t)
    if faq:
        ld = {"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "mainEntity": faq}
        t = put_block(t, "FAQ", '<script type="application/ld+json">%s</script>'
                      % json.dumps(ld, ensure_ascii=False, separators=(",", ":")), r"</head>")
    t = put_block(t, "RELATED", related_html(f), r"<footer\b")
    t = re.sub(r"&copy; 20\d\d EASEN", "&copy; 2026 EASEN", t)
    wr(p, t)

# ---------------------------------------------------------------- 2. hub 页
cards = "".join(
    '<a class="card" href="/en/%s"><h2>%s</h2><p>%s</p><span>Read more →</span></a>'
    % (f, html.escape(h1), html.escape(desc)) for f, (h1, desc) in info.items())
hub_url = DOMAIN + "/en/solutions.html"
hub_ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "CollectionPage", "@id": hub_url, "url": hub_url, "inLanguage": "en",
     "name": "Commercial Furniture Solutions by Venue & Product | EASEN",
     "description": "Guides to EASEN's commercial furniture manufacturing: booths, banquettes, restaurant chairs and tables, bar, café, hotel, fine dining, fast food and outdoor furniture from Foshan, China."},
    {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": "%s/en/%s" % (DOMAIN, f), "name": info[f][0]}
        for i, f in enumerate(info)]},
    {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/en/"},
        {"@type": "ListItem", "position": 2, "name": "Solutions", "item": hub_url}]}]}
hub = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Commercial Furniture Solutions by Venue & Product | EASEN</title>
<meta name="description" content="Guides to EASEN's commercial furniture manufacturing: custom booths, banquettes, restaurant chairs and tables, bar, café, hotel, fine dining, fast food and outdoor furniture. Factory-direct from Foshan, China since 2016.">
<link rel="canonical" href="%(u)s"/>
<link rel="alternate" hreflang="en" href="%(u)s"/><link rel="alternate" hreflang="x-default" href="%(u)s"/>
<meta property="og:type" content="website"/><meta property="og:url" content="%(u)s"/>
<meta property="og:title" content="Commercial Furniture Solutions by Venue & Product | EASEN"/>
<meta property="og:description" content="Custom booths, restaurant chairs and tables, bar, café, hotel and outdoor furniture — factory-direct from Foshan, China."/>
<meta property="og:image" content="%(d)s/images/hero/hero-main.jpg"/>
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<script type="application/ld+json">%(ld)s</script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#333;line-height:1.65;background:#f8f7f4}
header{background:#1a365d;color:#fff;padding:72px 20px 56px;text-align:center}
header h1{font-size:2.4em;line-height:1.2;margin-bottom:14px}
header p{max-width:760px;margin:0 auto;opacity:.9;font-size:1.1em}
nav{background:#fff;border-bottom:1px solid #e5e7eb;padding:14px 20px;text-align:center}
nav a{color:#1a365d;text-decoration:none;font-weight:600;margin:0 14px}
main{max-width:1100px;margin:0 auto;padding:48px 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.card{display:block;background:#fff;border-radius:12px;padding:28px;text-decoration:none;color:#333;box-shadow:0 1px 4px rgba(16,24,40,.06);transition:box-shadow .3s,transform .3s}
.card:hover{box-shadow:0 14px 30px rgba(16,24,40,.12);transform:translateY(-4px)}
.card h2{font-size:1.25em;color:#1a365d;margin-bottom:10px;line-height:1.3}
.card p{font-size:.95em;color:#555;margin-bottom:14px}
.card span{color:#c8a45c;font-weight:700;font-size:.95em}
.cta{text-align:center;margin-top:48px}
.cta a{display:inline-block;background:#c8a45c;color:#fff;padding:16px 40px;border-radius:8px;text-decoration:none;font-weight:700}
footer{background:#1a1a1a;color:#aaa;text-align:center;padding:28px 20px;font-size:14px}
@media(max-width:640px){header h1{font-size:1.8em}nav a{display:inline-block;margin:4px 8px}}
</style>
</head>
<body>
<header><h1>Commercial Furniture Solutions</h1>
<p>EASEN is a commercial furniture manufacturer in Foshan, China, founded in 2016. Explore our guides by venue and product type — each covers materials, customization, lead times and how we work with restaurant, hotel and café projects worldwide.</p></header>
<nav><a href="/en/">Home</a><a href="/en/products.html">Products</a><a href="/en/cases.html">Cases</a><a href="/en/about.html">About</a><a href="/en/contact.html">Get a Quote</a></nav>
<main><div class="grid">%(cards)s</div>
<div class="cta"><a href="/en/contact.html">Request a Project Quote</a></div></main>
<footer>&copy; 2026 EASEN Commercial Furniture — Foshan, Guangdong, China · chinaeasen@outlook.com · +86 15011641080</footer>
</body>
</html>
""" % {"u": hub_url, "d": DOMAIN, "cards": cards, "ld": json.dumps(hub_ld, ensure_ascii=False, separators=(",", ":"))}
wr("en/solutions.html", hub)

# ---------------------------------------------------------------- 3. 产品分类页静态目录
products = json.loads(rd("data/products.json"))
live = [p for p in products if p.get("status") in ("online", None, "")]
by_cat = {}
for p in live:
    by_cat.setdefault(p.get("category"), []).append(p)


def alt_of(p, cat):
    en = (p.get("title_en") or p.get("title_zh") or "").strip()
    kind = TYPE_EN.get(p.get("type"), "furniture")
    return "%s — commercial %s %s | EASEN" % (en, CATS[cat][2], kind)


for cat in CATS:
    page = "products/%s/index.html" % cat
    items = list(reversed(by_cat.get(cat, [])))   # 与 js/products.js 同序(新品在前)
    if not items:
        continue
    t = rd(page)
    cards = "".join(
        '<div class="group block bg-white rounded-2xl overflow-hidden cf-pcard" data-static="1">'
        '<div class="aspect-[4/3] overflow-hidden"><img src="%s" style="width:100%%;height:100%%;object-fit:cover" loading="lazy" alt="%s"></div>'
        '<div class="p-6"><h3 class="text-xl font-heading font-semibold text-primary mb-2">'
        '<span data-lang="zh">%s</span><span data-lang="en">%s</span></h3></div></div>'
        % (html.escape(p.get("main_image") or ""), html.escape(alt_of(p, cat), quote=True),
           html.escape(p.get("title_zh") or p.get("title_en") or ""), html.escape(p.get("title_en") or p.get("title_zh") or ""))
        for p in items)
    t = put_block(t, "CATALOG", cards, r'<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">', before=False)
    url = "%s/products/%s/" % (DOMAIN, cat)
    ld = {"@context": "https://schema.org", "@type": "ItemList", "@id": url + "#catalog",
          "name": "EASEN %s catalog" % CATS[cat][0], "numberOfItems": len(items),
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": (p.get("title_en") or p.get("title_zh")),
                               "image": DOMAIN + (p.get("main_image") or "")} for i, p in enumerate(items)]}
    t = put_block(t, "ITEMLIST", '<script type="application/ld+json">%s</script>'
                  % json.dumps(ld, ensure_ascii=False, separators=(",", ":")), r"</head>")
    wr(page, t)

# ---------------------------------------------------------------- 4. sitemaps
def x(s):
    return html.escape(s, quote=True)


urls = ["%s/en/solutions.html" % DOMAIN] + ["%s/en/%s" % (DOMAIN, f) for f in landing]
for cat in list(CATS) + ["hotel"]:
    if os.path.exists(os.path.join(ROOT, "products", cat, "index.html")):
        urls.append("%s/products/%s/" % (DOMAIN, cat))
        for sub in sorted(os.listdir(os.path.join(ROOT, "products", cat))):
            if os.path.isfile(os.path.join(ROOT, "products", cat, sub, "index.html")):
                urls.append("%s/products/%s/%s/" % (DOMAIN, cat, sub))
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    pr = "0.8" if "/en/" in u else "0.7"
    sm.append("  <url><loc>%s</loc><changefreq>monthly</changefreq><priority>%s</priority></url>" % (x(u), pr))
sm.append("</urlset>")
wr("sitemap-landing.xml", "\n".join(sm) + "\n")

img = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
for cat in CATS:
    items = by_cat.get(cat, [])
    if not items:
        continue
    img.append("  <url><loc>%s/products/%s/</loc>" % (DOMAIN, cat))
    for p in items:
        for src in (p.get("images") or [])[:3]:
            img.append("    <image:image><image:loc>%s</image:loc><image:title>%s</image:title></image:image>"
                       % (x(DOMAIN + src), x(alt_of(p, cat))))
    img.append("  </url>")
cases = json.loads(rd("data/cases.json"))
img.append("  <url><loc>%s/cases.html</loc>" % DOMAIN)
seen = set()
for c in cases:
    for src in (c.get("images") or [])[:4]:
        if src in seen or not src.startswith("/"):
            continue
        seen.add(src)
        img.append("    <image:image><image:loc>%s</image:loc><image:title>%s</image:title></image:image>"
                   % (x(DOMAIN + src), x(c.get("title_en") or c.get("title_zh") or "EASEN project")))
img.append("  </url>")
img.append("</urlset>")
wr("sitemap-images.xml", "\n".join(img) + "\n")

print(("会改" if CHECK else "已改") + " %d 个文件" % len(changed))
for c in changed:
    print("  " + c)
