/* EASEN site runtime. Source: src/assets/site.js */
(function () {
  'use strict';
  var C = window.EASEN || {}, T = C.t || {}, L = C.L || 'en';
  var d = document, body = d.body;
  function $(s, r) { return (r || d).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ---------- header ---------- */
  var hdr = $('#hdr'), lastY = 0, over = body.classList.contains('over');
  function onScroll() {
    var y = window.scrollY || 0;
    if (over) hdr.classList.toggle('solid', y > 40);
    var hide = y > 480 && y > lastY + 4 && !body.classList.contains('lock');
    var show = y < lastY - 4 || y < 480;
    if (hide) { hdr.classList.add('hide'); body.classList.add('hdr-hidden'); }
    else if (show) { hdr.classList.remove('hide'); body.classList.remove('hdr-hidden'); }
    lastY = y;
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* ---------- mobile nav ---------- */
  var mnav = $('#mnav'), burger = $('.burger');
  function setNav(open) {
    mnav.classList.toggle('open', open); mnav.setAttribute('aria-hidden', open ? 'false' : 'true');
    burger.setAttribute('aria-expanded', open ? 'true' : 'false'); body.classList.toggle('lock', open);
  }
  if (burger) burger.addEventListener('click', function () { setNav(true); });
  if (mnav) { $('.mnav-close', mnav).addEventListener('click', function () { setNav(false); }); $$('a', mnav).forEach(function (a) { a.addEventListener('click', function () { setNav(false); }); }); }

  /* ---------- language memory ---------- */
  $$('[data-setlang]').forEach(function (a) { a.addEventListener('click', function () { store('easen-lang', a.getAttribute('data-setlang')); }); });

  /* ---------- reveal ---------- */
  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 }) : null;
  function reveal(root) { $$('.rv:not(.in)', root).forEach(function (el) { if (io) io.observe(el); else el.classList.add('in'); }); }
  reveal();

  /* ---------- motion (home hero, counters, marquee, parallax, cursor) ---------- */
  var RM = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  if ($('.intro')) { try { sessionStorage.setItem('easen-intro', '1'); } catch (e) {} }
  var d0 = d.documentElement.classList.contains('no-intro') ? 0.1 : 1.5;

  // headline: wrap words (CJK: characters) in masks so they rise line by line
  $$('[data-split]').forEach(function (h) {
    var i = 0, cjk = /[　-〿㐀-鿿＀-￯]/;
    function wrap(tok) { var o = d.createElement('span'), n = d.createElement('span'); o.className = 'w'; n.textContent = tok; n.style.setProperty('--i', i++); o.appendChild(n); return o; }
    function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var frag = d.createDocumentFragment();
          c.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) frag.appendChild(d.createTextNode(' '));
            else if (cjk.test(part)) Array.from(part).forEach(function (ch) { frag.appendChild(wrap(ch)); });
            else frag.appendChild(wrap(part));
          });
          node.replaceChild(frag, c);
        } else if (c.nodeType === 1 && c.tagName !== 'BR') walk(c);
      });
    }
    if (!RM) walk(h);
    h.classList.add('sp');
  });

  // hero: mouse drift + scroll progress, paused while off screen
  var hero = $('[data-hero]');
  if (hero && !RM) {
    var tx = 0, ty = 0, mx = 0, my = 0, heroOn = true;
    hero.addEventListener('mousemove', function (e) { var r = hero.getBoundingClientRect(); tx = (e.clientX - r.left) / r.width - 0.5; ty = (e.clientY - r.top) / r.height - 0.5; });
    hero.addEventListener('mouseleave', function () { tx = ty = 0; });
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { heroOn = es[0].isIntersecting; hero.classList.toggle('paused', !heroOn); }).observe(hero);
    (function loop() {
      if (heroOn) {
        mx += (tx - mx) * 0.05; my += (ty - my) * 0.05;
        var sy = Math.min(1, Math.max(0, (window.scrollY || 0) / (hero.offsetHeight || 1)));
        hero.style.setProperty('--mx', mx.toFixed(4)); hero.style.setProperty('--my', my.toFixed(4)); hero.style.setProperty('--sy', sy.toFixed(4));
      }
      requestAnimationFrame(loop);
    })();
  }

  // count-up figures
  $$('[data-count]').forEach(function (b) {
    var m = (b.textContent || '').trim().match(/^(\d[\d,.\s]*\d|\d)(\D.*)?$/); if (!m || RM) return;
    var raw = m[1], sep = (raw.match(/[,.\s]/) || [''])[0], to = +raw.replace(/[,.\s]/g, ''), suf = m[2] || '', t0 = 0, dur = 2000;
    function fmt(n) { return sep ? String(n).replace(/\B(?=(\d{3})+(?!\d))/g, sep) : String(n); }
    b.textContent = '0' + suf;
    function step(ts) { if (!t0) t0 = ts; var k = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(2, -10 * k); b.textContent = fmt(k >= 1 ? to : Math.round(to * e)) + suf; if (k < 1) requestAnimationFrame(step); }
    setTimeout(function () { requestAnimationFrame(step); }, (d0 + 0.9) * 1000);
  });

  // marquee leans with scroll speed; [data-par] images drift slower than the page
  var marq = $('.marq-in'), pars = $$('[data-par]');
  if (!RM && (marq || pars.length)) {
    var lastS = window.scrollY || 0, sk = 0;
    (function tick() {
      var y = window.scrollY || 0, v = y - lastS; lastS = y;
      sk += (Math.max(-10, Math.min(10, v * 0.3)) - sk) * 0.1;
      if (marq) marq.style.setProperty('--sk', sk.toFixed(2) + 'deg');
      var vh = window.innerHeight;
      pars.forEach(function (p) { var r = p.parentNode.getBoundingClientRect(); if (r.bottom < 0 || r.top > vh) return; p.style.setProperty('--py', (((r.top + r.height / 2) - vh / 2) / vh * -70).toFixed(1) + 'px'); });
      requestAnimationFrame(tick);
    })();
  }

  // "view" disc that follows the pointer over imagery (mouse only)
  if (!RM && window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches) {
    var cur = d.createElement('div'); cur.className = 'cur'; cur.setAttribute('aria-hidden', 'true');
    cur.innerHTML = '<i><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 12h15M13 6l6 6-6 6"/></svg></i>';
    body.appendChild(cur);
    var X = -200, Y = -200, cx = X, cy = Y;
    d.addEventListener('mousemove', function (e) {
      X = e.clientX; Y = e.clientY;
      cur.classList.toggle('on', !!(e.target.closest && e.target.closest('.col-card,.pf-media,.pcard .ph,.icard a,.ccard a,.masonry .ph,.gal .ph')));
    }, { passive: true });
    d.addEventListener('mouseleave', function () { cur.classList.remove('on'); });
    (function follow() { cx += (X - cx) * 0.2; cy += (Y - cy) * 0.2; cur.style.transform = 'translate3d(' + cx.toFixed(1) + 'px,' + cy.toFixed(1) + 'px,0)'; requestAnimationFrame(follow); })();
  }

  /* ---------- brand film band: muted loop (16:9 / 9:16 by screen) → click plays the full film in place ---------- */
  var filmBox = $('.film-box');
  if (filmBox) {
    var fl = $('.film-loop', filmBox), fx = $('.film-x', filmBox), narrow = matchMedia('(max-width:700px)').matches;
    var calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
    fl.poster = fl.getAttribute(narrow ? 'data-pv' : 'data-ph');
    var loopSrc = fl.getAttribute(narrow ? 'data-v' : 'data-h');
    var startLoop = function () { if (calm) return; if (fl.getAttribute('src') !== loopSrc) fl.src = loopSrc; var p = fl.play(); if (p && p.catch) p.catch(function () {}); };
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { es.forEach(function (e) { if (filmBox.classList.contains('playing')) return; if (e.isIntersecting) startLoop(); else fl.pause(); }); }, { rootMargin: '200px' }).observe(filmBox);
    } else startLoop();
    var stopFilm = function () {
      filmBox.classList.remove('playing'); fx.hidden = true;
      fl.muted = true; fl.loop = true; fl.controls = false; fl.src = loopSrc; startLoop();
    };
    $('.film-play', filmBox).addEventListener('click', function () {
      filmBox.classList.add('playing'); fx.hidden = false;
      fl.loop = false; fl.muted = false; fl.controls = true;
      fl.src = filmBox.getAttribute(narrow ? 'data-film-v' : 'data-film-h');
      var p = fl.play(); if (p && p.catch) p.catch(function () {});
    });
    fx.addEventListener('click', stopFilm);
    fl.addEventListener('ended', function () { if (filmBox.classList.contains('playing')) stopFilm(); });
  }

  /* ---------- video ---------- */
  $$('[data-video]').forEach(function (box) {
    var b = $('.play', box); if (!b) return;
    b.addEventListener('click', function () {
      var v = d.createElement('video');
      v.src = box.getAttribute('data-video'); v.controls = true; v.autoplay = true; v.playsInline = true; v.setAttribute('playsinline', '');
      var img = $('img', box); if (img) v.poster = img.currentSrc || img.src;
      box.innerHTML = ''; box.appendChild(v); box.classList.add('playing');
      var p = v.play(); if (p && p.catch) p.catch(function () {});
    });
  });

  /* ---------- lightbox ---------- */
  var lb = $('#lb'), lbImg = lb && $('img', lb), lbList = [], lbI = 0;
  function lbShow(i) { lbI = (i + lbList.length) % lbList.length; lbImg.src = lbList[lbI]; $('.c', lb).textContent = (lbI + 1) + ' / ' + lbList.length; }
  function lbOpen(group, el) {
    var els = $$('[data-lb="' + group + '"]');
    lbList = els.map(function (x) { var i = $('img', x); return i ? (i.getAttribute('data-full') || i.currentSrc || i.src) : ''; });
    lb.classList.add('open'); body.classList.add('lock'); lbShow(els.indexOf(el));
  }
  function lbClose() { lb.classList.remove('open'); body.classList.remove('lock'); }
  d.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-lb]');
    if (el && lb) { e.preventDefault(); lbOpen(el.getAttribute('data-lb'), el); }
  });
  if (lb) {
    $('.x', lb).addEventListener('click', lbClose);
    $('.p', lb).addEventListener('click', function () { lbShow(lbI - 1); });
    $('.n', lb).addEventListener('click', function () { lbShow(lbI + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) lbClose(); });
    var tx = 0; lb.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) { var dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 50) lbShow(lbI + (dx < 0 ? 1 : -1)); });
  }

  /* ---------- modals ---------- */
  function openModal(id) { var m = $(id); if (!m) return; m.classList.add('open'); body.classList.add('lock'); var f = $('input:not([type=hidden]):not(.hp),button', m); if (f) setTimeout(function () { f.focus(); }, 50); }
  function closeModals() { $$('.modal.open').forEach(function (m) { m.classList.remove('open'); }); body.classList.remove('lock'); }
  $$('.modal').forEach(function (m) { m.addEventListener('click', function (e) { if (e.target === m || (e.target.closest && e.target.closest('[data-close]'))) closeModals(); }); });
  d.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeModals(); if (lb) lbClose(); if (mnav && mnav.classList.contains('open')) setNav(false); fab && fab.classList.remove('open'); }
    if (lb && lb.classList.contains('open')) { if (e.key === 'ArrowRight') lbShow(lbI + 1); if (e.key === 'ArrowLeft') lbShow(lbI - 1); }
  });
  var onContact = !!$('#sent');
  d.addEventListener('click', function (e) {
    var q = e.target.closest && e.target.closest('[data-quote]');
    if (q) {
      if (onContact && !q.hasAttribute('data-product')) { e.preventDefault(); var f = $('form[name=contact]'); if (f) { f.scrollIntoView({ behavior: 'smooth', block: 'center' }); setTimeout(function () { var i = $('input[name=name]', f); if (i) i.focus({ preventScroll: true }); }, 500); } setNav(false); return; }
      e.preventDefault(); if (mnav && mnav.classList.contains('open')) setNav(false);
      var m = $('#m-quote'), prod = q.getAttribute('data-product') || '', line = $('.js-mq-product', m), fld = $('.js-product', m), subj = $('input[name=_subject]', m);
      fld.value = prod; line.hidden = !prod; line.textContent = prod;
      subj.value = prod ? ('EASEN 询价 / Quote request: ' + prod) : 'EASEN 网站新询盘 / New Website Enquiry';
      if (fab) fab.classList.remove('open');
      openModal('#m-quote'); return;
    }
    var w = e.target.closest && e.target.closest('[data-wechat]');
    if (w) { e.preventDefault(); if (fab) fab.classList.remove('open'); openModal('#m-wechat'); return; }
    var cp = e.target.closest && e.target.closest('[data-copy]');
    if (cp) {
      var txt = cp.getAttribute('data-copy'), done = function () { var o = cp.textContent; cp.textContent = cp.getAttribute('data-copied'); setTimeout(function () { cp.textContent = o; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, done); else done();
    }
  });

  /* ---------- fab ---------- */
  var fab = $('#fab');
  if (fab) {
    var fb = $('.fab-btn', fab);
    var hi = $('#sena-hi');
    var hiOff = function () { if (hi) hi.hidden = true; try { sessionStorage.setItem('easen-sena-hi', '1'); } catch (e) {} };
    var setFab = function (o) { fab.classList.toggle('open', o); fb.setAttribute('aria-expanded', o ? 'true' : 'false'); if (o) hiOff(); };
    fb.addEventListener('click', function () { setFab(!fab.classList.contains('open')); });
    d.addEventListener('click', function (e) { if (!fab.contains(e.target)) fab.classList.remove('open'); });
    /* Sena greeting bubble: once per session, after a short delay */
    if (hi) {
      $('.sena-hi-x', hi).addEventListener('click', function (e) { e.stopPropagation(); hiOff(); });
      $('.sena-hi-msg', hi).addEventListener('click', function (e) { e.stopPropagation(); setFab(true); });
      var seen = false;
      try { seen = !!sessionStorage.getItem('easen-sena-hi'); } catch (e) {}
      if (!seen) setTimeout(function () { if (!fab.classList.contains('open')) { hi.hidden = false; requestAnimationFrame(function () { hi.classList.add('in'); }); setTimeout(function () { if (!hi.hidden) { hi.classList.remove('in'); setTimeout(hiOff, 500); } }, 15000); } }, 3500);
    }
  }

  /* ---------- Sena video: living avatar + talking intro ---------- */
  var swallow = function (p) { if (p && p.catch) p.catch(function () {}); };
  var sav = $('.sena-av');
  if (sav && !RM) window.addEventListener('load', function () {
    setTimeout(function () {
      sav.addEventListener('playing', function () { sav.classList.add('on'); }, { once: true });
      sav.src = sav.getAttribute('data-src'); swallow(sav.play());
    }, 1200);
  });
  var st = $('.sena-talk');
  if (st) {
    var sv = $('video', st), sp = $('.sena-play', st), sx = $('.sena-stop', st), idle = sv.getAttribute('data-idle'), trk = null;
    var toIdle = function () {
      if (trk) { trk.remove(); trk = null; }
      st.classList.remove('talking'); st.parentNode.classList.remove('talking'); sx.hidden = true; sp.hidden = false;
      sv.muted = true; sv.loop = true;
      if (RM) { sv.pause(); sv.removeAttribute('src'); sv.load(); return; }
      sv.src = idle; swallow(sv.play());
    };
    if (!RM && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (st.classList.contains('talking')) return;
          if (e.isIntersecting) { if (!sv.getAttribute('src')) sv.src = idle; swallow(sv.play()); } else sv.pause();
        });
      }, { rootMargin: '200px' }).observe(st);
    }
    sp.addEventListener('click', function () {
      st.classList.add('talking'); st.parentNode.classList.add('talking'); sp.hidden = true; sx.hidden = false;
      sv.loop = false; sv.muted = false; sv.src = st.getAttribute('data-talk');
      trk = d.createElement('track'); trk.kind = 'captions'; trk.srclang = trk.label = st.getAttribute('data-srclang'); trk.src = st.getAttribute('data-vtt'); trk.default = true;
      sv.appendChild(trk);
      sv.addEventListener('loadedmetadata', function () { if (sv.textTracks[0]) sv.textTracks[0].mode = 'showing'; }, { once: true });
      swallow(sv.play());
    });
    sx.addEventListener('click', toIdle);
    sv.addEventListener('ended', function () { if (st.classList.contains('talking')) toIdle(); });
  }

  /* ---------- forms ---------- */
  if (/[?&]sent=1(&|$)/.test(location.search)) {
    var ok = $('#sent'); if (ok) { ok.hidden = false; setTimeout(function () { ok.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 200); }
    if (history.replaceState) history.replaceState(null, '', location.pathname);
  }
  $$('.js-form').forEach(function (f) {
    f.addEventListener('submit', function () {
      var b = $('button[type=submit]', f); if (b) { b.disabled = true; b.textContent = b.getAttribute('data-sending') || '…'; }
    });
  });

  /* ---------- toast ---------- */
  var toastEl = $('#toast'), toastT;
  function toast(msg) { if (!toastEl) return; toastEl.textContent = msg; toastEl.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(function () { toastEl.classList.remove('show'); }, 1900); }

  /* ---------- AI preview cart ---------- */
  function cart() { try { return JSON.parse(store('easen-ai-cart') || '[]'); } catch (e) { return []; } }
  function saveCart(c) { store('easen-ai-cart', JSON.stringify(c)); syncCart(); }
  function inCart(id) { return cart().some(function (x) { return String(x.id) === String(id); }); }
  function toggleCart(id, name, img) {
    var c = cart(), i = -1;
    c.forEach(function (x, k) { if (String(x.id) === String(id)) i = k; });
    if (i > -1) { c.splice(i, 1); } else { c.push({ id: id, name: name, img: img }); toast('✓ ' + (T.added_ai || 'Added')); }
    saveCart(c);
  }
  function syncCart() {
    var c = cart(), f = $('#ai-fab'), n = $('#ai-n');
    if (f) { f.classList.toggle('show', c.length > 0); if (n) n.textContent = c.length; f.href = f.getAttribute('href').split('?')[0] + (c.length ? '?cart=' + encodeURIComponent(c.map(function (x) { return x.id; }).join(',')) : ''); }
    $$('[data-ai]').forEach(function (b) { b.classList.toggle('on', inCart(b.getAttribute('data-ai'))); });
    $$('[data-ai-detail]').forEach(function (b) { var id = b.getAttribute('data-ai-detail'); if (id) b.classList.toggle('brass', inCart(id)); });
  }
  d.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-ai],[data-ai-detail]');
    if (!b) return; e.preventDefault();
    var id = b.getAttribute('data-ai') || b.getAttribute('data-ai-detail'); if (!id) return;
    toggleCart(id, b.getAttribute('data-name'), b.getAttribute('data-img'));
  });
  syncCart();

  /* ---------- panorama ---------- */
  $$('[data-pano]').forEach(function (p) {
    var inner = $('.pano-in', p), x = 0, sx = 0, sx0 = 0, drag = false, w = 0, auto = true;
    function width() { var i = $('img', inner); w = i ? i.getBoundingClientRect().width : 0; }
    function set() { if (!w) width(); if (w) { x = ((x % w) + w) % w; inner.style.transform = 'translate3d(' + (-x) + 'px,0,0)'; } }
    function tick() { if (auto && !drag) { x += 0.35; set(); } requestAnimationFrame(tick); }
    $$('img', inner).forEach(function (i) { i.addEventListener('load', function () { width(); set(); }); });
    window.addEventListener('resize', width);
    function down(cx) { drag = true; auto = false; sx = cx; sx0 = x; p.classList.add('drag', 'used'); }
    function move(cx) { if (!drag) return; x = sx0 - (cx - sx); set(); }
    function up() { drag = false; p.classList.remove('drag'); }
    p.addEventListener('mousedown', function (e) { e.preventDefault(); down(e.clientX); });
    window.addEventListener('mousemove', function (e) { move(e.clientX); });
    window.addEventListener('mouseup', up);
    p.addEventListener('touchstart', function (e) { down(e.touches[0].clientX); }, { passive: true });
    p.addEventListener('touchmove', function (e) { move(e.touches[0].clientX); }, { passive: true });
    p.addEventListener('touchend', up);
    requestAnimationFrame(tick);
  });

  /* ---------- data helpers ---------- */
  var BASE = '/' + L + '/';
  function getJSON(u) { return fetch(u, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw 0; return r.json(); }); }
  function pName(p, tr) { if (L === 'zh') return p.title_zh || p.title_en || ''; if (L === 'en') return p.title_en || p.title_zh || ''; var x = tr && tr[p.id]; return (x && x[L]) || p.title_en || p.title_zh || ''; }
  function pCode(p) { return p.sku || ('EA-' + String(p.id).slice(-5)); }
  function pUrl(p) { return (C.builtP || []).indexOf(String(p.id)) > -1 ? BASE + 'products/item/' + p.id + '.html' : BASE + 'product.html?id=' + p.id; }
  function cUrl(c) { return (C.builtC || []).indexOf(String(c.id)) > -1 ? BASE + 'cases/' + c.id + '.html' : BASE + 'case.html?id=' + c.id; }
  function cardHTML(p, tr) {
    var nm = esc(pName(p, tr)), ty = (T.type && T.type[p.type]) || '', alt = p.images && p.images[1];
    return '<article class="pcard rv in"><a href="' + pUrl(p) + '" class="ph ar-34" aria-label="' + nm + '"><img src="' + esc(p.main_image) + '" alt="' + nm + '" loading="lazy" decoding="async">' +
      (alt ? '<img class="alt" src="' + esc(alt) + '" alt="" loading="lazy" decoding="async">' : '') + '</a><div class="meta"><div><h3><a href="' + pUrl(p) + '">' + nm + '</a></h3><span class="kind">' + esc(ty) + ' · ' + esc(pCode(p)) + '</span></div>' +
      '<button class="add" type="button" data-ai="' + esc(p.id) + '" data-name="' + nm + '" data-img="' + esc(p.main_image) + '" aria-label="' + esc(T.add_ai) + '"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg></button></div></article>';
  }
  function visibleCases(list) {
    var cnt = {}; list.forEach(function (c) { cnt[c.cover_image] = (cnt[c.cover_image] || 0) + 1; });
    return list.filter(function (c) { return c.cover_image && cnt[c.cover_image] === 1 && c.status !== 'hidden' && c.status !== 'offline' && (c.images || []).length; });
  }

  /* ---------- product listing ---------- */
  var grid = $('#pgrid');
  if (grid) {
    var BATCH = 24, shown = BATCH, fCat = grid.getAttribute('data-cat') || '', fType = '', fQ = '';
    var params = new URLSearchParams(location.search);
    if (!fCat && params.get('cat')) fCat = params.get('cat');
    if (params.get('type')) fType = params.get('type');
    var lockCat = !!grid.getAttribute('data-cat');
    var moreBtn = $('[data-more]'), countEl = $('[data-count]'), emptyEl = $('[data-empty]', grid), search = $('[data-search]');
    function items() { return $$('.pwrap', grid); }
    function apply(reset) {
      if (reset) shown = BATCH;
      var q = fQ.trim().toLowerCase(), n = 0, vis = 0;
      items().forEach(function (it) {
        var ok = (!fCat || it.getAttribute('data-cat') === fCat) && (!fType || it.getAttribute('data-type') === fType) && (!q || (it.getAttribute('data-q') || '').indexOf(q) > -1) && !it.hasAttribute('data-off');
        if (ok) n++;
        var show = ok && n <= shown; it.hidden = !show; if (show) vis++;
      });
      if (countEl) countEl.textContent = (countEl.getAttribute('data-tpl') || '{n}').replace('{n}', n);
      if (moreBtn) moreBtn.parentNode.hidden = vis >= n;
      if (emptyEl) emptyEl.hidden = n > 0;
      reveal(grid);
    }
    function syncChips() {
      $$('[data-filter]').forEach(function (g) {
        var v = g.getAttribute('data-filter') === 'cat' ? fCat : fType;
        $$('.chip', g).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-v') === v ? 'true' : 'false'); });
      });
      if (history.replaceState) { var p = new URLSearchParams(); if (fCat && !lockCat) p.set('cat', fCat); if (fType) p.set('type', fType); var s = p.toString(); history.replaceState(null, '', location.pathname + (s ? '?' + s : '')); }
    }
    $$('[data-filter]').forEach(function (g) {
      g.addEventListener('click', function (e) {
        var b = e.target.closest('.chip'); if (!b) return;
        if (g.getAttribute('data-filter') === 'cat') fCat = b.getAttribute('data-v'); else fType = b.getAttribute('data-v');
        syncChips(); apply(true);
      });
    });
    if (search) { var st; search.addEventListener('input', function () { clearTimeout(st); st = setTimeout(function () { fQ = search.value; apply(true); }, 120); }); }
    if (moreBtn) moreBtn.addEventListener('click', function () { shown += BATCH; apply(false); });
    syncChips(); apply(true);
    // live data: hide removed pieces, add new ones published from the admin
    Promise.all([getJSON('/data/products.json'), getJSON('/data/products-i18n.json').catch(function () { return {}; })]).then(function (r) {
      var list = r[0] || [], tr = r[1] || {}, live = {};
      list.forEach(function (p) { if (!p.status || p.status === 'online') live[String(p.id)] = p; });
      items().forEach(function (it) { if (!live[it.getAttribute('data-id')]) it.setAttribute('data-off', ''); });
      var have = {}; items().forEach(function (it) { have[it.getAttribute('data-id')] = 1; });
      var add = list.filter(function (p) { return live[String(p.id)] && !have[String(p.id)] && (!lockCat || p.category === fCat); });
      if (add.length) {
        var frag = d.createElement('div');
        add.reverse().forEach(function (p) {
          frag.innerHTML = '<div class="pwrap" data-id="' + esc(p.id) + '" data-cat="' + esc(p.category) + '" data-type="' + esc(p.type || '') + '" data-q="' + esc([p.title_zh, p.title_en, pName(p, tr), pCode(p)].join(' ').toLowerCase()) + '">' + cardHTML(p, tr) + '</div>';
          grid.insertBefore(frag.firstChild, grid.firstChild);
        });
      }
      syncCart(); apply(false);
    }).catch(function () {});
  }

  /* ---------- case listing (live) ---------- */
  var cgrid = $('#cgrid');
  if (cgrid) {
    getJSON('/data/cases.json').then(function (list) {
      var vis = visibleCases(list || []), ids = {}, cat = cgrid.getAttribute('data-cat');
      vis.forEach(function (c) { ids[String(c.id)] = c; });
      $$('.cwrap', cgrid).forEach(function (w) { if (!ids[w.getAttribute('data-id')]) w.hidden = true; });
      var have = {}; $$('.cwrap', cgrid).forEach(function (w) { have[w.getAttribute('data-id')] = 1; });
      vis.filter(function (c) { return !have[String(c.id)] && (!cat || c.category === cat); }).forEach(function (c) {
        var nm = esc(L === 'zh' ? (c.title_zh || c.title_en) : (c.title_en || c.title_zh)), loc = esc(c.location || ''), ds = esc(String((L === 'zh' ? c.desc_zh : c.desc_en) || '').slice(0, 160));
        var el = d.createElement('div'); el.className = 'cwrap';
        el.innerHTML = '<article class="ccard rv in"><a href="' + cUrl(c) + '"><div class="ph zoom"><img src="' + esc(c.cover_image) + '" alt="' + nm + '" loading="lazy"></div><span class="loc">' + loc + '</span><h3>' + nm + '</h3><p>' + ds + '</p></a></article>';
        cgrid.appendChild(el);
      });
    }).catch(function () {});
  }

  /* ---------- dynamic detail pages (?id=) for items added after the last build ---------- */
  var pd = $('#pd[data-dynamic]');
  if (pd) {
    var pid = new URLSearchParams(location.search).get('id');
    if ((C.builtP || []).indexOf(String(pid)) > -1) { location.replace(BASE + 'products/item/' + pid + '.html'); return; }
    Promise.all([getJSON('/data/products.json'), getJSON('/data/products-i18n.json').catch(function () { return {}; })]).then(function (r) {
      var p = (r[0] || []).filter(function (x) { return String(x.id) === String(pid); })[0];
      if (!p) { location.replace(BASE + 'products.html'); return; }
      var nm = pName(p, r[1]), code = pCode(p);
      d.title = nm + ' | EASEN';
      $$('[data-f=name]').forEach(function (e) { e.textContent = nm; });
      $('[data-f=eyebrow]').textContent = (T.catLong && T.catLong[p.category]) || '';
      $('[data-f=sub]').textContent = ((T.type && T.type[p.type]) || '') + ' · ' + code;
      $('[data-f=gallery]').innerHTML = (p.images || []).map(function (im) { return '<div class="ph" data-lb="p"><img src="' + esc(im) + '" alt="' + esc(nm) + '"></div>'; }).join('');
      var S = T.spec || {};
      $('[data-f=specs]').innerHTML = [[S.code, code], [S.dims, p.dimensions || S.dims_v], [S.material, p.material || S.mat_v], [S.moq, S.moq_v], [S.lead, S.lead_v]].map(function (r) { return '<div><dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd></div>'; }).join('');
      $$('[data-quote][data-product]', pd).forEach(function (b) { b.setAttribute('data-product', nm + ' (' + code + ')'); });
      var ai = $('[data-ai-detail]', pd); if (ai) { ai.setAttribute('data-ai-detail', p.id); ai.setAttribute('data-name', nm); ai.setAttribute('data-img', p.main_image); }
      syncCart();
    }).catch(function () {});
  }
  var cd = $('[data-f=desc]');
  if (cd && !cd.innerHTML.trim()) {
    var cid = new URLSearchParams(location.search).get('id');
    if ((C.builtC || []).indexOf(String(cid)) > -1) { location.replace(BASE + 'cases/' + cid + '.html'); return; }
    getJSON('/data/cases.json').then(function (list) {
      var c = (list || []).filter(function (x) { return String(x.id) === String(cid); })[0];
      if (!c) { location.replace(BASE + 'cases.html'); return; }
      var nm = L === 'zh' ? (c.title_zh || c.title_en) : (c.title_en || c.title_zh), ds = (L === 'zh' ? c.desc_zh : c.desc_en) || c.desc_en || '';
      d.title = nm + ' | EASEN';
      $$('[data-f=name]').forEach(function (e) { e.textContent = nm; });
      var cov = $('[data-f=cover]'); if (cov) cov.src = c.cover_image;
      $('[data-f=eyebrow]').textContent = c.location || '';
      $('[data-f=loc]').textContent = c.location || '';
      $('[data-f=cat]').textContent = (T.catLong && T.catLong[c.category]) || c.category;
      $('[data-f=count]').textContent = (c.images || []).length;
      cd.innerHTML = ds.split(/\n\s*\n/).map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('');
      $('[data-f=gallery]').innerHTML = (c.images || []).map(function (im) { return '<div class="ph" data-lb="case"><img src="' + esc(im) + '" alt="' + esc(nm) + '" loading="lazy"></div>'; }).join('');
    }).catch(function () {});
  }
})();
