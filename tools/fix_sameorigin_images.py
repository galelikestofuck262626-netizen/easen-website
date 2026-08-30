# -*- coding: utf-8 -*-
"""修复: 产品/案例图片与数据从 raw.githubusercontent.com 改为同源加载。

raw.githubusercontent.com 在中国大陆基本被墙、海外偶发限流,
而主站 chinaeasen.com (GitHub Pages) 可正常访问,
因此"网站能开但图片/数据加载失败"。图片本来就随仓库发布,
改用同源绝对路径 (/images/..., /data/...) 即可。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 内联 SVG 占位图 (data URI), 替代外部 via.placeholder.com / images.unsplash.com
PLACEHOLDER = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300'>"
    "<rect width='100%25' height='100%25' fill='%23e5e7eb'/>"
    "<text x='50%25' y='50%25' fill='%239ca3af' font-family='sans-serif' "
    "font-size='16' text-anchor='middle' dominant-baseline='middle'>EASEN</text></svg>"
)

REPLACEMENTS = {
    # ---- js/products.js ----
    "js/products.js": [
        (
            'var imgUrl="https://raw.githubusercontent.com/"+REPO+"/"+BRANCH+p.main_image;',
            'var imgUrl=p.main_image||"";',
        ),
        (
            'fetch("https://raw.githubusercontent.com/"+REPO+"/"+BRANCH+"/data/products-i18n.json?t="+Date.now())',
            'fetch("/data/products-i18n.json?t="+Date.now())',
        ),
        (
            'fetch("https://raw.githubusercontent.com/"+REPO+"/"+BRANCH+"/data/products.json?t="+Date.now())',
            'fetch("/data/products.json?t="+Date.now())',
        ),
    ],
    # ---- products.html (根版; 语言版由 gen_i18n 重新生成) ----
    "products.html": [
        (
            "const r = await fetch('https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+'/data/products.json?t='+Date.now());",
            "const r = await fetch('/data/products.json?t='+Date.now());",
        ),
        (
            "const ri = await fetch('https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+'/data/products-i18n.json?t='+Date.now());",
            "const ri = await fetch('/data/products-i18n.json?t='+Date.now());",
        ),
        (
            "      ? 'https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+p.main_image\n      : 'https://via.placeholder.com/400x300?text=No+Image';",
            f"      ? p.main_image\n      : '{PLACEHOLDER}';",
        ),
        (
            "var url = 'https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+img;",
            "var url = img;",
        ),
    ],
    # ---- cases.html (根版) ----
    "cases.html": [
        (
            "const r = await fetch('https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+'/data/cases.json?t='+Date.now());",
            "const r = await fetch('/data/cases.json?t='+Date.now());",
        ),
        (
            "var imgBase = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? '' : 'https://raw.githubusercontent.com/'+REPO+'/'+BRANCH;",
            "var imgBase = '';",
        ),
        (
            "var img = c.cover_image ? imgBase+c.cover_image : 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&q=80';",
            f"var img = c.cover_image ? imgBase+c.cover_image : '{PLACEHOLDER}';",
        ),
        (
            "return '<img src=\"https://raw.githubusercontent.com/'+REPO+'/'+BRANCH+img+'\" style=\"width:100%;height:auto;border-radius:8px;margin-bottom:8px\" loading=\"lazy\" alt=\"'+title.replace(/\"/g,'&quot;')+'\">';",
            "return '<img src=\"'+img+'\" style=\"width:100%;height:auto;border-radius:8px;margin-bottom:8px\" loading=\"lazy\" alt=\"'+title.replace(/\"/g,'&quot;')+'\">';",
        ),
    ],
}


def patch_file(rel, pairs):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    orig = t
    for old, new in pairs:
        if old not in t:
            print(f"  WARN not found in {rel}: {old[:90]}...")
            continue
        t = t.replace(old, new)
    if t != orig:
        p.write_text(t, encoding="utf-8")
        print(f"patched {rel}")
    else:
        print(f"no change {rel}")


def main():
    for rel, pairs in REPLACEMENTS.items():
        patch_file(rel, pairs)

    # 移除产品 1781457330360 引用的不存在图片 啊啊.png (会造成 404 裂图)
    dp = ROOT / "data" / "products.json"
    pr = json.loads(dp.read_text(encoding="utf-8"))
    changed = 0
    for x in pr:
        imgs = x.get("images") or []
        if any(str(i).endswith("啊啊.png") for i in imgs):
            x["images"] = [i for i in imgs if not str(i).endswith("啊啊.png")]
            changed += 1
            print(f"removed 啊啊.png from product {x.get('id')} {x.get('title_zh')}")
    if changed:
        dp.write_text(json.dumps(pr, ensure_ascii=False, indent=2), encoding="utf-8")

    # 校验: 前端文件不应再有 raw.githubusercontent / 外部占位图
    left = []
    for pat in ["raw.githubusercontent.com", "via.placeholder.com", "images.unsplash.com"]:
        for p in list(ROOT.glob("*.html")) + [ROOT / "js" / "products.js", ROOT / "js" / "components.js"]:
            if p.name == "index-demo.html":
                continue
            if pat in p.read_text(encoding="utf-8"):
                left.append((str(p), pat))
    print("remaining external refs:", left if left else "NONE")
    print("done")


if __name__ == "__main__":
    main()
