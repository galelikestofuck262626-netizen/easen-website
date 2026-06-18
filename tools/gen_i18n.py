# -*- coding: utf-8 -*-
"""
gen_i18n.py — 从根目录多语言页面生成 /zh /en /fr /es /de /ar 单语言静态页。
纯标准库。可重跑幂等。详见 plan：fluttering-cuddling-sky.md。

用法:
  python tools/gen_i18n.py                 # 全语言、全营销页
  python tools/gen_i18n.py --langs en,zh   # 指定语言
  python tools/gen_i18n.py --pages index.html,about.html
  python tools/gen_i18n.py --no-clean      # 不先清空语言目录（调试用）

核心策略:
  - 解析裁剪: 手动扫描 <span data-lang="X"> 配对(跳过 script/style 区段)，逆序切片
    删除非目标语言 span，保留目标语言并去 display:none。缺目标语言回退 en->zh。
  - 路径改写: 仅在 script/style 区段之外，把相对 images//videos//js/ 改根绝对、
    站内 *.html 内链改 /L/*.html、内联 url(images/..) 改 /images/..。
  - head: <html lang>(ar 加 dir=rtl)、canonical 自指、I18N:HREFLANG 标记块注入完整集群。
  - 护栏: 生成页与源页的 <script>/<style> 区段必须字节完全一致，否则中止。
"""
import os, re, sys, shutil, json, html

ROOT = r"G:\网站代码\easen-netlify-deploy-clean"
DOMAIN = "https://chinaeasen.com"
LANGS = ["zh", "en", "fr", "es", "de", "ar"]
ACTIVE_LANGS = LANGS[:]  # 本次生成/部署的语言集合(决定 hreflang 集群只引用已存在的语言)
OG_LOCALE = {"zh": "zh_CN", "en": "en_US", "fr": "fr_FR", "es": "es_ES", "de": "de_DE", "ar": "ar_AR"}
# 不生成 /L/404.html（GitHub Pages 只用根 /404.html）
EXCLUDE_GEN = {"404.html"}

# 翻译词典(从 lang.js 的 T 抽取, 与运行时同源)。fr/es/de/ar 对 en 回退文本套用。
def _load_json(name):
    try:
        return json.load(open(os.path.join(os.path.dirname(__file__), name), encoding="utf-8"))
    except Exception:
        return {}


DICT = _load_json("i18n_dict.json")          # 从 lang.js 抽取的常用词典
_extra = _load_json("i18n_extra.json")        # 补译(详情页长文本)
for _L, _m in (_extra or {}).items():
    DICT.setdefault(_L, {}).update(_m)


def norm_key(s):
    s = (s.replace("’", "'").replace("‘", "'").replace("”", '"')
         .replace("“", '"').replace("—", "--").replace("–", "-"))
    return re.sub(r"\s+", " ", s).strip()


MISSES = {}  # L -> set(未被词典覆盖的英文串)


def translate(inner_html, L):
    """把 en span 的纯文本内容译成 L(查 DICT)。有嵌套标签或查不到则返回 None(保留英文)。"""
    if "<" in inner_html:
        return None
    raw = html.unescape(inner_html).strip()
    if not raw:
        return None
    d = DICT.get(L, {})
    t = d.get(norm_key(raw)) or d.get(raw)
    if t is None:
        MISSES.setdefault(L, set()).add(raw)
        return None
    return html.escape(t, quote=False)


MASK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)
TAG_RE = re.compile(r"<(/?)span\b([^>]*)>", re.I)
DATALANG_RE = re.compile(r'data-lang\s*=\s*"([^"]*)"', re.I)


def list_root_pages():
    return sorted(f for f in os.listdir(ROOT)
                  if f.endswith(".html") and os.path.isfile(os.path.join(ROOT, f)))


def masked_spans(text):
    return [(m.start(), m.end()) for m in MASK_RE.finditer(text)]


def in_masked(pos, masked):
    for a, b in masked:
        if a <= pos < b:
            return True
    return False


