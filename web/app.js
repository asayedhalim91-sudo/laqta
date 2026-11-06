/* Laqta web app — reads /data/products.json (written by the collector) and renders every screen. */
(() => {
  'use strict';

  const STORE_MONO = { amazon: 'A', noon: 'N', shein: 'S', aliexpress: 'Ae', namshi: 'Nm', temu: 'T' };
  const ICONS = {
    tech: '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/><rect x="2" y="14" width="5" height="7" rx="2"/><rect x="17" y="14" width="5" height="7" rx="2"/>',
    fashion: '<path d="M12 8V7a2 2 0 1 0-2-2"/><path d="M12 8 2.6 15.4A1.5 1.5 0 0 0 3.5 18h17a1.5 1.5 0 0 0 .9-2.6z"/>',
    beauty: '<rect x="6" y="9" width="12" height="13" rx="3"/><path d="M9 9V6h6v3M10 6V3h4v3M9 14h6"/>',
    home: '<path d="M8 2h8l3 8H5z"/><path d="M12 10v9M8 22h8"/>',
    kids: '<rect x="3" y="12" width="8" height="8" rx="1.5"/><rect x="13" y="12" width="8" height="8" rx="1.5"/><rect x="8" y="3" width="8" height="8" rx="1.5"/>',
    other: '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
  };
  const I = {
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    wallet: '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    back: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    out: '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    arrow: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
  };
  const svg = (p, label) => `<svg viewBox="0 0 24 24" ${label ? `role="img" aria-label="${esc(label)}"` : 'aria-hidden="true"'}>${p}</svg>`;

  let DATA = null, STORES = {}, CATS = {};
  const main = document.getElementById('main');

  // ---------- helpers ----------
  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  const fmt = n => Number(n).toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: Number.isInteger(+n) ? 0 : 2 });
  const sar = n => `${fmt(n)} ر.س`;
  const discount = p => (p.old_price && p.old_price > p.price) ? 1 - p.price / p.old_price : 0;
  const storeName = id => STORES[id] || id;
  const storesLine = p => p.offers.map(o => storeName(o.store)).join(' · ');
  const EXTRA = {
    watch: '<rect x="6" y="6" width="12" height="12" rx="3"/><path d="M9 6l1-4h4l1 4M9 18l1 4h4l1-4M12 10v2l1.5 1.5"/>',
    charger: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    bag: '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    pot: '<path d="M4 10h16v7a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path d="M2 10h20M9 6V4M15 6V4"/>',
  };
  const WORDS = [[/ساعة|watch/i, 'watch'], [/شاحن|charger/i, 'charger'], [/حقيبة|شنطة|backpack|bag/i, 'bag'], [/قلاية|fryer|طنجرة/i, 'pot']];
  const iconFor = p => { const w = WORDS.find(([re]) => re.test(p.title)); return w ? EXTRA[w[1]] : (ICONS[p.category] || ICONS.other); };
  const thumb = p => p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : svg(iconFor(p));
  const byPid = h => DATA.products.find(p => pid(p.id) === h);
  const S = { q: '', sel: {} };                       // state that is not in the address
  const FRAMED = (() => { try { return window.self !== window.top; } catch { return true; } })();
  // The early-access form saves through Netlify Forms, so it only shows on a Netlify address.
  const FORMS = !FRAMED && /\.netlify\.app$/.test(location.hostname);
  const pid = id => 'p-' + String(id).replace(/^g_/, '').replace(/[^A-Za-z0-9-]/g, '-');
  const tHash = (cat, store) => '#trending' + (cat || store ? `--${cat || 'all'}` : '') + (store ? `--${store}` : '');
  function setTitle(t) { document.title = t ? `${t} — لقطة` : 'لقطة — كل المتاجر في مكان واحد'; }

  function card(p) {
    const cash = p.max_cashback > 0 ? `<span class="badge b-cash">كاش باك حتى ${sar(p.max_cashback)}</span>` : '';
    return `<a class="card" href="#${pid(p.id)}">
      <div class="thumb">${thumb(p)}${cash}<span class="badge b-rank">#${p.rank}</span>
        <span class="badge b-store">أرخص في ${esc(storeName(p.best_store))}</span></div>
      <span class="t">${esc(p.title)}</span>
      <div class="price"><span><b>${sar(p.price)}</b> ${p.old_price ? `<s>${fmt(p.old_price)}</s>` : ''}</span>
        <small>${p.offers.length > 1 ? `${p.offers.length} متاجر` : esc(storeName(p.best_store))}</small></div>
    </a>`;
  }
  function row(p, n) {
    return `<li><a href="#${pid(p.id)}"><span class="n">${n}</span>
      <span class="ic">${svg(iconFor(p))}</span>
      <span class="m"><span>${esc(p.title)}</span><span>${esc(storesLine(p))}</span></span>
      <span class="p">${sar(p.price)}</span></a></li>`;
  }
  const header = (right = '') => `<header class="top">
      <a class="logo" href="#home" aria-label="لقطة — الرئيسية"><span class="mark" aria-hidden="true"><i></i></span><b>لقطة</b></a>${right}</header>`;
  const walletPill = `<a class="pill" href="#wallet"><span class="dot">${svg(I.wallet)}</span><span>الكاش باك</span></a>`;
  const searchBox = (q = '') => `<form class="search" role="search" data-search>
      ${svg(I.search)}<input name="q" value="${esc(q)}" aria-label="ابحث في كل المتاجر" placeholder="ابحث عن أي منتج في 6 متاجر" autocomplete="off">
      <button type="submit">ابحث</button></form>`;
  const footer = () => `<footer class="foot">
      <span>لقطة تقارن الأسعار بين المتاجر. عند الشراء عبر روابطنا قد نحصل على عمولة من المتجر ونرجع جزءاً منها لك ككاش باك. السعر النهائي هو المعروض في المتجر.</span>
      <span>آخر تحديث: ${esc(new Date(DATA.generated_at).toLocaleString('ar-SA', { dateStyle: 'medium', timeStyle: 'short' }))}</span></footer>`;

  // ---------- screens ----------
  function home() {
    setTitle('');
    const P = DATA.products;
    const deals = [...P].sort((a, b) => discount(b) - discount(a));
    const maxOff = Math.round(discount(deals[0] || {}) * 100);
    return `${header(walletPill)}
      ${searchBox()}
      <div class="row-scroll" aria-label="المتاجر">${DATA.stores.map(s =>
        `<a class="store-dot" href="${tHash('', s.id)}"><b>${STORE_MONO[s.id] || s.name[0]}</b><span>${esc(s.name)}</span></a>`).join('')}</div>
      <section class="banner" aria-labelledby="bn">
        <span class="big" aria-hidden="true">${maxOff}%</span>
        <span class="tag"><i></i>عروض اليوم من كل المتاجر</span>
        <h2 id="bn">خصومات حتى ${maxOff}% في مكان واحد</h2>
        <p>رتبنا لك أقوى التخفيضات من أمازون ونون وشي إن وعلي إكسبريس ونمشي وتيمو.</p>
        <a class="btn btn-dark" href="#deals">شوف العروض ${svg(I.arrow)}</a>
      </section>
      <div class="head"><h2>مختارات لك</h2><a href="#trending">عرض الكل</a></div>
      <div class="cards scroll">${P.slice(0, 8).map(card).join('')}</div>
      <div class="head"><h2>الأكثر مبيعاً الآن</h2><a href="#trending">الترتيب الكامل</a></div>
      <ol class="list">${P.slice(0, 5).map((p, i) => row(p, i + 1)).join('')}</ol>
      <div class="head"><h2>تسوّق حسب الفئة</h2></div>
      <div class="cats">${DATA.categories.filter(c => P.some(p => p.category === c.id)).map(c =>
        `<a class="cat" href="${tHash(c.id, '')}">${svg(ICONS[c.id] || ICONS.other)}${esc(c.name)}</a>`).join('')}</div>
      ${footer()}`;
  }

  function trending() {
    setTitle('الأكثر مبيعاً');
    const [, cat0 = '', store = ''] = location.hash.slice(1).split('--');
    const cat = cat0 === 'all' ? '' : cat0;
    let list = DATA.products.filter(p => (!cat || p.category === cat) && (!store || p.offers.some(o => o.store === store)));
    const tabs = [{ id: '', name: 'الكل' }, ...DATA.categories.filter(c => DATA.products.some(p => p.category === c.id))];
    return `${header(walletPill)}
      <h1 style="font-size:clamp(30px,5vw,44px);font-weight:800">الأكثر <span class="gold">مبيعاً</span> في السعودية</h1>
      <div class="row-scroll" role="tablist" aria-label="الفئات">${tabs.map(t =>
        `<a class="chip" role="tab" aria-selected="${t.id === cat}" href="${tHash(t.id, store)}">${esc(t.name)}</a>`).join('')}</div>
      <div class="filters"><label class="muted" for="st">المتجر</label>
        <select id="st" data-store-filter>${[{ id: '', name: 'كل المتاجر' }, ...DATA.stores].map(s =>
          `<option value="${s.id}" ${s.id === store ? 'selected' : ''}>${esc(s.name)}</option>`).join('')}</select>
        <span class="muted">${list.length} منتج</span></div>
      ${list.length ? `<div class="cards">${list.map(card).join('')}</div>` : '<p class="empty">ما فيه منتجات هنا حالياً.</p>'}
      ${footer()}`;
  }

  function deals() {
    setTitle('العروض');
    const list = DATA.products.filter(p => discount(p) >= 0.15).sort((a, b) => discount(b) - discount(a));
    return `${header(walletPill)}
      <section class="banner"><span class="big" aria-hidden="true">%</span><span class="tag"><i></i>تخفيضات حقيقية</span>
        <h1 style="font-size:clamp(28px,4.5vw,40px);font-weight:800">أقوى العروض الآن</h1>
        <p>مرتبة حسب نسبة الخصم. نبلغك أول ما ينزل سعر أي منتج تبيه.</p></section>
      <div class="cards">${list.map(p => card(p).replace('class="badge b-rank">#' + p.rank, `class="badge b-rank">-${Math.round(discount(p) * 100)}%`)).join('')}</div>
      ${footer()}`;
  }

  function search() {
    const q = S.q.trim();
    setTitle(q ? `بحث: ${q}` : 'بحث');
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    const norm = s => s.toLowerCase().replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي');
    const list = words.length ? DATA.products.filter(p => {
      const hay = norm(`${p.title} ${p.brand || ''} ${CATS[p.category] || ''} ${storesLine(p)}`);
      return words.every(w => hay.includes(norm(w)));
    }) : [];
    return `${header(walletPill)}${searchBox(q)}
      ${q ? `<p class="muted">${list.length ? `${list.length} نتيجة لـ «${esc(q)}»` : `ما لقينا نتائج لـ «${esc(q)}». جرّب كلمة ثانية.`}</p>` : ''}
      ${list.length ? `<div class="cards">${list.map(card).join('')}</div>` : ''}
      ${!list.length ? `<div class="head"><h2>الأكثر بحثاً</h2></div><div class="cards">${DATA.products.slice(0, 4).map(card).join('')}</div>` : ''}
      ${footer()}`;
  }

  function product(h) {
    const p = byPid(h);
    if (!p) return `${header()}<p class="empty">المنتج غير موجود. <a href="#home">ارجع للرئيسية</a></p>`;
    setTitle(p.title);
    const sel = Math.max(0, p.offers.findIndex(o => o.uid === S.sel[p.id]));
    const o = p.offers[sel];
    const hist = o.history.length ? o.history : [{ price: o.price }];
    const lo = Math.min(...hist.map(h => h.price)), hi = Math.max(...hist.map(h => h.price));
    const isLow = o.price <= lo;
    return `<header class="top"><a class="back" href="#home" data-back aria-label="رجوع">${svg(I.back)}</a>
        <button class="back" type="button" data-share aria-label="مشاركة">${svg(I.share)}</button></header>
      <div class="p-grid">
        <div class="stage">${p.image ? `<img src="${esc(p.image)}" alt="${esc(p.title)}">` : svg(iconFor(p), p.title)}
          ${p.rank <= 10 ? `<span class="badge">رقم ${p.rank} في الأكثر رواجاً</span>` : ''}</div>
        <div style="display:flex;flex-direction:column;gap:18px">
          <div class="p-head"><h1>${esc(p.title)}</h1>
            <span class="muted">قارنّا ${p.offers.length > 1 ? `${p.offers.length} متاجر` : 'المتجر'} — مرتبة حسب السعر الحقيقي بعد الكاش باك${p.rating ? ` · ★ ${p.rating}` : ''}</span></div>
          <div class="offers" role="radiogroup" aria-label="اختر المتجر">${p.offers.map((x, i) => `
            <button class="offer" type="button" role="radio" aria-checked="${i === sel}" data-offer="${esc(x.uid)}">
              <span class="mono">${STORE_MONO[x.store] || '?'}</span>
              <span class="m"><b>${esc(storeName(x.store))} ${i === 0 ? '<span class="best">الأوفر</span>' : ''}</b><span>${esc(x.shipping || '')}</span></span>
              <span class="pr"><b>${sar(x.price)}</b>${x.cashback > 0 ? `<span>+${fmt(x.cashback)} كاش باك</span>` : ''}</span>
            </button>`).join('')}</div>
          <section class="net" aria-label="السعر الحقيقي">
            <strong>السعر الحقيقي من ${esc(storeName(o.store))}</strong>
            <span class="v">${fmt(o.net_price)} <small>ر.س</small></span>
            <p>${o.cashback > 0 ? `يرجع لك ${sar(o.cashback)} كاش باك بعد تأكيد الطلب من المتجر.` : 'هذا المتجر ما عليه كاش باك حالياً.'}</p>
          </section>
          <section class="chart" aria-label="سجل السعر">
            <div class="head" style="align-items:center"><strong>سجل السعر في ${esc(storeName(o.store))}</strong>
              ${isLow ? '<span class="badge" style="position:static;background:var(--gold);color:var(--ink)">أقل سعر الآن</span>' : ''}</div>
            <div class="bars" aria-hidden="true">${hist.map(h => `<i class="${h.price <= lo ? 'low' : ''}" style="height:${hi === lo ? 70 : 35 + 65 * (h.price - lo) / (hi - lo)}%"></i>`).join('')}</div>
            <span class="note">من ${sar(lo)} إلى ${sar(hi)} خلال آخر ${hist.length} قراءات</span>
          </section>
          <div class="buybar">
            <a class="btn btn-gold" href="${esc(o.url)}" target="_blank" rel="sponsored noopener">
              <span>${o.sample ? 'افتح في' : 'اشترِ من'} ${esc(storeName(o.store))}</span><span style="display:inline-flex;gap:8px;align-items:center">${sar(o.price)} ${svg(I.out)}</span></a>
            <small>${o.sample ? 'نسخة تجريبية: يفتح لك البحث عن المنتج في المتجر.' : 'تكمل الشراء في المتجر نفسه.'}</small>
          </div>
        </div>
      </div>
      ${footer()}`;
  }

  function wallet() {
    setTitle('المحفظة');
    return `${header()}
      <section class="wallet"><span style="font-weight:600">رصيدك</span><span class="v">0.00 <small style="font-size:16px">ر.س</small></span>
        <span style="font-weight:600">المحفظة تنطلق قريباً — كل طلب عن طريق لقطة يرجع لك منه كاش باك.</span></section>
      <ol class="steps">
        <li><b>1</b><h3>ابحث وقارن</h3><p>نعرض لك سعر المنتج في كل المتاجر مع الشحن.</p></li>
        <li><b>2</b><h3>اشترِ من المتجر نفسه</h3><p>تدفع في المتجر بطريقتك المعتادة. ما يتغير شيء.</p></li>
        <li><b>3</b><h3>استلم الكاش باك</h3><p>بعد تأكيد الطلب يرجع جزء من المبلغ لمحفظتك وتسحبه على STC Pay أو حسابك البنكي.</p></li>
      </ol>
      <section class="banner ivory" aria-labelledby="wl"><span class="tag"><i></i>انضم لأول المستخدمين</span>
        <h2 id="wl">سجّل رقمك ونبلغك أول ما تتفعّل المحفظة</h2>
        ${!FORMS ? '<p style="margin:0;color:#3B3842">التسجيل يفتح قريباً مع إطلاق المحفظة.</p>' : `<form class="form" data-waitlist>
          <label>رقم الجوال<input name="phone" type="tel" inputmode="tel" required pattern="^(\\+?966|0)?5[0-9]{8}$" placeholder="05xxxxxxxx" autocomplete="tel"></label>
          <input name="company" tabindex="-1" autocomplete="off" hidden>
          <button class="btn btn-dark" type="submit">سجّلني</button>
        </form>`}
        <p class="note" data-form-msg style="color:#3B3842" role="status"></p>
      </section>
      ${footer()}`;
  }

  // ---------- router ----------
  function render() {
    const h = location.hash.slice(1) || 'home';
    let html, tab = 'home';
    if (h.startsWith('p-')) { html = product(h); tab = ''; }
    else if (h.startsWith('trending')) { html = trending(); tab = 'trending'; }
    else if (h === 'deals') { html = deals(); tab = 'deals'; }
    else if (h === 'search') { html = search(); tab = ''; }
    else if (h === 'wallet') { html = wallet(); tab = 'wallet'; }
    else html = home();
    main.innerHTML = html;
    document.querySelectorAll('.tabbar a').forEach(a => { if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    if (!render.first) main.focus({ preventScroll: true });
    render.first = false;
    window.scrollTo(0, 0);
  }
  render.first = true;

  // ---------- events ----------
  document.addEventListener('submit', async e => {
    const f = e.target;
    if (f.matches('[data-search]')) {
      e.preventDefault();
      const q = new FormData(f).get('q').trim();
      if (q) { S.q = q; location.hash === '#search' ? render() : (location.hash = '#search'); }
    }
    if (f.matches('[data-waitlist]')) {
      e.preventDefault();
      const msg = main.querySelector('[data-form-msg]');
      const body = new URLSearchParams({ 'form-name': 'waitlist', interest: 'wallet', ...Object.fromEntries(new FormData(f)) });
      try {
        const r = await fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
        if (!r.ok) throw new Error(r.status);
        f.reset(); msg.textContent = 'تم! بنرسل لك رسالة أول ما تتفعّل المحفظة.';
      } catch { msg.textContent = 'ما قدرنا نسجّل الحين. حاول مرة ثانية بعد شوي.'; }
    }
  });
  let visits = 0;
  window.addEventListener('hashchange', () => visits++);
  document.addEventListener('click', async e => {
    if (e.target.closest('[data-back]') && visits > 0) { e.preventDefault(); history.back(); return; }
    const off = e.target.closest('[data-offer]');
    if (off) {
      const p = byPid(location.hash.slice(1));
      if (p) S.sel[p.id] = off.dataset.offer;
      const y = window.scrollY; render(); window.scrollTo(0, y);
      main.querySelector(`[data-offer="${CSS.escape(off.dataset.offer)}"]`)?.focus();
    }
    if (e.target.closest('[data-share]')) {
      const data = { title: document.title, url: location.href };
      try { if (navigator.share && !FRAMED) await navigator.share(data); else { await navigator.clipboard.writeText(location.href); e.target.closest('[data-share]').setAttribute('aria-label', 'تم نسخ الرابط'); } } catch {}
    }
  });
  document.addEventListener('change', e => {
    if (e.target.matches('[data-store-filter]')) {
      const [, cat = ''] = location.hash.slice(1).split('--');
      location.hash = tHash(cat === 'all' ? '' : cat, e.target.value);
    }
  });
  window.addEventListener('hashchange', render);

  // ---------- start ----------
  fetch('data/products.json', { cache: 'no-cache' })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(d => {
      DATA = d;
      d.stores.forEach(s => STORES[s.id] = s.name);
      d.categories.forEach(c => CATS[c.id] = c.name);
      document.getElementById('sample-bar').hidden = !d.sample;
      render();
    })
    .catch(() => { main.innerHTML = '<p class="empty">ما قدرنا نحمّل المنتجات. تأكد من الاتصال وحدّث الصفحة.</p>'; });

  if (!FRAMED && 'serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
})();
