/**
 * EASEN 共享组件 - 导航栏、页脚、联系浮窗
 * 自动注入到所有页面
 */
(function(){

  // 当前页面路径检测
  var path = window.location.pathname;
  var isRoot = path === '/' || path.endsWith('index.html');
  var isAdmin = path.indexOf('/admin') > -1;
  if (isAdmin) return; // 后台不注入

  // 计算根路径前缀
  var depth = (path.match(/\//g)||[]).length - 1;
  var prefix = '';
  for (var i=0; i<depth; i++) prefix += '../';

  function isActive(page) {
    if (page === 'index' && (isRoot || path === '/')) return true;
    return path.indexOf(page) > -1;
  }

  // 注入导航栏
  function injectNav() {
    var existing = document.querySelector('header');
    if (!existing) return;

    var nav = [
      { key:'index',    zh:'首页',    en:'Home',        href: prefix + 'index.html' },
      { key:'products', zh:'产品',    en:'Products',    href: prefix + 'products.html' },
      { key:'cases',    zh:'案例',    en:'Cases',       href: prefix + 'cases.html' },
      { key:'about',    zh:'关于我们', en:'About Us',    href: prefix + 'about.html' },
      { key:'contact',  zh:'联系我们', en:'Contact Us',  href: prefix + 'contact.html' },
    ];

    var navLinks = nav.map(function(n){
      var active = isActive(n.key) ? 'style="color:#c8a45c;font-weight:600"' : '';
      return '<a href="'+n.href+'" class="text-sm font-medium text-neutral-700 hover:text-accent transition-colors" '+active+'>'
        +'<span data-lang="zh">'+n.zh+'</span>'
        +'<span data-lang="en" style="display:none">'+n.en+'</span>'
        +'<span data-lang="fr" style="display:none">'+getFr(n.key)+'</span>'
        +'<span data-lang="es" style="display:none">'+getEs(n.key)+'</span>'
        +'<span data-lang="de" style="display:none">'+getDe(n.key)+'</span>'
        +'<span data-lang="ar" style="display:none">'+getAr(n.key)+'</span>'
        +'</a>';
    }).join('');

    // 移动端菜单链接
    var mobileLinks = nav.map(function(n){
      return '<a href="'+n.href+'" style="display:block;padding:12px 0;font-size:15px;border-bottom:1px solid #f3f4f6;color:#374151;text-decoration:none">'
        +'<span data-lang="zh">'+n.zh+'</span>'
        +'<span data-lang="en" style="display:none">'+n.en+'</span>'
        +'</a>';
    }).join('');

    existing.innerHTML =
      '<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">'
      +'<div class="flex items-center justify-between h-28">'
      +'<a href="'+prefix+'index.html" class="flex items-center gap-4">'
      +'<img src="'+prefix+'images/logo.jpg" alt="EASEN Logo" class="h-28 w-auto"/>'
      +'<div class="flex items-center gap-3">'
      +'<span class="text-3xl font-heading font-bold text-primary">EASEN</span>'
      +'<span class="text-neutral-400 text-2xl">|</span>'
      +'<span class="text-lg font-medium text-neutral-600">'
      +'<span data-lang="zh">宜森商业空间家具</span>'
      +'<span data-lang="en" style="display:none">EASEN Commercial Furniture</span>'
      +'</span></div></a>'
      +'<nav class="hidden md:flex items-center gap-8">'+navLinks+'</nav>'
      +'<button id="nav-mobile-btn" class="md:hidden p-2">'
      +'<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
      +'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>'
      +'</svg></button>'
      +'</div></div>';

    // 移动端菜单
    var mobileMenu = document.createElement('div');
    mobileMenu.id = 'mobile-nav-menu';
    mobileMenu.style.cssText = 'display:none;position:fixed;top:112px;left:0;right:0;background:#fff;z-index:49;box-shadow:0 4px 12px rgba(0,0,0,0.1);padding:16px 24px;';
    mobileMenu.innerHTML = mobileLinks;
    document.body.appendChild(mobileMenu);

    document.getElementById('nav-mobile-btn').addEventListener('click', function(){
      var m = document.getElementById('mobile-nav-menu');
      m.style.display = m.style.display === 'none' ? 'block' : 'none';
    });
  }

  // 注入页脚
  function injectFooter() {
    var existing = document.querySelector('footer');
    if (!existing) return;
    existing.innerHTML =
      '<div class="max-w-7xl mx-auto px-4">'
      +'<div class="grid grid-cols-1 md:grid-cols-3 gap-8">'
      +'<div>'
      +'<h3 class="font-semibold text-lg mb-4"><span data-lang="zh">宜森商业空间家具</span><span data-lang="en" style="display:none">EASEN Commercial Furniture</span></h3>'
      +'<p class="text-neutral-400 text-sm"><span data-lang="zh">为全球客户提供高品质定制家具。</span><span data-lang="en" style="display:none">Providing high-quality custom furniture for global clients.</span></p>'
      +'</div>'
      +'<div>'
      +'<h3 class="font-semibold text-lg mb-4"><span data-lang="zh">快速链接</span><span data-lang="en" style="display:none">Quick Links</span></h3>'
      +'<div class="space-y-2 text-sm">'
      +'<a href="'+prefix+'index.html" class="block text-neutral-400 hover:text-accent"><span data-lang="zh">首页</span><span data-lang="en" style="display:none">Home</span></a>'
      +'<a href="'+prefix+'products.html" class="block text-neutral-400 hover:text-accent"><span data-lang="zh">产品</span><span data-lang="en" style="display:none">Products</span></a>'
      +'<a href="'+prefix+'cases.html" class="block text-neutral-400 hover:text-accent"><span data-lang="zh">案例</span><span data-lang="en" style="display:none">Cases</span></a>'
      +'<a href="'+prefix+'about.html" class="block text-neutral-400 hover:text-accent"><span data-lang="zh">关于我们</span><span data-lang="en" style="display:none">About Us</span></a>'
      +'<a href="'+prefix+'contact.html" class="block text-neutral-400 hover:text-accent"><span data-lang="zh">联系我们</span><span data-lang="en" style="display:none">Contact Us</span></a>'
      +'</div></div>'
      +'<div>'
      +'<h3 class="font-semibold text-lg mb-4"><span data-lang="zh">联系信息</span><span data-lang="en" style="display:none">Contact Info</span></h3>'
      +'<div class="space-y-2 text-sm text-neutral-400">'
      +'<p><span data-lang="zh">广东省佛山市顺德区乐从镇</span><span data-lang="en" style="display:none">Lecong, Shunde, Foshan, China</span></p>'
      +'<p>chinaeasen@outlook.com</p>'
      +'<p>+86 15159581871</p>'
      +'</div></div></div>'
      +'<div class="border-t border-neutral-700 mt-8 pt-8 text-center text-neutral-400 text-sm">'
      +'© 2026 <span data-lang="zh">宜森商业空间家具</span><span data-lang="en" style="display:none">EASEN Commercial Furniture</span>. '
      +'<span data-lang="zh">版权所有</span><span data-lang="en" style="display:none">All Rights Reserved</span>.'
      +'</div></div>';
  }

  // 注入联系浮窗
  function injectContactFloat() {
    if (document.getElementById('contact-float')) return;
    var el = document.createElement('div');
    el.id = 'contact-float';
    el.style.cssText = 'position:fixed;bottom:32px;right:32px;z-index:9998;';
    el.innerHTML =
      '<div id="cf-menu" style="display:none;position:absolute;bottom:68px;right:0;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.15);padding:12px;min-width:200px;">'
      +'<p style="font-size:12px;color:#999;padding:4px 8px 8px;border-bottom:1px solid #f3f4f6;margin-bottom:8px;"><span data-lang="zh">选择联系方式</span><span data-lang="en" style="display:none">Contact Us Via</span></p>'
      +'<a href="https://wa.me/8615159581871" target="_blank" style="display:flex;align-items:center;gap:10px;padding:10px 8px;border-radius:10px;text-decoration:none;color:#1a1a1a;font-size:14px;" onmouseover="this.style.background=\'#f5f5f5\'" onmouseout="this.style.background=\'transparent\'">'
      +'<svg width="20" height="20" viewBox="0 0 24 24" fill="#25D366"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'
      +'WhatsApp</a>'
      +'<a href="mailto:chinaeasen@outlook.com" style="display:flex;align-items:center;gap:10px;padding:10px 8px;border-radius:10px;text-decoration:none;color:#1a1a1a;font-size:14px;" onmouseover="this.style.background=\'#f5f5f5\'" onmouseout="this.style.background=\'transparent\'">'
      +'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c8a45c" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>'
      +'Email</a>'
      +'<a href="'+prefix+'contact.html" style="display:flex;align-items:center;gap:10px;padding:10px 8px;border-radius:10px;text-decoration:none;color:#1a1a1a;font-size:14px;" onmouseover="this.style.background=\'#f5f5f5\'" onmouseout="this.style.background=\'transparent\'">'
      +'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c8a45c" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>'
      +'<span data-lang="zh">在线留言</span><span data-lang="en" style="display:none">Contact Form</span></a>'
      +'</div>'
      +'<button id="cf-btn" style="width:56px;height:56px;background:#c8a45c;color:#fff;border:none;border-radius:50%;box-shadow:0 4px 16px rgba(200,164,92,0.5);display:flex;align-items:center;justify-content:center;cursor:pointer;">'
      +'<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>'
      +'</button>';
    document.body.appendChild(el);
    document.getElementById('cf-btn').addEventListener('click', function(e){
      e.stopPropagation();
      var m = document.getElementById('cf-menu');
      m.style.display = m.style.display === 'none' ? 'block' : 'none';
    });
    document.addEventListener('click', function(){ document.getElementById('cf-menu').style.display='none'; });
  }

  // 多语言翻译辅助
  function getFr(k){ return {index:'Accueil',products:'Produits',cases:'Références',about:'À Propos',contact:'Contact'}[k]||k; }
  function getEs(k){ return {index:'Inicio',products:'Productos',cases:'Casos',about:'Sobre Nosotros',contact:'Contacto'}[k]||k; }
  function getDe(k){ return {index:'Startseite',products:'Produkte',cases:'Referenzen',about:'Über Uns',contact:'Kontakt'}[k]||k; }
  function getAr(k){ return {index:'الرئيسية',products:'المنتجات',cases:'المشاريع',about:'من نحن',contact:'اتصل بنا'}[k]||k; }

  // 手机端底部固定导航栏（所有设备注入，CSS控制显示）
  function injectMobileNav() {
    var nav = document.createElement('div');
    nav.id = 'mobile-bottom-nav';
    nav.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:9998;background:#fff;border-top:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-around;padding:8px 0 8px;box-shadow:0 -2px 10px rgba(0,0,0,0.08);';
    var items = [
      { key:'index',   zh:'首页',  en:'Home',     icon:'🏠', href: prefix+'index.html' },
      { key:'products',zh:'产品',  en:'Products', icon:'🛋️', href: prefix+'products.html' },
      { key:'cases',   zh:'案例',  en:'Cases',    icon:'📷', href: prefix+'cases.html' },
      { key:'about',   zh:'关于',  en:'About',    icon:'🏭', href: prefix+'about.html' },
      { key:'contact', zh:'联系',  en:'Contact',  icon:'📞', href: prefix+'contact.html' },
    ];
    nav.innerHTML = items.map(function(item){
      var active = isActive(item.key);
      return '<a href="'+item.href+'" style="display:flex;flex-direction:column;align-items:center;gap:2px;text-decoration:none;flex:1;padding:4px 0;'+(active?'color:#1a365d;':'color:#9ca3af;')+'">'
        +'<span style="font-size:20px;line-height:1">'+item.icon+'</span>'
        +'<span style="font-size:10px;font-weight:'+(active?'700':'500')+';">'
        +'<span data-lang="zh">'+item.zh+'</span>'
        +'<span data-lang="en" style="display:none">'+item.en+'</span>'
        +'</span></a>';
    }).join('');
    // CSS：只在手机端显示
    var style = document.createElement('style');
    style.textContent = '#mobile-bottom-nav{display:none}@media(max-width:768px){#mobile-bottom-nav{display:flex!important}body{padding-bottom:65px!important}}';
    document.head.appendChild(style);
    document.body.appendChild(nav);
  }

  // 执行注入
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){
      injectNav();
      injectFooter();
      injectContactFloat();
      injectMobileNav();
      initVideoControls();
    });
  } else {
    injectNav();
    injectFooter();
    injectContactFloat();
    injectMobileNav();
    initVideoControls();
  }

  // 视频播放控制（首页工厂视频）
  function initVideoControls() {
    var video = document.getElementById('factoryVideo');
    var overlay = document.getElementById('playOverlay');
    var wrapper = document.getElementById('videoWrapper');

    if (!video || !overlay || !wrapper) return;

    // 点击播放/暂停
    wrapper.addEventListener('click', function(e){
      if (video.paused) {
        video.play();
        overlay.style.opacity = '0';
        overlay.style.pointerEvents = 'none';
      } else {
        video.pause();
        overlay.style.opacity = '1';
        overlay.style.pointerEvents = 'auto';
      }
    });

    // 视频播放时隐藏遮罩
    video.addEventListener('play', function(){
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
    });

    // 视频暂停时显示遮罩
    video.addEventListener('pause', function(){
      overlay.style.opacity = '1';
      overlay.style.pointerEvents = 'auto';
    });

    // 视频结束时显示遮罩
    video.addEventListener('ended', function(){
      overlay.style.opacity = '1';
      overlay.style.pointerEvents = 'auto';
    });
  }

})();