def find_lang_spans(text, masked):
    """返回顶层 data-lang span: (start, content_start, end, lang)。跳过 script/style。"""
    spans, stack, dl_depth = [], [], 0
    for m in TAG_RE.finditer(text):
        if in_masked(m.start(), masked):
            continue
        if m.group(1) != "/":            # 开标签 <span ...>
            dl = DATALANG_RE.search(m.group(2))
            lang = dl.group(1) if dl else None
            top = (lang is not None and dl_depth == 0)
            stack.append({"lang": lang, "is_dl": lang is not None,
                          "start": m.start(), "cstart": m.end(), "top": top})
            if lang is not None:
                dl_depth += 1
        else:                            # 闭标签 </span>
            if not stack:
                continue
            t = stack.pop()
            if t["is_dl"]:
                dl_depth -= 1
                if t["top"]:
                    spans.append((t["start"], t["cstart"], m.end(), t["lang"]))
    return spans


def group_spans(text, spans):
    """相邻(仅空白间隔)的顶层 data-lang span 归为一组。"""
    groups, cur = [], []
    for sp in spans:
        if cur and text[cur[-1][2]:sp[0]].strip() == "":
            cur.append(sp)
        else:
            if cur:
                groups.append(cur)
            cur = [sp]
    if cur:
        groups.append(cur)
    return groups


def fix_kept_starttag(starttag, L):
    # 保留的 span 统一改成 data-lang="L"(使 applyLang(L) 显示它)并去 display:none
    s = re.sub(r'data-lang="[^"]*"', 'data-lang="%s"' % L, starttag, count=1)
    s = s.replace(' style="display:none"', "")
    s = re.sub(r'(style=")display:\s*none;?\s*', r"\1", s)
    s = s.replace(' style=""', "")
    return s


def apply_edits(text, edits):
    """edits: list of (start, end, replacement)。逆序应用。"""
    for s, e, rep in sorted(edits, key=lambda x: x[0], reverse=True):
        text = text[:s] + rep + text[e:]
    return text


def trim_languages(text, L):
    masked = masked_spans(text)
    groups = group_spans(text, find_lang_spans(text, masked))
    edits = []
    for g in groups:
        has_L = any(sp[3] == L for sp in g)
        has_en = any(sp[3] == "en" for sp in g)
        for (s, cs, e, lang) in g:
            keep = (lang == L) or (not has_L and lang == "en") or \
                   (not has_L and not has_en and lang == "zh")
            if keep:
                st = text[s:cs]
                st2 = fix_kept_starttag(st, L)
                if st2 != st:
                    edits.append((s, cs, st2))
                # en 回退到 fr/es/de/ar 时, 用词典把内容译成目标语言
                if lang == "en" and not has_L and L in ("fr", "es", "de", "ar"):
                    inner = text[cs:e - 7]  # </span> = 7 chars
                    tr = translate(inner, L)
                    if tr is not None and tr != inner:
                        edits.append((cs, e - 7, tr))
            else:
                edits.append((s, e, ""))
    return apply_edits(text, edits)


def transform_seg(seg, L, whitelist):
    seg = re.sub(r'((?:src|href|srcset|poster)=")(images/|videos/|js/)', r"\1/\2", seg)

    def link_repl(m):
        fname = m.group(2)
        if fname in whitelist:
            return 'href="/' + L + "/" + fname + m.group(3)
        return m.group(0)
    seg = re.sub(r'(href=")([a-z0-9][a-z0-9\-]*\.html)((?:[#?][^"]*)?")', link_repl, seg)
    seg = re.sub(r"url\((['\"]?)(images/[^)'\"]*)(['\"]?)\)", r"url(\1/\2\3)", seg)
    return seg


def rewrite_paths(text, L, whitelist):
    masked = masked_spans(text)
    out, last = [], 0
    for a, b in masked:
        out.append(transform_seg(text[last:a], L, whitelist))
        out.append(text[a:b])
        last = b
    out.append(transform_seg(text[last:], L, whitelist))
    return "".join(out)


