/*
 * EASEN 官网 → 询盘 CRM 接入（与现有 FormSubmit 并存，邮件照常发）
 *
 * 用法：把本文件部署到站点根目录，并在带表单的页面 </body> 前加：
 *   <script src="/crm-capture.js" defer></script>
 *
 * 部署 easen-crm 后，只需把下面的 CRM_INGEST 改成你的真实地址即可生效；
 * 未配置（仍含 REPLACE-ME）时本脚本不做任何事，安全占位、不影响线上表单。
 */
(function () {
  "use strict";

  // ★★★ 部署 easen-crm 后改这里（仅此一处） ★★★
  var CRM_INGEST = "https://easen-crm.galelikestofuck262626.workers.dev/api/ingest";

  if (CRM_INGEST.indexOf("REPLACE-ME") !== -1) return; // 未配置 → 不动作

  var LANGS = { ar: 1, de: 1, en: 1, es: 1, fr: 1, zh: 1 };

  function detectLang() {
    var seg = (location.pathname.split("/").filter(Boolean)[0] || "").toLowerCase();
    return LANGS[seg] ? seg : "zh";
  }

  function send(form) {
    try {
      var fd = new FormData(form);
      var body = {};
      fd.forEach(function (v, k) {
        if (typeof v === "string") body[k] = v;
      });
      // 需求类型(select) 映射成意向产品，方便 CRM 直接展示
      if (!body.product && body.type) body.product = body.type;
      body.source = "website";
      body.page = location.pathname;
      body.language = detectLang();

      // fire-and-forget；keepalive 保证整页跳转(FormSubmit 重定向)时请求仍发得出去
      fetch(CRM_INGEST, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        keepalive: true,
        mode: "cors",
        credentials: "omit",
      }).catch(function () {});
    } catch (e) {
      /* 任何异常都不得影响表单正常提交 */
    }
  }

  function hook(form) {
    if (form.__crmHooked) return;
    form.__crmHooked = true;
    // 捕获阶段监听，先于默认提交触发；不调用 preventDefault，FormSubmit 照常工作
    form.addEventListener("submit", function () { send(form); }, true);
  }

  function init() {
    var forms = document.querySelectorAll('form[action*="formsubmit.co"]');
    for (var i = 0; i < forms.length; i++) hook(forms[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
