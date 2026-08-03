# -*- coding: utf-8 -*-
"""One-shot SEO optimization for EASEN static site root pages."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

META = {
    "index.html": {
        "title": "EASEN Commercial Furniture | Hotel, Restaurant & Cafe Manufacturer",
        "description": (
            "EASEN manufactures custom commercial furniture for hotels, restaurants, cafes and outdoor spaces. "
            "20+ years experience, 3000+ projects in 50+ countries. 7-day sampling, factory-direct pricing."
        ),
    },
    "products.html": {
        "title": "Commercial Furniture Catalog | Restaurant, Hotel, Cafe & Outdoor — EASEN",
        "description": (
            "Browse 300+ commercial furniture products: restaurant chairs & booths, hotel seating, cafe tables, "
            "and outdoor furniture. Custom OEM/ODM from Foshan factory. Free quote within 24 hours."
        ),
    },
    "cases.html": {
        "title": "Commercial Furniture Case Studies Worldwide — EASEN Projects",
        "description": (
            "Explore real hotel, restaurant, cafe and outdoor furniture projects by EASEN across 50+ countries. "
            "See custom commercial space solutions, materials and finished installations."
        ),
    },
    "about.html": {
        "title": "About EASEN | Commercial Furniture Manufacturer in Foshan, China",
        "description": (
            "EASEN is a Foshan-based commercial furniture manufacturer founded in 2016, with 20 years industry expertise, "
            "10,000㎡ factory capacity and export experience to 50+ countries. Learn our story, process and quality system."
        ),
    },
    "contact.html": {
        "title": "Contact EASEN | Free Commercial Furniture Quote in 24 Hours",
        "description": (
            "Contact EASEN for a free commercial furniture quote. WhatsApp/phone +86 15011641080, email chinaeasen@outlook.com. "
            "Custom hotel, restaurant and cafe furniture — factory-direct from Foshan, China."
        ),
    },
    "visualizer.html": {
        "title": "AI Furniture Visualizer | Preview EASEN Pieces in Your Space",
        "description": (
            "Upload a photo of your restaurant, hotel or cafe and preview EASEN commercial furniture with AI. "
            "Free visualizer — get a customized quote after your room preview."
        ),
    },
    "case-hotel.html": {
        "title": "New York Luxury Hotel Furniture Project — EASEN Case Study",
        "description": (
            "Case study: custom upholstered hotel furniture for a New York luxury property — sofas, lounge chairs, "
            "booths and dining chairs as a coordinated commercial furniture package by EASEN."
        ),
    },
    "case-restaurant.html": {
        "title": "Singapore Hotel Dining Furniture Project — EASEN Case Study",
        "description": (
            "Case study: Singapore luxury hotel dining space furniture by EASEN — space planning to installation, "
            "including restaurant seating, tables and coordinated commercial interiors."
        ),
    },
    "case-cafe.html": {
        "title": "Cafe Chain Furniture Project — Custom Commercial Seating | EASEN",
        "description": (
            "Full custom commercial furniture for cafe chain projects — consistent batch production, durable materials "
            "and multi-location rollout support from EASEN factory."
        ),
    },
    "case-outdoor.html": {
        "title": "Outdoor Dining Furniture Project — Weatherproof Commercial Sets | EASEN",
        "description": (
            "Outdoor commercial dining furniture case by EASEN — weather-resistant materials with refined aesthetics "
            "for rooftop, terrace and open-air hospitality spaces."
        ),
    },
    "insight-furniture-guide.html": {
        "title": "PU Leather vs Fabric for Restaurant Booths — Buyer Guide | EASEN",
        "description": (
            "Compare PU leather and fabric for restaurant booths: durability, cleaning, comfort and cost. "
            "A practical commercial furniture buyer guide from EASEN manufacturers."
        ),
    },
    "insight-project-cafe.html": {
        "title": "Cafe Furniture Engineering Case — Custom Fit-Out Insights | EASEN",
        "description": (
            "How EASEN engineers custom cafe furniture for contemporary spaces — layout, materials, production "
            "and installation lessons for hospitality fit-outs."
        ),
    },
    "insight-quality-compliance.html": {
        "title": "Furniture Pre-Shipment Inspection Process — Quality Control | EASEN",
        "description": (
            "See how EASEN inspects commercial furniture before shipping: materials, structure, finish and packaging checks "
            "that protect export quality for hotel and restaurant projects."
        ),
    },
}

FACTORY_ALTS = {
    "factory-1.png": "EASEN commercial furniture factory production floor in Foshan",
    "factory-2.jpg": "EASEN factory workshop manufacturing commercial seating",
    "factory-3.jpg": "EASEN quality inspection of commercial furniture",
    "factory-4.jpg": "EASEN furniture production line and craftsmanship",
    "factory-5.jpg": "EASEN warehouse ready commercial furniture shipments",
    "factory-6.jpg": "EASEN commercial furniture materials and frames",
    "factory-7.jpg": "EASEN factory team assembling hospitality furniture",
    "factory-8.jpg": "EASEN showroom sample commercial furniture display",
}


def set_attr_content(html, attr_name, attr_value, new_content):
    patterns = [
        (
            rf'(<meta\s+[^>]*\b{attr_name}=["\']{re.escape(attr_value)}["\'][^>]*\bcontent=["\'])([^"\']*)(["\'])',
            rf"\g<1>{new_content}\g<3>",
        ),
        (
            rf'(<meta\s+[^>]*\bcontent=["\'])([^"\']*)(["\'][^>]*\b{attr_name}=["\']{re.escape(attr_value)}["\'])',
            rf"\g<1>{new_content}\g<3>",
        ),
    ]
    out = html
    for pat, rep in patterns:
        out2, n = re.subn(pat, rep, out, count=1, flags=re.I)
        if n:
            return out2, True
    return out, False


def set_title(html, new_title):
    out, n = re.subn(
        r"(<title>)(.*?)(</title>)",
        rf"\g<1>{new_title}\g<3>",
        html,
        count=1,
        flags=re.I | re.S,
    )
    return out, n > 0


def add_factory_alts(html):
    def repl(m):
        tag = m.group(0)
        if re.search(r"\balt\s*=", tag, re.I):
            return tag
        src = re.search(r'src=["\']([^"\']+)["\']', tag, re.I)
        if not src:
            return tag
        name = Path(src.group(1)).name
        alt = FACTORY_ALTS.get(name, "EASEN commercial furniture factory photo")
        if tag.endswith("/>"):
            return tag[:-2] + f' alt="{alt}" />'
        if tag.endswith(">"):
            return tag[:-1] + f' alt="{alt}">'
        return tag

    return re.sub(r"<img\b[^>]*>", repl, html, flags=re.I)


def update_meta_pages():
    for page, pack in META.items():
        p = ROOT / page
        if not p.exists():
            print("MISSING", page)
            continue
        text = p.read_text(encoding="utf-8")
        orig = text
        text, ok_t = set_title(text, pack["title"])
        text, ok_d = set_attr_content(text, "name", "description", pack["description"])
        for prop in ["og:title"]:
            text, _ = set_attr_content(text, "property", prop, pack["title"])
        for prop in ["twitter:title"]:
            text, _ = set_attr_content(text, "name", prop, pack["title"])
        for prop in ["og:description"]:
            text, _ = set_attr_content(text, "property", prop, pack["description"])
        for prop in ["twitter:description"]:
            text, _ = set_attr_content(text, "name", prop, pack["description"])
        if text != orig:
            p.write_text(text, encoding="utf-8")
            print(
                f"updated meta: {page} title_ok={ok_t} desc_ok={ok_d} "
                f"lenT={len(pack['title'])} lenD={len(pack['description'])}"
            )
        else:
            print(f"no change: {page}")


def update_visualizer():
    vp = ROOT / "visualizer.html"
    vt = vp.read_text(encoding="utf-8")
    pack = META["visualizer.html"]
    if 'property="og:title"' not in vt and "property='og:title'" not in vt:
        insert = "\n".join(
            [
                f'<meta property="og:title" content="{pack["title"]}"/>',
                f'<meta property="og:description" content="{pack["description"]}"/>',
                '<meta property="og:type" content="website"/>',
                '<meta property="og:url" content="https://chinaeasen.com/visualizer.html"/>',
                '<meta property="og:image" content="https://chinaeasen.com/images/og-image.jpg"/>',
                '<meta property="og:site_name" content="EASEN Commercial Furniture"/>',
                '<meta name="twitter:card" content="summary_large_image"/>',
                f'<meta name="twitter:title" content="{pack["title"]}"/>',
                f'<meta name="twitter:description" content="{pack["description"]}"/>',
                '<meta name="twitter:image" content="https://chinaeasen.com/images/og-image.jpg"/>',
                '<meta name="robots" content="index, follow"/>',
                (
                    '<script type="application/ld+json">'
                    '{"@context":"https://schema.org","@type":"WebApplication",'
                    '"name":"EASEN AI Furniture Visualizer",'
                    '"url":"https://chinaeasen.com/visualizer.html",'
                    '"applicationCategory":"DesignApplication","operatingSystem":"Web",'
                    '"description":"AI room preview tool for EASEN commercial furniture in hotels, restaurants and cafes.",'
                    '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},'
                    '"provider":{"@type":"Organization","name":"EASEN Commercial Furniture","url":"https://chinaeasen.com/"}}'
                    "</script>"
                ),
            ]
        )
        vt = vt.replace("</head>", insert + "\n</head>", 1)
        print("visualizer: OG/Twitter/JSON-LD added")
    if "<h1" not in vt.lower():
        h1 = (
            '<h1 class="seo-h1" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;'
            "overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0\">"
            "AI Furniture Visualizer — Preview EASEN Commercial Furniture in Your Space</h1>\n"
        )
        vt = vt.replace('<div class="stage">', h1 + '  <div class="stage">', 1)
        print("visualizer: H1 added")
    vp.write_text(vt, encoding="utf-8")


def update_factory_alts():
    for page in ["index.html", "about.html"]:
        p = ROOT / page
        t = p.read_text(encoding="utf-8")
        nt = add_factory_alts(t)
        if nt != t:
            p.write_text(nt, encoding="utf-8")
            print("factory alts fixed:", page)


def update_cases_alts():
    cp = ROOT / "cases.html"
    ct = cp.read_text(encoding="utf-8")
    old1 = (
        "+'<div style=\"height:600px;overflow:hidden\"><img src=\"'+img+'\" "
        "style=\"width:100%;height:600px;object-fit:cover\" loading=\"lazy\"></div>'"
    )
    new1 = (
        "+'<div style=\"height:600px;overflow:hidden\"><img src=\"'+img+'\" "
        "style=\"width:100%;height:600px;object-fit:cover\" loading=\"lazy\" "
        "alt=\"'+title.replace(/\"/g,'&quot;')+'\"></div>'"
    )
    old2 = (
        "return '<img src=\"https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+img+'\" "
        "style=\"width:100%;height:auto;border-radius:8px;margin-bottom:8px\" loading=\"lazy\">';"
    )
    new2 = (
        "return '<img src=\"https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+img+'\" "
        "style=\"width:100%;height:auto;border-radius:8px;margin-bottom:8px\" loading=\"lazy\" "
        "alt=\"'+title.replace(/\"/g,'&quot;')+'\">';"
    )
    n = 0
    if old1 in ct:
        ct = ct.replace(old1, new1)
        n += 1
    if old2 in ct:
        ct = ct.replace(old2, new2)
        n += 1
    if n:
        cp.write_text(ct, encoding="utf-8")
        print("cases.html dynamic alts fixed:", n)
    else:
        print("WARN cases.html patterns not found")
        for i, line in enumerate(ct.splitlines(), 1):
            if "<img" in line and ("height:600px" in line or "raw.githubusercontent.com" in line):
                print(i, line[:220])


def update_products_alts():
    pp = ROOT / "products.html"
    pt = pp.read_text(encoding="utf-8")
    orig = pt

    def add_alt_if_missing(tag):
        if re.search(r"\balt\s*=", tag, re.I):
            return tag
        if tag.endswith("/>"):
            return tag[:-2] + ' alt="" />'
        if tag.endswith(">"):
            return tag[:-1] + ' alt="">'
        return tag

    # modal gallery template images
    pt = re.sub(
        r"<img src=\"'\+url\+'\"[^>]*>",
        lambda m: add_alt_if_missing(m.group(0)),
        pt,
    )
    pt = re.sub(
        r'<img id="lightbox-img"[^>]*>',
        lambda m: add_alt_if_missing(m.group(0)),
        pt,
    )
    if pt != orig:
        pp.write_text(pt, encoding="utf-8")
        print("products.html alts updated")
    else:
        print("products.html no alt changes needed/found")


def update_robots():
    text = """# Robots.txt for EASEN Commercial Furniture