def page_url(page, lang):
    if lang is None:
        return DOMAIN + "/" + ("" if page == "index.html" else page)
    base = DOMAIN + "/" + lang + "/"
    return base if page == "index.html" else base + page


def hreflang_block(page, nl):
    lines = ['<link rel="alternate" hreflang="%s" href="%s"/>' % (lg, page_url(page, lg)) for lg in ACTIVE_LANGS]
    lines.append('<link rel="alternate" hreflang="x-default" href="%s"/>' % page_url(page, None))
    return "<!-- I18N:HREFLANG:START -->" + nl + nl.join(lines) + nl + "<!-- I18N:HREFLANG:END -->"


def update_root_hreflang(page):
    """把根页面的假 hreflang 改成真集群(标记块, 幂等)。只动 head, 不动 canonical/lang/script/style。"""
    fp = os.path.join(ROOT, page)
    raw = open(fp, "rb").read()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    before_mask = [m.group(0) for m in MASK_RE.finditer(text)]
    text = re.sub(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*"/>\r?\n?', "", text)
    text = re.sub(r"<!-- I18N:HREFLANG:START -->.*?<!-- I18N:HREFLANG:END -->\r?\n?", "", text, flags=re.S)
    m = re.search(r'<link rel="canonical" href="[^"]*"/>', text)
    if m:
        blk = m.group(0) + nl + hreflang_block(page, nl)
        text = text[:m.start()] + blk + text[m.end():]
    out = text.encode("utf-8")
    if [mm.group(0) for mm in MASK_RE.finditer(text)] != before_mask:
        raise SystemExit("GUARDRAIL FAILED(root hreflang): %s" % page)
    if out != raw:
        open(fp, "wb").write(out)


def write_sitemap(path, entries):
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
    open(path, "wb").write(("\n".join(lines) + "\n").encode("utf-8"))


def write_sitemap_index(path, subs):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for s in subs:
        lines.append("  <sitemap><loc>%s/%s</loc></sitemap>" % (DOMAIN, s))
    lines.append("</sitemapindex>")
    open(path, "wb").write(("\n".join(lines) + "\n").encode("utf-8"))


def gen_sitemaps(gen_pages):
    for L in ACTIVE_LANGS:
        write_sitemap(os.path.join(ROOT, "sitemap-%s.xml" % L), [(p, L) for p in gen_pages])
    write_sitemap(os.path.join(ROOT, "sitemap-root.xml"), [(p, None) for p in gen_pages])
    subs = ["sitemap-root.xml"] + ["sitemap-%s.xml" % L for L in ACTIVE_LANGS]
    if os.path.isfile(os.path.join(ROOT, "video-sitemap.xml")):
        subs.append("video-sitemap.xml")
    write_sitemap_index(os.path.join(ROOT, "sitemap.xml"), subs)


def head_edits(text, page, L, nl):
    text = text.replace('<html lang="zh">',
                        '<html lang="%s"%s>' % (L, ' dir="rtl"' if L == "ar" else ""), 1)
    # 告知 lang.js 当前已部署的语言集合(子目录切换器据此过滤, 避免跳到未生成的 /L/)
    text = text.replace("<head>", '<head>' + nl + '<meta name="i18n-langs" content="%s"/>'
                        % ",".join(ACTIVE_LANGS), 1)
    new_canon = '<link rel="canonical" href="%s"/>' % page_url(page, L)
    text = re.sub(r'<link rel="canonical" href="[^"]*"/>', lambda m: new_canon, text, count=1)
    text = re.sub(r'(<meta property="og:url" content=")[^"]*("/>)',
                  lambda m: m.group(1) + page_url(page, L) + m.group(2), text, count=1)
    text = re.sub(r'(<meta property="og:locale" content=")[^"]*("/>)',
                  lambda m: m.group(1) + OG_LOCALE[L] + m.group(2), text, count=1)
    # 去旧 hreflang 行 + 旧标记块（幂等）
    text = re.sub(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*"/>\r?\n?', "", text)
    text = re.sub(r"<!-- I18N:HREFLANG:START -->.*?<!-- I18N:HREFLANG:END -->\r?\n?", "", text, flags=re.S)
    text = text.replace(new_canon, new_canon + nl + hreflang_block(page, nl), 1)
    return text


def gen_page(src_text, page, L, whitelist, nl):
    text = trim_languages(src_text, L)
    text = rewrite_paths(text, L, whitelist)
    text = head_edits(text, page, L, nl)
    return text


def guardrail(src_text, gen_text, page, L):
    a = [m.group(0) for m in MASK_RE.finditer(src_text)]
    b = [m.group(0) for m in MASK_RE.finditer(gen_text)]
    if a != b:
        raise SystemExit("GUARDRAIL FAILED: script/style 区段被改动 @ %s [%s]" % (page, L))


def main():
    args = sys.argv[1:]
    langs = LANGS[:]
    pages = None
    do_clean = "--no-clean" not in args
    for a in args:
        if a.startswith("--langs"):
            langs = a.split("=", 1)[1].split(",") if "=" in a else None
        if a.startswith("--pages"):
            pages = a.split("=", 1)[1].split(",") if "=" in a else None
    # 支持 "--langs en,zh" 形式
    for i, a in enumerate(args):
        if a == "--langs" and i + 1 < len(args):
            langs = args[i + 1].split(",")
        if a == "--pages" and i + 1 < len(args):
            pages = args[i + 1].split(",")

    global ACTIVE_LANGS
    ACTIVE_LANGS = [l for l in LANGS if l in langs]  # 规范顺序

    all_pages = list_root_pages()
    whitelist = set(all_pages)
    gen_pages = [p for p in all_pages if p not in EXCLUDE_GEN]
    if pages:
        gen_pages = [p for p in gen_pages if p in pages]

    if do_clean:
        for L in langs:
            d = os.path.join(ROOT, L)
            if os.path.isdir(d):
                shutil.rmtree(d)

    total = 0
    for L in langs:
        os.makedirs(os.path.join(ROOT, L), exist_ok=True)
        for page in gen_pages:
            raw = open(os.path.join(ROOT, page), "rb").read()
            nl = "\r\n" if b"\r\n" in raw else "\n"
            src_text = raw.decode("utf-8")
            gen_text = gen_page(src_text, page, L, whitelist, nl)
            guardrail(src_text, gen_text, page, L)
            outp = os.path.join(ROOT, L, page)
            open(outp, "wb").write(gen_text.encode("utf-8"))
            total += 1
        print("  [%s] %d 页" % (L, len(gen_pages)))

    # 站点级步骤(仅全量运行: 未用 --pages 限定时)
    if not pages:
        for page in gen_pages:
            update_root_hreflang(page)
        gen_sitemaps(gen_pages)
        open(os.path.join(ROOT, ".nojekyll"), "wb").write(b"")
        print("  根页面 hreflang 已更新 + sitemap(%d lang)+index + .nojekyll" % len(ACTIVE_LANGS))

    if MISSES:
        allmiss = sorted(set().union(*MISSES.values()))
        with open(os.path.join(os.path.dirname(__file__), "i18n_missing.json"), "w", encoding="utf-8") as f:
            json.dump(allmiss, f, ensure_ascii=False, indent=0)
        print("  未译(词典未覆盖): " + " ".join("%s=%d" % (L, len(MISSES.get(L, set())))
                                            for L in ("fr", "es", "de", "ar") if L in ACTIVE_LANGS)
              + " | 唯一串=%d -> tools/i18n_missing.json" % len(allmiss))
    print("生成完成: %d 个文件 (langs=%s, pages=%d)" % (total, ",".join(ACTIVE_LANGS), len(gen_pages)))


if __name__ == "__main__":
    main()
