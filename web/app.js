/* Laqta web app — Arabic / English. Reads data/products.json (written by the collector) and renders every screen. */
(() => {
  'use strict';

  // ---------- language ----------
  const L = {
    ar: {
      dir: 'rtl', locale: 'ar-SA-u-ca-gregory', cur: 'ر.س', toggle: 'EN', toggleLabel: 'Switch to English',
      docTitle: 'لقطة — كل المتاجر في مكان واحد', brand: 'لقطة', skip: 'تخطَّ إلى المحتوى',
      sample: 'نسخة تجريبية: المنتجات والأسعار للعرض، وتتحدث تلقائياً بعد ربط المتاجر.',
      tabs: { home: 'الرئيسية', trending: 'رائج', deals: 'عروض', favorites: 'المفضلة' },
      loadErr: 'ما قدرنا نحمّل المنتجات. تأكد من الاتصال وحدّث الصفحة.',
      searchPh: 'ابحث عن أي منتج في 6 متاجر', searchBtn: 'ابحث', searchLabel: 'ابحث في كل المتاجر',
      cashPill: 'الكاش باك', live: 'الأسعار تتحدث تلقائياً · التحديث القادم بعد',
      heroLabel: 'أقوى العروض', slideOf: 'عرض {i} من {n}', slideN: 'العرض {i}', bestAt: 'الأوفر في {s}', compare: 'قارن',
      stores: 'المتاجر', picks: 'مختارات لك', seeAll: 'عرض الكل', bestNow: 'الأكثر مبيعاً الآن', fullRank: 'الترتيب الكامل',
      byCat: 'تسوّق حسب الفئة', nProducts: '{n} منتج', cashBadge: 'كاش باك {v}', drop: '↓ نزل {v}',
      cheapestAt: 'أرخص في {s}', nStores: '{n} متاجر', favAdd: 'إضافة إلى المفضلة: {t}', favRemove: 'إزالة من المفضلة: {t}',
      toastAdd: 'انضاف للمفضلة ♥', toastRemove: 'انشال من المفضلة', copied: 'تم نسخ الرابط',
      trendingTitle: 'الأكثر <span class="gold">مبيعاً</span> في السعودية', all: 'الكل', cats: 'الفئات',
      store: 'المتجر', allStores: 'كل المتاجر', emptyList: 'ما فيه منتجات هنا حالياً.',
      dealsTag: 'تخفيضات حقيقية', dealsTitle: 'أقوى العروض الآن', dealsSub: 'مرتبة حسب نسبة الخصم، والأسعار تتحدث كل كم ساعة.',
      results: '{n} نتيجة لـ «{q}»', noResults: 'ما لقينا نتائج لـ «{q}». جرّب كلمة ثانية.', popular: 'الأكثر بحثاً', searchT: 'بحث',
      back: 'رجوع', share: 'مشاركة', fav: 'المفضلة', notFound: 'المنتج غير موجود.', goHome: 'ارجع للرئيسية',
      rankBadge: 'رقم {n} في الأكثر رواجاً', compared: 'قارنّا {n} متاجر — مرتبة حسب السعر الحقيقي بعد الكاش باك',
      comparedOne: 'متوفر في متجر واحد حالياً', chooseStore: 'اختر المتجر', best: 'الأوفر', plusCash: '+{v} كاش باك',
      realPrice: 'السعر الحقيقي من {s}', cashNote: 'كاش باك متوقع {v} — المحفظة تنطلق قريباً.', noCash: 'هذا المتجر ما عليه كاش باك حالياً.',
      history: 'سجل السعر في {s}', lowestNow: 'أقل سعر الآن', range: 'من {a} إلى {b} خلال آخر {n} قراءات',
      openIn: 'افتح في {s}', buyFrom: 'اشترِ من {s}', sampleNote: 'نسخة تجريبية: يفتح لك البحث عن المنتج في المتجر.',
      realNote: 'تكمل الشراء في المتجر نفسه.', walletT: 'المحفظة', balance: 'رصيدك',
      walletSoon: 'المحفظة تنطلق قريباً — كل طلب عن طريق لقطة يرجع لك منه كاش باك.',
      steps: [['ابحث وقارن', 'نعرض لك سعر المنتج في كل المتاجر مع الشحن.'], ['اشترِ من المتجر نفسه', 'تدفع في المتجر بطريقتك المعتادة. ما يتغير شيء.'],
              ['استلم الكاش باك', 'بعد تأكيد الطلب يرجع جزء من المبلغ لمحفظتك وتسحبه على STC Pay أو حسابك البنكي.']],
      joinTag: 'انضم لأول المستخدمين', joinTitle: 'سجّل رقمك ونبلغك أول ما تتفعّل المحفظة', joinSoon: 'التسجيل يفتح قريباً مع إطلاق المحفظة.',
      phone: 'رقم الجوال', joinBtn: 'سجّلني', joinOk: 'تم! بنرسل لك رسالة أول ما تتفعّل المحفظة.', joinErr: 'ما قدرنا نسجّل الحين. حاول مرة ثانية بعد شوي.',
      favTitle: 'المفضلة', favEmpty: 'ما عندك مفضلة للحين', favEmptyText: 'اضغط على القلب في أي منتج، ونحفظه لك هنا عشان ترجع له بسرعة.',
      browse: 'تصفّح الأكثر مبيعاً', disclosure: 'لقطة تقارن الأسعار بين المتاجر. عند الشراء عبر روابطنا قد نحصل على عمولة من المتجر ونرجع جزءاً منها لك ككاش باك. السعر النهائي هو المعروض في المتجر.',
      amazon: 'بصفتنا شريكاً في برنامج أمازون، نكسب من عمليات الشراء المؤهلة. As an Amazon Associate I earn from qualifying purchases.',
      updated: 'آخر تحديث: {d}', days: v => v,
    },
    en: {
      dir: 'ltr', locale: 'en-GB', cur: 'SAR', toggle: 'ع', toggleLabel: 'التبديل إلى العربية',
      docTitle: 'Laqta — every store in one place', brand: 'Laqta', skip: 'Skip to content',
      sample: 'Preview: products and prices are samples and update automatically once stores are connected.',
      tabs: { home: 'Home', trending: 'Trending', deals: 'Deals', favorites: 'Saved' },
      loadErr: 'We couldn’t load the products. Check your connection and refresh.',
      searchPh: 'Search 6 stores…', searchBtn: 'Search', searchLabel: 'Search every store',
      cashPill: 'Cashback', live: 'Prices update automatically · next update in',
      heroLabel: 'Top deals', slideOf: 'Deal {i} of {n}', slideN: 'Deal {i}', bestAt: 'Best price at {s}', compare: 'Compare',
      stores: 'Stores', picks: 'Picked for you', seeAll: 'See all', bestNow: 'Best sellers now', fullRank: 'Full ranking',
      byCat: 'Shop by category', nProducts: '{n} products', cashBadge: '{v} cashback', drop: '↓ {v} off',
      cheapestAt: 'Cheapest at {s}', nStores: '{n} stores', favAdd: 'Save: {t}', favRemove: 'Remove from saved: {t}',
      toastAdd: 'Saved ♥', toastRemove: 'Removed from saved', copied: 'Link copied',
      trendingTitle: 'Best <span class="gold">sellers</span> in Saudi Arabia', all: 'All', cats: 'Categories',
      store: 'Store', allStores: 'All stores', emptyList: 'No products here yet.',
      dealsTag: 'Real discounts', dealsTitle: 'Top deals right now', dealsSub: 'Sorted by discount size. Prices refresh every few hours.',
      results: '{n} results for “{q}”', noResults: 'No results for “{q}”. Try another word.', popular: 'Popular', searchT: 'Search',
      back: 'Back', share: 'Share', fav: 'Save', notFound: 'Product not found.', goHome: 'Back to home',
      rankBadge: '#{n} trending', compared: 'Compared across {n} stores — sorted by real price after cashback',
      comparedOne: 'Available in one store right now', chooseStore: 'Choose a store', best: 'Best', plusCash: '+{v} cashback',
      realPrice: 'Real price at {s}', cashNote: 'Expected cashback {v} — wallet launching soon.', noCash: 'No cashback at this store right now.',
      history: 'Price history at {s}', lowestNow: 'Lowest price now', range: 'From {a} to {b} over the last {n} readings',
      openIn: 'Open in {s}', buyFrom: 'Buy from {s}', sampleNote: 'Preview: opens a search for this product on the store.',
      realNote: 'You complete the purchase on the store’s site.', walletT: 'Wallet', balance: 'Your balance',
      walletSoon: 'The wallet is launching soon — every order through Laqta earns you cashback.',
      steps: [['Search and compare', 'See the product’s price in every store, shipping included.'], ['Buy from the store', 'Pay on the store’s site the way you always do.'],
              ['Get cashback', 'Once the order is confirmed, part of it comes back to your wallet, ready to withdraw to STC Pay or your bank.']],
      joinTag: 'Be one of the first', joinTitle: 'Leave your number and we’ll tell you when the wallet opens', joinSoon: 'Sign-up opens soon, with the wallet launch.',
      phone: 'Mobile number', joinBtn: 'Notify me', joinOk: 'Done! We’ll message you when the wallet opens.', joinErr: 'We couldn’t sign you up right now. Please try again shortly.',
      favTitle: 'Saved', favEmpty: 'Nothing saved yet', favEmptyText: 'Tap the heart on any product and it’ll be waiting for you here.',
      browse: 'Browse best sellers', disclosure: 'Laqta compares prices between stores. When you buy through our links we may earn a commission from the store and share part of it with you as cashback. The final price is the one shown by the store.',
      amazon: 'As an Amazon Associate I earn from qualifying purchases.',
      updated: 'Last updated: {d}', days: v => String(v || '').replace(/أيام|يوم/g, 'days'),
    },
  };
  const STORE_EN = { amazon: 'Amazon', noon: 'noon', shein: 'SHEIN', aliexpress: 'AliExpress', namshi: 'Namshi', temu: 'Temu' };
  const CAT_EN = { tech: 'Electronics', fashion: 'Fashion', beauty: 'Perfume & beauty', home: 'Home', kids: 'Kids', other: 'Other' };
  let lang = (() => { try { return localStorage.getItem('laqta-lang') === 'en' ? 'en' : 'ar'; } catch { return 'ar'; } })();
  const T = () => L[lang];
  const t = (k, v = {}) => String(T()[k]).replace(/\{(\w+)\}/g, (_, x) => v[x] ?? '');

  // ---------- icons ----------
  const STORE_MONO = { amazon: 'A', noon: 'N', shein: 'S', aliexpress: 'Ae', namshi: 'Nm', temu: 'T' };
  const ICONS = {
    tech: '<path d="M3 14v-2a9 9 0 0 1 18 0v2"/><rect x="2" y="14" width="5" height="7" rx="2"/><rect x="17" y="14" width="5" height="7" rx="2"/>',
    fashion: '<path d="M12 8V7a2 2 0 1 0-2-2"/><path d="M12 8 2.6 15.4A1.5 1.5 0 0 0 3.5 18h17a1.5 1.5 0 0 0 .9-2.6z"/>',
    beauty: '<rect x="6" y="9" width="12" height="13" rx="3"/><path d="M9 9V6h6v3M10 6V3h4v3M9 14h6"/>',
    home: '<path d="M8 2h8l3 8H5z"/><path d="M12 10v9M8 22h8"/>',
    kids: '<rect x="3" y="12" width="8" height="8" rx="1.5"/><rect x="13" y="12" width="8" height="8" rx="1.5"/><rect x="8" y="3" width="8" height="8" rx="1.5"/>',
    other: '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
  };
  const EXTRA = {
    watch: '<rect x="6" y="6" width="12" height="12" rx="3"/><path d="M9 6l1-4h4l1 4M9 18l1 4h4l1-4M12 10v2l1.5 1.5"/>',
    charger: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    bag: '<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/>',
    pot: '<path d="M4 10h16v7a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path d="M2 10h20M9 6V4M15 6V4"/>',
  };
  const WORDS = [[/ساعة|watch/i, 'watch'], [/شاحن|charger/i, 'charger'], [/حقيبة|شنطة|backpack|bag/i, 'bag'], [/قلاية|fryer|طنجرة/i, 'pot']];
  const I = {
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    wallet: '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    back: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    out: '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    arrow: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
    heart: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7z"/>',
  };
  const svg = (p, label, cls = '') => `<svg viewBox="0 0 24 24" ${cls ? `class="${cls}"` : ''} ${label ? `role="img" aria-label="${esc(label)}"` : 'aria-hidden="true"'}>${p}</svg>`;
  // Each category gets its own colour pair: tile background + bright accent.
  const THEME = { tech: ['#18213D', '#8FB2FF'], fashion: ['#37172A', '#FF93B8'], beauty: ['#382711', '#F5C76E'],
                  home: ['#10302A', '#71DCC3'], kids: ['#25310D', '#BFE36F'], other: ['#262036', '#C7B5FF'] };
  const STORE_COLOR = { amazon: '#F5A524', noon: '#F7E15A', shein: '#F5F0E6', aliexpress: '#FF6A4D', namshi: '#A99BFF', temu: '#FF8A3D' };

  // ---------- state & helpers ----------
  let DATA = null, STORES = {}, CATS = {};
  const main = document.getElementById('main');
  const S = { q: '', sel: {} };
  const FRAMED = (() => { try { return window.self !== window.top; } catch { return true; } })();
  const FORMS = !FRAMED && /\.netlify\.app$/.test(location.hostname);  // early-access form saves through Netlify Forms
  const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const FAV = (() => { try { return new Set(JSON.parse(localStorage.getItem('laqta-fav') || '[]')); } catch { return new Set(); } })();
  const saveFav = () => { try { localStorage.setItem('laqta-fav', JSON.stringify([...FAV])); } catch {} };

  function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  const fmt = n => Number(n).toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: Number.isInteger(+n) ? 0 : 2 });
  const sar = n => lang === 'en' ? `SAR ${fmt(n)}` : `${fmt(n)} ر.س`;
  const discount = p => (p.old_price && p.old_price > p.price) ? 1 - p.price / p.old_price : 0;
  const pct = p => Math.round(discount(p) * 100);
  const storeName = id => lang === 'en' ? (STORE_EN[id] || id) : (STORES[id] || id);
  const catName = id => lang === 'en' ? (CAT_EN[id] || id) : (CATS[id] || id);
  const titleOf = p => (lang === 'en' && p.title_en) || p.title;
  const storesLine = p => p.offers.map(o => storeName(o.store)).join(' · ');
  const iconFor = p => { const w = WORDS.find(([re]) => re.test(p.title + ' ' + (p.title_en || ''))); return w ? EXTRA[w[1]] : (ICONS[p.category] || ICONS.other); };
  const thumb = p => p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : `<span class="duo">${svg(iconFor(p))}</span>`;
  const tstyle = cat => { const [bg, ac] = THEME[cat] || THEME.other; return `--tbg:${bg};--tac:${ac}`; };
  const dropOf = p => { const o = p.offers[0]; return o && o.history.length > 1 ? Math.round(o.history[0].price - o.price) : 0; };
  const pid = id => 'p-' + String(id).replace(/^g_/, '').replace(/[^A-Za-z0-9-]/g, '-');
  const byPid = h => DATA.products.find(p => pid(p.id) === h);
  const tHash = (cat, store) => '#trending' + (cat || store ? `--${cat || 'all'}` : '') + (store ? `--${store}` : '');
  function setTitle(x) { document.title = x ? `${x} — ${t('brand')}` : t('docTitle'); }
  // Next automatic price update: the workflow runs at minute 17 of every 3rd UTC hour.
  function nextUpdate() {
    const d = new Date(); d.setUTCSeconds(0, 0); d.setUTCMinutes(17);
    while (d <= new Date() || d.getUTCHours() % 3) d.setUTCHours(d.getUTCHours() + 1);
    return d;
  }
  const hms = ms => { const s = Math.max(0, Math.floor(ms / 1000)); return [s / 3600, (s % 3600) / 60, s % 60].map(n => String(Math.floor(n)).padStart(2, '0')).join(':'); };

  // ---------- pieces ----------
  function card(p, i = 0) {
    const on = FAV.has(p.id), drop = dropOf(p);
    return `<article class="card" style="--i:${Math.min(i, 12)}">
      <a class="card-link" href="#${pid(p.id)}">
        <div class="thumb" style="${tstyle(p.category)}">${thumb(p)}
          ${p.max_cashback > 0 ? `<span class="badge b-cash">${t('cashBadge', { v: sar(p.max_cashback) })}</span>` : ''}
          ${pct(p) >= 10 ? `<span class="badge b-off">-${pct(p)}%</span>` : `<span class="badge b-rank">#${p.rank}</span>`}
          ${drop > 0 ? `<span class="badge b-drop">${t('drop', { v: sar(drop) })}</span>` : ''}</div>
        <span class="t">${esc(titleOf(p))}</span>
        <div class="price"><b>${sar(p.price)}</b>${p.old_price ? `<s>${fmt(p.old_price)}</s>` : ''}</div>
        <div class="meta"><span class="sdot" style="--sc:${STORE_COLOR[p.best_store] || '#fff'}"></span>${esc(t('cheapestAt', { s: storeName(p.best_store) }))}
          ${p.offers.length > 1 ? `<span class="muted">· ${t('nStores', { n: p.offers.length })}</span>` : ''}</div>
      </a>
      <button class="fav" type="button" data-fav="${esc(p.id)}" aria-pressed="${on}" aria-label="${esc(t(on ? 'favRemove' : 'favAdd', { t: titleOf(p) }))}">${svg(I.heart)}</button>
    </article>`;
  }
  const row = (p, n) => `<li><a href="#${pid(p.id)}"><span class="n">${n}</span>
      <span class="ic" style="${tstyle(p.category)}">${svg(iconFor(p))}</span>
      <span class="m"><span>${esc(titleOf(p))}</span><span>${esc(storesLine(p))}</span></span>
      <span class="p">${sar(p.price)}</span></a></li>`;
  const langBtn = () => `<button class="lang" type="button" data-lang aria-label="${esc(t('toggleLabel'))}" lang="${lang === 'ar' ? 'en' : 'ar'}">${t('toggle')}</button>`;
  const header = (right = '') => `<header class="top">
      <a class="logo" href="#home" aria-label="${esc(t('brand'))}"><span class="mark" aria-hidden="true"><i></i></span><b>${t('brand')}</b></a>
      <span class="top-end">${right}${langBtn()}</span></header>`;
  const walletPill = () => `<a class="pill" href="#wallet"><span class="dot">${svg(I.wallet)}</span><span>${t('cashPill')}</span></a>`;
  const searchBox = (q = '') => `<form class="search" role="search" data-search>
      ${svg(I.search)}<input name="q" value="${esc(q)}" aria-label="${esc(t('searchLabel'))}" placeholder="${esc(t('searchPh'))}" autocomplete="off">
      <button type="submit">${t('searchBtn')}</button></form>`;
  const footer = () => `<footer class="foot"><span>${t('disclosure')}</span><span>${t('amazon')}</span>
      <span>${esc(t('updated', { d: new Date(DATA.generated_at).toLocaleString(T().locale, { dateStyle: 'medium', timeStyle: 'short' }) }))}</span></footer>`;

  // ---------- screens ----------
  function home() {
    setTitle('');
    const P = DATA.products;
    const top = [...P].sort((a, b) => discount(b) - discount(a)).slice(0, 5);
    return `${header(walletPill())}
      ${searchBox()}
      <div class="live"><span class="pulse" aria-hidden="true"></span><span>${t('live')} <b data-countdown>${hms(nextUpdate() - Date.now())}</b></span></div>
      <section class="hero" aria-roledescription="carousel" aria-label="${esc(t('heroLabel'))}">
        <div class="slides" data-carousel>${top.map((p, i) => `
          <a class="slide" href="#${pid(p.id)}" style="${tstyle(p.category)}" aria-label="${esc(t('slideOf', { i: i + 1, n: top.length }))}: ${esc(titleOf(p))}">
            <span class="off">-${pct(p)}%</span>
            <span class="slide-ic" aria-hidden="true">${svg(iconFor(p))}</span>
            <span class="slide-txt"><small>${esc(t('bestAt', { s: storeName(p.best_store) }))}</small><b>${esc(titleOf(p))}</b>
              <span class="sp"><b>${sar(p.price)}</b>${p.old_price ? `<s>${fmt(p.old_price)}</s>` : ''}</span></span>
            <span class="go" aria-hidden="true">${t('compare')} ${svg(I.arrow, '', 'flip')}</span>
          </a>`).join('')}</div>
        <div class="dots">${top.map((p, i) => `<button type="button" data-dot="${i}" aria-label="${esc(t('slideN', { i: i + 1 }))}" aria-current="${i === 0}"></button>`).join('')}</div>
      </section>
      <div class="row-scroll stores" aria-label="${esc(t('stores'))}">${DATA.stores.map(s =>
        `<a class="store-dot" href="${tHash('', s.id)}" style="--sc:${STORE_COLOR[s.id] || '#fff'}"><b>${STORE_MONO[s.id] || '?'}</b><span>${esc(storeName(s.id))}</span></a>`).join('')}</div>
      <div class="head"><h2>${t('picks')}</h2><a href="#trending">${t('seeAll')}</a></div>
      <div class="cards scroll">${P.slice(0, 8).map(card).join('')}</div>
      <div class="head"><h2>${t('bestNow')}</h2><a href="#trending">${t('fullRank')}</a></div>
      <ol class="list">${P.slice(0, 5).map((p, i) => row(p, i + 1)).join('')}</ol>
      <div class="head"><h2>${t('byCat')}</h2></div>
      <div class="cats">${DATA.categories.filter(c => P.some(p => p.category === c.id)).map(c =>
        `<a class="cat" href="${tHash(c.id, '')}" style="${tstyle(c.id)}"><span class="duo">${svg(ICONS[c.id] || ICONS.other)}</span><b>${esc(catName(c.id))}</b>
          <small>${t('nProducts', { n: P.filter(p => p.category === c.id).length })}</small></a>`).join('')}</div>
      ${footer()}`;
  }

  function trending() {
    setTitle(t('tabs').trending);
    const [, cat0 = '', store = ''] = location.hash.slice(1).split('--');
    const cat = cat0 === 'all' ? '' : cat0;
    const list = DATA.products.filter(p => (!cat || p.category === cat) && (!store || p.offers.some(o => o.store === store)));
    const tabs = [{ id: '' }, ...DATA.categories.filter(c => DATA.products.some(p => p.category === c.id))];
    return `${header(walletPill())}
      <h1 class="page-title">${t('trendingTitle')}</h1>
      <div class="row-scroll" role="tablist" aria-label="${esc(t('cats'))}">${tabs.map(c =>
        `<a class="chip" role="tab" aria-selected="${c.id === cat}" href="${tHash(c.id, store)}">${esc(c.id ? catName(c.id) : t('all'))}</a>`).join('')}</div>
      <div class="filters"><label class="muted" for="st">${t('store')}</label>
        <select id="st" data-store-filter>${[{ id: '' }, ...DATA.stores].map(s =>
          `<option value="${s.id}" ${s.id === store ? 'selected' : ''}>${esc(s.id ? storeName(s.id) : t('allStores'))}</option>`).join('')}</select>
        <span class="muted">${t('nProducts', { n: list.length })}</span></div>
      ${list.length ? `<div class="cards">${list.map(card).join('')}</div>` : `<p class="empty">${t('emptyList')}</p>`}
      ${footer()}`;
  }

  function deals() {
    setTitle(t('tabs').deals);
    const list = DATA.products.filter(p => discount(p) >= 0.15).sort((a, b) => discount(b) - discount(a));
    return `${header(walletPill())}
      <section class="banner"><span class="big" aria-hidden="true">%</span><span class="tag"><i></i>${t('dealsTag')}</span>
        <h1>${t('dealsTitle')}</h1><p>${t('dealsSub')}</p></section>
      <div class="cards">${list.map(card).join('')}</div>
      ${footer()}`;
  }

  function search() {
    const q = S.q.trim();
    setTitle(q || t('searchT'));
    const norm = s => s.toLowerCase().replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي');
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    const list = words.length ? DATA.products.filter(p => {
      const hay = norm(`${p.title} ${p.title_en || ''} ${p.brand || ''} ${CATS[p.category] || ''} ${CAT_EN[p.category] || ''} ${p.offers.map(o => `${STORES[o.store]} ${STORE_EN[o.store]}`).join(' ')}`);
      return words.every(w => hay.includes(norm(w)));
    }) : [];
    return `${header(walletPill())}${searchBox(q)}
      ${q ? `<p class="muted">${esc(list.length ? t('results', { n: list.length, q }) : t('noResults', { q }))}</p>` : ''}
      ${list.length ? `<div class="cards">${list.map(card).join('')}</div>` :
        `<div class="head"><h2>${t('popular')}</h2></div><div class="cards">${DATA.products.slice(0, 4).map(card).join('')}</div>`}
      ${footer()}`;
  }

  function product(h) {
    const p = byPid(h);
    if (!p) return `${header()}<p class="empty">${t('notFound')} <a href="#home">${t('goHome')}</a></p>`;
    setTitle(titleOf(p));
    const sel = Math.max(0, p.offers.findIndex(o => o.uid === S.sel[p.id]));
    const o = p.offers[sel];
    const hist = o.history.length ? o.history : [{ price: o.price }];
    const lo = Math.min(...hist.map(x => x.price)), hi = Math.max(...hist.map(x => x.price));
    const s = storeName(o.store);
    return `<header class="top"><a class="back" href="#home" data-back aria-label="${esc(t('back'))}">${svg(I.back, '', 'flip')}</a>
        <span class="top-end"><button class="back fav-lg" type="button" data-fav="${esc(p.id)}" aria-pressed="${FAV.has(p.id)}" aria-label="${esc(t('fav'))}">${svg(I.heart)}</button>
        <button class="back" type="button" data-share aria-label="${esc(t('share'))}">${svg(I.share)}</button>${langBtn()}</span></header>
      <div class="p-grid">
        <div class="stage" style="${tstyle(p.category)}">${p.image ? `<img src="${esc(p.image)}" alt="${esc(titleOf(p))}">` : `<span class="duo">${svg(iconFor(p), titleOf(p))}</span>`}
          ${pct(p) >= 10 ? `<span class="badge b-off">-${pct(p)}%</span>` : ''}
          ${p.rank <= 10 ? `<span class="badge b-rank-lg">${t('rankBadge', { n: p.rank })}</span>` : ''}</div>
        <div class="p-side">
          <div class="p-head"><h1>${esc(titleOf(p))}</h1>
            <span class="muted">${p.offers.length > 1 ? t('compared', { n: p.offers.length }) : t('comparedOne')}${p.rating ? ` · ★ ${p.rating}` : ''}</span></div>
          <div class="offers" role="radiogroup" aria-label="${esc(t('chooseStore'))}">${p.offers.map((x, i) => `
            <button class="offer" type="button" role="radio" aria-checked="${i === sel}" data-offer="${esc(x.uid)}">
              <span class="mono" style="--sc:${STORE_COLOR[x.store] || '#fff'}">${STORE_MONO[x.store] || '?'}</span>
              <span class="m"><b>${esc(storeName(x.store))} ${i === 0 ? `<span class="best">${t('best')}</span>` : ''}</b><span>${esc(T().days(x.shipping))}</span></span>
              <span class="pr"><b>${sar(x.price)}</b>${x.cashback > 0 ? `<span>${t('plusCash', { v: fmt(x.cashback) })}</span>` : ''}</span>
            </button>`).join('')}</div>
          <section class="net" aria-label="${esc(t('realPrice', { s }))}">
            <strong>${esc(t('realPrice', { s }))}</strong>
            <span class="v">${lang === 'en' ? '<small>SAR</small> ' : ''}<span data-net="${o.net_price}">${fmt(o.net_price)}</span>${lang === 'ar' ? ' <small>ر.س</small>' : ''}</span>
            <p>${esc(o.cashback > 0 ? t('cashNote', { v: sar(o.cashback) }) : t('noCash'))}</p>
          </section>
          <section class="chart">
            <div class="head"><strong>${esc(t('history', { s }))}</strong>${o.price <= lo ? `<span class="pill-gold">${t('lowestNow')}</span>` : ''}</div>
            <div class="bars" aria-hidden="true">${hist.map((x, i) => `<i class="${x.price <= lo ? 'low' : ''}" style="--h:${hi === lo ? 70 : 35 + 65 * (x.price - lo) / (hi - lo)}%;--i:${i}"></i>`).join('')}</div>
            <span class="note">${esc(t('range', { a: sar(lo), b: sar(hi), n: hist.length }))}</span>
          </section>
          <div class="buybar">
            <a class="btn btn-gold shine" href="${esc(o.url)}" target="_blank" rel="sponsored noopener">
              <span>${esc(t(o.sample ? 'openIn' : 'buyFrom', { s }))}</span><span class="bb-p">${sar(o.price)} ${svg(I.out)}</span></a>
            <small>${t(o.sample ? 'sampleNote' : 'realNote')}</small>
          </div>
        </div>
      </div>
      ${footer()}`;
  }

  function wallet() {
    setTitle(t('walletT'));
    return `${header()}
      <section class="wallet"><span class="w-l">${t('balance')}</span><span class="v">0.00 <small>${T().cur}</small></span>
        <span class="w-l">${t('walletSoon')}</span></section>
      <ol class="steps">${T().steps.map(([h, d], i) => `<li><b>${i + 1}</b><h3>${h}</h3><p>${d}</p></li>`).join('')}</ol>
      <section class="banner"><span class="tag"><i></i>${t('joinTag')}</span><h2>${t('joinTitle')}</h2>
        ${!FORMS ? `<p>${t('joinSoon')}</p>` : `<form class="form" data-waitlist>
          <label>${t('phone')}<input name="phone" type="tel" inputmode="tel" required pattern="^(\\+?966|0)?5[0-9]{8}$" placeholder="05xxxxxxxx" autocomplete="tel" dir="ltr"></label>
          <input name="company" tabindex="-1" autocomplete="off" hidden>
          <button class="btn btn-dark" type="submit">${t('joinBtn')}</button></form>`}
        <p class="note" data-form-msg role="status"></p></section>
      ${footer()}`;
  }

  function favorites() {
    setTitle(t('favTitle'));
    const list = DATA.products.filter(p => FAV.has(p.id));
    return `${header(walletPill())}
      <h1 class="page-title">${t('favTitle')} <span class="gold">${list.length || ''}</span></h1>
      ${list.length ? `<div class="cards">${list.map(card).join('')}</div>` : `
      <section class="empty-fav"><span class="big-heart" aria-hidden="true">${svg(I.heart)}</span>
        <h2>${t('favEmpty')}</h2><p class="muted">${t('favEmptyText')}</p>
        <a class="btn btn-gold" href="#trending">${t('browse')}</a></section>`}
      ${footer()}`;
  }

  // ---------- chrome (things outside <main>) ----------
  function chrome() {
    document.documentElement.lang = lang;
    document.documentElement.dir = T().dir;
    const skip = document.querySelector('.skip'); if (skip) skip.textContent = t('skip');
    const bar = document.getElementById('sample-bar'); if (bar) bar.textContent = t('sample');
    document.querySelectorAll('.tabbar a').forEach(a => { const s = a.querySelector('span'); if (s) s.textContent = T().tabs[a.dataset.tab]; });
    document.querySelector('.tabbar')?.setAttribute('aria-label', lang === 'en' ? 'Main menu' : 'القائمة الرئيسية');
  }

  // ---------- router ----------
  function render() {
    const h = location.hash.slice(1) || 'home';
    let html, tab = 'home';
    if (h.startsWith('p-')) { html = product(h); tab = ''; }
    else if (h.startsWith('trending')) { html = trending(); tab = 'trending'; }
    else if (h === 'deals') { html = deals(); tab = 'deals'; }
    else if (h === 'search') { html = search(); tab = ''; }
    else if (h === 'wallet') { html = wallet(); tab = ''; }
    else if (h === 'favorites') { html = favorites(); tab = 'favorites'; }
    else html = home();
    main.innerHTML = html;
    [...main.children].forEach((c, i) => c.style.setProperty('--d', Math.min(i, 8)));
    main.classList.remove('enter'); void main.offsetWidth; main.classList.add('enter');
    document.querySelectorAll('.tabbar a').forEach(a => { if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    startCarousel();
    if (!render.first) main.focus({ preventScroll: true });
    render.first = false;
    window.scrollTo(0, 0);
  }
  render.first = true;

  // ---------- little delights ----------
  let toastTimer;
  function toast(msg) {
    const el = document.getElementById('toast'); if (!el) return;
    el.textContent = msg; el.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('show'), 1800);
  }
  function countUp(el, from, to) {
    if (REDUCED || from === to) return;
    const t0 = performance.now(), d = 450;
    const step = now => { const k = Math.min(1, (now - t0) / d), e = 1 - Math.pow(1 - k, 3);
      el.textContent = fmt(Math.round((from + (to - from) * e) * 100) / 100); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }
  let carTimer, carIdx = 0, carPaused = 0;
  function goSlide(i, user) {
    const box = main.querySelector('[data-carousel]'); if (!box) return;
    const n = box.children.length; carIdx = (i + n) % n;
    box.scrollTo({ left: box.children[carIdx].offsetLeft - box.children[0].offsetLeft, behavior: REDUCED ? 'auto' : 'smooth' });
    if (user) carPaused = Date.now();
  }
  function startCarousel() {
    clearInterval(carTimer); carIdx = 0;
    const box = main.querySelector('[data-carousel]'); if (!box) return;
    box.addEventListener('scroll', () => {
      carIdx = Math.round(Math.abs(box.scrollLeft) / box.clientWidth);
      main.querySelectorAll('[data-dot]').forEach(d => d.setAttribute('aria-current', +d.dataset.dot === carIdx));
    }, { passive: true });
    ['pointerdown', 'focusin'].forEach(ev => box.addEventListener(ev, () => { carPaused = Date.now(); }));
    if (!REDUCED) carTimer = setInterval(() => { if (Date.now() - carPaused > 6000 && !document.hidden) goSlide(carIdx + 1); }, 4200);
  }
  setInterval(() => { const el = document.querySelector('[data-countdown]'); if (el) el.textContent = hms(nextUpdate() - Date.now()); }, 1000);

  // ---------- events ----------
  document.addEventListener('submit', async e => {
    const f = e.target;
    if (f.matches('[data-search]')) {
      e.preventDefault();
      const q = String(new FormData(f).get('q') || '').trim();
      if (q) { S.q = q; location.hash === '#search' ? render() : (location.hash = '#search'); }
    }
    if (f.matches('[data-waitlist]')) {
      e.preventDefault();
      const msg = main.querySelector('[data-form-msg]');
      const body = new URLSearchParams({ 'form-name': 'waitlist', interest: 'wallet', ...Object.fromEntries(new FormData(f)) });
      try {
        const r = await fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
        if (!r.ok) throw new Error(r.status);
        f.reset(); msg.textContent = t('joinOk');
      } catch { msg.textContent = t('joinErr'); }
    }
  });
  let visits = 0;
  window.addEventListener('hashchange', () => visits++);
  document.addEventListener('click', async e => {
    if (e.target.closest('[data-back]') && visits > 0) { e.preventDefault(); history.back(); return; }
    if (e.target.closest('[data-lang]')) {
      lang = lang === 'ar' ? 'en' : 'ar';
      try { localStorage.setItem('laqta-lang', lang); } catch {}
      chrome(); const y = window.scrollY; render(); window.scrollTo(0, y);
      main.querySelector('[data-lang]')?.focus();
      return;
    }
    const fv = e.target.closest('[data-fav]');
    if (fv) {
      e.preventDefault();
      const id = fv.dataset.fav, on = !FAV.has(id);
      on ? FAV.add(id) : FAV.delete(id); saveFav();
      const p = DATA.products.find(x => x.id === id);
      document.querySelectorAll(`[data-fav="${CSS.escape(id)}"]`).forEach(b => {
        b.setAttribute('aria-pressed', on);
        if (b.classList.contains('fav') && p) b.setAttribute('aria-label', t(on ? 'favRemove' : 'favAdd', { t: titleOf(p) }));
      });
      toast(t(on ? 'toastAdd' : 'toastRemove'));
      if (location.hash === '#favorites' && !on) { const y = window.scrollY; render(); window.scrollTo(0, y); }
      return;
    }
    const dot = e.target.closest('[data-dot]');
    if (dot) { goSlide(+dot.dataset.dot, true); return; }
    const off = e.target.closest('[data-offer]');
    if (off) {
      const p = byPid(location.hash.slice(1));
      const before = parseFloat(main.querySelector('[data-net]')?.dataset.net || 0);
      if (p) S.sel[p.id] = off.dataset.offer;
      const y = window.scrollY; render(); window.scrollTo(0, y);
      const el = main.querySelector('[data-net]');
      if (el && before) countUp(el, before, parseFloat(el.dataset.net));
      main.querySelector(`[data-offer="${CSS.escape(off.dataset.offer)}"]`)?.focus();
      return;
    }
    const sh = e.target.closest('[data-share]');
    if (sh) {
      try { if (navigator.share && !FRAMED) await navigator.share({ title: document.title, url: location.href });
            else { await navigator.clipboard.writeText(location.href); toast(t('copied')); } } catch {}
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
  chrome();
  fetch('data/products.json', { cache: 'no-cache' })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(d => {
      DATA = d;
      d.stores.forEach(s => STORES[s.id] = s.name);
      d.categories.forEach(c => CATS[c.id] = c.name);
      document.getElementById('sample-bar').hidden = !d.sample;
      render();
    })
    .catch(() => { main.innerHTML = `<p class="empty">${t('loadErr')}</p>`; });

  if (!FRAMED && 'serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
})();
