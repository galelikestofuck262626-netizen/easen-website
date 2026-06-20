(function(){
var REPO="galelikestofuck262626-netizen/easen-website";var BRANCH="main";var PI18N={};
var L6=["zh","en","fr","es","de","ar"];
function spans(d){var o="";L6.forEach(function(L){o+='<span data-lang="'+L+'"'+(L==="zh"?"":' style="display:none"')+'>'+d[L]+'</span>';});return o;}
function curLang(){return (location.pathname.match(/^\/(zh|en|fr|es|de|ar)(\/|$)/)||[])[1]||localStorage.getItem("easen-lang")||"zh";}
function applyLang(){if(window.applyLangGlobal){window.applyLangGlobal(curLang());}}
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function getCategory(){var p=window.location.pathname;if(p.indexOf("/restaurant")>-1)return"restaurant";if(p.indexOf("/hotel")>-1)return"hotel";if(p.indexOf("/cafe")>-1)return"cafe";if(p.indexOf("/outdoor")>-1)return"outdoor";return null;}
// —— AI 看效果 文案(6语言)——
var T={
  add:{zh:"加入 AI 看效果",en:"Add to AI Preview",fr:"Ajouter à l'aperçu IA",es:"Añadir a vista IA",de:"Zur KI-Vorschau",ar:"أضف إلى المعاينة"},
  added:{zh:"已加入",en:"Added",fr:"Ajouté",es:"Añadido",de:"Hinzugefügt",ar:"أُضيف"},
  like:{zh:"喜欢这款？加入 AI 看效果",en:"Like this? Add to AI Preview",fr:"Vous aimez ? Ajouter à l'aperçu IA",es:"¿Le gusta? Añadir a vista IA",de:"Gefällt Ihnen? Zur KI-Vorschau",ar:"يعجبك؟ أضف إلى المعاينة"},
  fab:{zh:"AI 看效果",en:"AI Preview",fr:"Aperçu IA",es:"Vista IA",de:"KI-Vorschau",ar:"معاينة AI"},
  toast:{zh:"已加入 AI 看效果",en:"Added to AI Preview",fr:"Ajouté à l'aperçu IA",es:"Añadido a vista IA",de:"Zur KI-Vorschau hinzugefügt",ar:"أُضيف إلى المعاينة"},
  go:{zh:"生成效果图 →",en:"Generate →",fr:"Générer →",es:"Generar →",de:"Erzeugen →",ar:"إنشاء →"}
};
function tt(k){return T[k][curLang()]||T[k].en;}
var ADD_HTML=spans(T.add),GO_HTML=spans(T.go);
// —— 购物车 ——
function getCart(){try{return JSON.parse(localStorage.getItem("easen-ai-cart")||"[]");}catch(e){return [];}}
function saveCart(c){try{localStorage.setItem("easen-ai-cart",JSON.stringify(c));}catch(e){}}
function inCart(id){return getCart().some(function(x){return String(x.id)===String(id);});}
function addToCart(p){var c=getCart();if(!c.some(function(x){return String(x.id)===String(p.id);})){c.push({id:p.id,name:p.title_zh||p.title_en||"",img:p.main_image});saveCart(c);}updateFab();markCards();toast();}
function toast(){var t=document.getElementById("ai-toast");if(!t){t=document.createElement("div");t.id="ai-toast";t.style.cssText="position:fixed;left:50%;bottom:96px;transform:translateX(-50%) translateY(10px);background:#1a365d;color:#fff;padding:11px 22px;border-radius:9999px;font-size:14px;font-weight:600;box-shadow:0 10px 30px rgba(0,0,0,.2);z-index:10000;opacity:0;transition:all .3s ease;pointer-events:none;white-space:nowrap";document.body.appendChild(t);}t.textContent="✓ "+tt("toast");requestAnimationFrame(function(){t.style.opacity="1";t.style.transform="translateX(-50%) translateY(0)";});clearTimeout(t._h);t._h=setTimeout(function(){t.style.opacity="0";t.style.transform="translateX(-50%) translateY(10px)";},1800);}
function updateFab(){
  var c=getCart(),fab=document.getElementById("ai-fab");
  if(c.length===0){if(fab)fab.style.display="none";return;}
  if(!fab){
    fab=document.createElement("a");fab.id="ai-fab";
    fab.style.cssText="position:fixed;left:24px;bottom:32px;z-index:9997;display:inline-flex;align-items:center;gap:10px;padding:13px 22px;background:#c8a45c;color:#1a365d;font-weight:700;font-size:14px;border-radius:9999px;text-decoration:none;box-shadow:0 12px 30px rgba(200,164,92,.4);transition:transform .2s ease";
    fab.onmouseover=function(){fab.style.transform="translateY(-3px)";};fab.onmouseout=function(){fab.style.transform="";};
    document.body.appendChild(fab);
  }
  fab.style.display="inline-flex";
  fab.href="/visualizer.html?cart="+encodeURIComponent(c.map(function(x){return x.id;}).join(","));
  fab.innerHTML='<span style="font-size:17px">✦</span><span>'+tt("fab")+' ('+c.length+')</span><span style="opacity:.7">'+tt("go")+'</span>';
}
function markCards(){document.querySelectorAll(".cf-pcard[data-pid]").forEach(function(a){var on=inCart(a.getAttribute("data-pid"));var b=a.querySelector(".cf-add");if(b){b.classList.toggle("on",on);var lab=b.querySelector(".cf-add-lab");if(lab)lab.innerHTML=on?("✓ "+spans(T.added)):("✦ "+ADD_HTML);}});applyLang();}
function injectStyle(){if(document.getElementById('cf-pcard-style'))return;var s=document.createElement('style');s.id='cf-pcard-style';s.textContent='.cf-pcard{box-shadow:0 1px 4px rgba(16,24,40,.06);transition:box-shadow .35s ease, transform .35s ease;cursor:pointer}.cf-pcard:hover{box-shadow:0 18px 36px rgba(16,24,40,.14);transform:translateY(-6px)}.cf-imgwrap{position:relative}.cf-ov{position:absolute;inset:0;display:flex;align-items:flex-end;justify-content:center;padding:16px;background:linear-gradient(to top,rgba(15,27,48,.78),rgba(15,27,48,0) 55%);opacity:0;transition:opacity .3s ease}.cf-pcard:hover .cf-ov{opacity:1}.cf-ov span{color:#fff;font-size:13px;font-weight:600;text-align:center}.cf-add{display:inline-flex;align-items:center;gap:6px;margin-top:4px;padding:9px 16px;border-radius:9999px;background:#1a365d;color:#fff;font-weight:600;font-size:13px;border:none;cursor:pointer;transition:background .2s ease;width:100%;justify-content:center}.cf-add:hover{background:#c8a45c}.cf-add.on{background:rgba(200,164,92,.16);color:#1a365d}';document.head.appendChild(s);}
function nameSpans(p,tzh,ten){var tr=PI18N[p.id]||{};var o='<span data-lang="zh">'+tzh+'</span><span data-lang="en" data-en-original="'+ten+'">'+ten+'</span>';["fr","es","de","ar"].forEach(function(L){var v=esc(tr[L]||"")||ten;o+='<span data-lang="'+L+'" style="display:none">'+v+'</span>';});return o;}
function buildCard(p){
  var imgUrl="https://raw.githubusercontent.com/"+REPO+"/"+BRANCH+p.main_image;
  var a=document.createElement("div");a.className="group block bg-white rounded-2xl overflow-hidden cf-pcard";a.setAttribute("data-pid",p.id);
  var dims=[p.dimensions,p.material,p.fabric].filter(Boolean).join(" / ");
  var tzh=esc(p.title_zh||p.title_en||""),ten=esc(p.title_en||p.title_zh||"");
  a.innerHTML='<div class="cf-imgwrap aspect-[4/3] overflow-hidden"><img src="'+imgUrl+'" style="width:100%;height:100%;object-fit:cover" loading="lazy" alt="'+ten+'"><div class="cf-ov">'+spans(T.like)+'</div></div>'
    +'<div class="p-6"><h3 class="text-xl font-heading font-semibold text-primary mb-2">'+nameSpans(p,tzh,ten)+'</h3>'
    +(dims?'<p class="text-neutral-500 text-xs mb-3">'+esc(dims)+'</p>':'')
    +'<button class="cf-add" type="button"><span class="cf-add-lab">✦ '+ADD_HTML+'</span></button></div>';
  a.addEventListener("click",function(){addToCart(p);});
  return a;
}
var EMPTY_HTML='<div style="grid-column:1/-1;text-align:center;padding:64px 20px"><p style="font-size:18px;color:#6b7280;margin-bottom:18px">'+spans({zh:"本系列支持全系列定制，欢迎联系我们获取专属方案与最新目录",en:"This series is fully customizable — contact us for tailored solutions and the latest catalog",fr:"Cette gamme est entièrement personnalisable — contactez-nous pour des solutions sur mesure et le dernier catalogue",es:"Esta serie es totalmente personalizable: contáctenos para soluciones a medida y el catálogo más reciente",de:"Diese Serie ist vollständig anpassbar — kontaktieren Sie uns für maßgeschneiderte Lösungen",ar:"هذه السلسلة قابلة للتخصيص بالكامل — تواصل معنا للحصول على حلول مخصصة"})+'</p><a href="../../#contact" style="display:inline-flex;align-items:center;padding:12px 28px;background:#c8a45c;color:#fff;font-weight:600;border-radius:8px;text-decoration:none">'+spans({zh:"联系我们 →",en:"Contact Us →",fr:"Contactez-nous →",es:"Contáctenos →",de:"Kontakt →",ar:"اتصل بنا →"})+'</a></div>';
function renderProducts(products){
  var cat=getCategory();
  var filtered=products.filter(function(p){return p.category===cat&&(p.status==="online"||!p.status);}).slice().reverse();
  var grid=document.querySelector(".grid");if(!grid)return;
  injectStyle();updateFab();
  if(filtered.length===0){grid.innerHTML=EMPTY_HTML;applyLang();return;}
  var BATCH=24,shown=0;
  var wrap=document.createElement("div");wrap.style.cssText="text-align:center;margin-top:48px";
  var btn=document.createElement("button");btn.style.cssText="display:inline-flex;align-items:center;padding:14px 38px;background:#1a365d;color:#fff;font-weight:600;border:none;border-radius:9999px;cursor:pointer;font-size:15px;transition:background .25s ease";btn.innerHTML=spans({zh:"加载更多",en:"Load More",fr:"Voir plus",es:"Ver más",de:"Mehr laden",ar:"تحميل المزيد"});
  btn.onmouseenter=function(){btn.style.background="#c8a45c";};btn.onmouseleave=function(){btn.style.background="#1a365d";};
  wrap.appendChild(btn);grid.insertAdjacentElement("afterend",wrap);
  function renderBatch(){
    var end=Math.min(shown+BATCH,filtered.length);var frag=document.createDocumentFragment();
    for(var i=shown;i<end;i++){frag.appendChild(buildCard(filtered[i]));}
    grid.appendChild(frag);shown=end;
    wrap.style.display=(shown>=filtered.length)?"none":"block";
    markCards();applyLang();
  }
  renderBatch();btn.onclick=function(e){e.stopPropagation();renderBatch();};
}
function loadProducts(){updateFab();var cat=getCategory();if(!cat){return;}fetch("https://raw.githubusercontent.com/"+REPO+"/"+BRANCH+"/data/products-i18n.json?t="+Date.now()).then(function(r){return r.json();}).then(function(j){PI18N=j||{};}).catch(function(){}).then(function(){fetch("https://raw.githubusercontent.com/"+REPO+"/"+BRANCH+"/data/products.json?t="+Date.now()).then(function(r){return r.json();}).then(function(products){renderProducts(products);}).catch(function(){});});}
if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",loadProducts);}else{loadProducts();}
})();