# https://chinaeasen.com

User-agent: *
Allow: /
Disallow: /admin/
Disallow: /index-demo.html
Disallow: /*/index-demo.html
Disallow: /temp-preview/
Disallow: /tools/

# Host
Host: https://chinaeasen.com

# Sitemaps
Sitemap: https://chinaeasen.com/sitemap.xml
Sitemap: https://chinaeasen.com/video-sitemap.xml
"""
    (ROOT / "robots.txt").write_text(text, encoding="utf-8")
    print("robots.txt updated")


def patch_gen_i18n():
    gp = ROOT / "tools" / "gen_i18n.py"
    gt = gp.read_text(encoding="utf-8")
    orig = gt
    gt = gt.replace(
        'EXCLUDE_GEN = {"404.html"}',
        'EXCLUDE_GEN = {"404.html", "index-demo.html"}',
    )
    if "lastmod" not in gt:
        old = '''def write_sitemap(path, entries):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for page, L in entries:
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % page_url(page, L))
        for lg in ACTIVE_LANGS:
            lines.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (lg, page_url(page, lg)))
        lines.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % page_url(page, None))
        lines.append("  </url>")
    lines.append("</urlset>")
    open(path, "wb").write(("\\n".join(lines) + "\\n").encode("utf-8"))
'''
        new = '''def write_sitemap(path, entries):
    from datetime import date
    today = date.today().isoformat()
    def prio(page):
        if page in ("index.html",):
            return "1.0", "daily"
        if page in ("products.html", "cases.html", "contact.html"):
            return "0.9", "weekly"
        if page.startswith("case-") or page.startswith("insight-") or page == "about.html":
            return "0.8", "monthly"
        if page == "visualizer.html":
            return "0.7", "monthly"
        return "0.6", "monthly"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for page, L in entries:
        pr, cf = prio(page)
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % page_url(page, L))
        lines.append("    <lastmod>%s</lastmod>" % today)
        lines.append("    <changefreq>%s</changefreq>" % cf)
        lines.append("    <priority>%s</priority>" % pr)
        for lg in ACTIVE_LANGS:
            lines.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (lg, page_url(page, lg)))
        lines.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % page_url(page, None))
        lines.append("  </url>")
    lines.append("</urlset>")
    open(path, "wb").write(("\\n".join(lines) + "\\n").encode("utf-8"))
'''
        if old in gt:
            gt = gt.replace(old, new)
            print("write_sitemap enhanced")
        else:
            # fallback: inject after def line body using regex
            m = re.search(r"def write_sitemap\(path, entries\):\n", gt)
            if not m:
                print("WARN: write_sitemap not found")
            else:
                # replace whole function until next def
                m2 = re.search(r"\ndef write_sitemap_index\(", gt)
                if m2:
                    gt = gt[: m.start()] + new + "\n\n" + gt[m2.start() + 1 :]
                    print("write_sitemap enhanced via span replace")
    if gt != orig:
        gp.write_text(gt, encoding="utf-8")
        print("gen_i18n.py patched")
    else:
        print("gen_i18n.py unchanged")


def main():
    update_meta_pages()
    update_visualizer()
    update_factory_alts()
    update_cases_alts()
    update_products_alts()
    update_robots()
    patch_gen_i18n()
    print("SEO optimize done")


if __name__ == "__main__":
    main()
