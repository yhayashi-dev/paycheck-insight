/* Suzume opt-in analytics v1. No form, app state or localStorage access. */
(() => {
  'use strict';
  const prior = window.__suzumeAnalyticsV1;
  if (prior) { prior.visit(); return; }
  const c = window.SuzumeAnalyticsConfig;
  const origins = ['https://yhayashi-dev.github.io', 'https://paycheck-insight-dfnvaodwxttypa7gtdouhj.streamlit.app'];
  if (!c || c.enabled !== true || !/^G-[A-Z0-9]{6,20}$/.test(c.measurementId || '') || window.self !== window.top || !origins.includes(c.origin) || location.origin !== c.origin || !/^[A-Za-z0-9_-]+$/.test(c.siteId || '') || !c.basePath?.startsWith('/') || !c.basePath.endsWith('/')) return;
  const id = c.measurementId, cookieName = 'su_analytics_consent_' + c.siteId, gaPrefix = 'su_' + c.siteId + '_ga';
  let granted = false, started = false, lastPath = '', loading = false;
  const channel = typeof BroadcastChannel === 'function' ? new BroadcastChannel('su-analytics-consent-' + c.siteId) : null;
  const layer = window.suzumeDataLayer = [];
  function tag() { layer.push(arguments); }
  const cookie = () => document.cookie.split(';').map(x => x.trim()).find(x => x.startsWith(cookieName + '='))?.slice(cookieName.length + 1) || '';
  const writeChoice = v => { document.cookie = cookieName + '=' + v + '; Path=' + c.basePath + '; Max-Age=7776000; SameSite=Lax; Secure'; };
  function page() {
    const u = new URL(location.href);
    if (u.origin !== c.origin || !u.pathname.startsWith(c.basePath) || !Object.hasOwn(c.pages || {}, u.pathname) || u.hash) return null;
    let campaign = null;
    if (u.search) {
      const keys = [...u.searchParams.keys()];
      if (keys.length !== 3 || new Set(keys).size !== 3 || keys.some(k => !['utm_source', 'utm_medium', 'utm_campaign'].includes(k))) return null;
      const name = u.searchParams.get('utm_campaign');
      const known = Object.hasOwn(c.campaigns || {}, name) ? c.campaigns[name] : null;
      if (!known || known.source !== u.searchParams.get('utm_source') || known.medium !== u.searchParams.get('utm_medium')) return null;
      campaign = {name, ...known};
    }
    const fixed = c.origin + u.pathname;
    return {path:u.pathname, url:fixed, title:String(c.pages[u.pathname]), campaign};
  }
  function source(p) {
    if (p.campaign) return {bucket:p.campaign.source, referrer:''};
    let u; try { u = new URL(document.referrer); } catch { return {bucket:'direct_or_unknown', referrer:''}; }
    const host = u.hostname.toLowerCase();
    if (['x.com','www.x.com','twitter.com','www.twitter.com','t.co'].includes(host)) return {bucket:'x', referrer:u.origin + '/'};
    if (['note.com','www.note.com'].includes(host)) return {bucket:'note', referrer:u.origin + '/'};
    if (['youtube.com','www.youtube.com','m.youtube.com','youtu.be'].includes(host)) return {bucket:'youtube', referrer:u.origin + '/'};
    if (['google.com','www.google.com','google.co.jp','www.google.co.jp'].includes(host)) return {bucket:'google', referrer:u.origin + '/'};
    if (['bing.com','www.bing.com'].includes(host)) return {bucket:'bing', referrer:u.origin + '/'};
    if (host === 'yhayashi-dev.github.io') {
      const prefix = '/' + u.pathname.split('/')[1] + '/';
      const allowed = ['/kurashi-seido-portal/','/policy-guide/','/japan-life-explained/','/manga-world/','/my-chaldea/','/tokyo-support-finder/','/zaisei-no-mikata/','/economy-explained/'];
      if (allowed.includes(prefix)) return {bucket:prefix === c.basePath ? 'internal' : prefix === '/kurashi-seido-portal/' ? 'portal' : 'related_site', referrer:u.origin + prefix};
    }
    return {bucket:'external_other', referrer:''};
  }
  const texts = {
    ja:['アクセス解析の設定','同意した場合のみGoogle Analyticsを使い、閲覧ページ・時刻・流入元・端末情報・仮名Cookieを計測します。通信時にはIPもGoogleへ届きます。入力内容・所持情報・問い合わせ内容は送りません。拒否しても利用できます。中国本土などGoogleに接続できない地域の来訪は捕捉できない場合があります。','同意して計測する','計測しない','プライバシー'],
    en:['Analytics settings','Only with your consent, Google Analytics measures pages, times, sources, device information and pseudonymous cookies. Google also receives your IP in transit. We do not send your inputs, saved game data or messages. You can use this site without analytics. Visits from mainland China or other places where Google is unavailable may not be captured.','Allow analytics','Do not measure','Privacy'],
    vi:['Cài đặt đo lường','Chỉ khi bạn đồng ý, Google Analytics đo trang, thời gian, nguồn truy cập, thiết bị và cookie định danh giả. Google nhận IP khi kết nối. Không gửi nội dung nhập, dữ liệu trò chơi hay tin nhắn. Bạn vẫn dùng được trang khi từ chối.','Đồng ý đo lường','Không đo lường','Quyền riêng tư'],
    zh:['访问统计设置','仅在您同意后使用 Google Analytics，统计页面、时间、来源、设备信息和假名标识 Cookie。通信时 Google 也会接收 IP。不会发送您输入的内容、游戏持有数据或咨询正文。拒绝不影响使用。中国大陆等无法连接 Google 的地区可能无法统计，未记录不代表无人访问。','同意统计','不进行统计','隐私说明']
  };
  const language = document.documentElement.lang.toLowerCase();
  const t = texts[language.startsWith('vi')?'vi':language.startsWith('zh')?'zh':language.startsWith('en')?'en':'ja'];
  let root, panel;
  function render() {
    if (root) return;
    root = document.createElement('div'); root.id = 'su-analytics-root';
    const style = document.createElement('style');
    style.textContent = '#su-analytics-root{font:14px/1.6 system-ui,sans-serif;color:#172b3a}#su-analytics-panel{position:fixed;z-index:2147483000;left:12px;right:12px;bottom:52px;max-width:680px;margin:auto;padding:16px;background:#fff;border:1px solid #738797;border-radius:12px;box-shadow:0 4px 24px #0003;max-height:65vh;overflow:auto}#su-analytics-root button,#su-analytics-root a{font:inherit;min-height:44px;margin:4px;padding:8px 12px;border-radius:6px;white-space:normal}#su-analytics-settings{position:fixed;z-index:2147483000;right:12px;bottom:6px;color:#123d60;background:#fff;border:1px solid #738797}#su-analytics-root button{cursor:pointer;color:#123d60;background:#f2f7fc;border:1px solid #738797}#su-analytics-root p{margin:6px 0}#su-analytics-root a{color:#123d60}';
    if(c.styleUrl){const url=new URL(c.styleUrl,c.origin);if(url.origin!==c.origin||!url.pathname.startsWith(c.basePath))return;const link=document.createElement('link');link.rel='stylesheet';link.href=url.href;root.append(link);}else{root.append(style);}
    panel=document.createElement('section');panel.id='su-analytics-panel';panel.setAttribute('aria-label',t[0]);
    const text=document.createElement('p');text.textContent=t[1];panel.append(text);
    const privacy=document.createElement('a');privacy.textContent=t[4];
    const privacyURL=new URL(c.privacyUrl,c.origin);if(privacyURL.origin!==c.origin) return;privacy.href=privacyURL.href;panel.append(privacy);
    for(const [name,label,fn] of [['accept',t[2],allow],['decline',t[3],decline]]){const b=document.createElement('button');b.type='button';b.id='su-analytics-'+name;b.textContent=label;b.addEventListener('click',fn);panel.append(b);}
    root.append(panel);const settings=document.createElement('button');settings.type='button';settings.id='su-analytics-settings';settings.textContent=t[0];settings.addEventListener('click',()=>{panel.hidden=false;});root.append(settings);document.body.append(root);
  }
  function disable() { window['ga-disable-' + id] = true; }
  function visit() {
    const p=page();
    if (!p) { disable(); return; }
    if (cookie() !== 'yes') { granted=false; disable(); return; }
    granted=true;
    window['ga-disable-' + id] = false;
    const s=source(p);
    const params={page_location:p.url,page_title:p.title,page_referrer:s.referrer,send_page_view:false,cookie_prefix:gaPrefix,cookie_path:c.basePath,cookie_expires:7776000,cookie_update:false,allow_google_signals:false,allow_ad_personalization_signals:false};
    if (p.campaign) Object.assign(params,{campaign_source:p.campaign.source,campaign_medium:p.campaign.medium,campaign_name:p.campaign.name});
    if (!started) {
      started=true;tag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
      tag('consent','update',{analytics_storage:'granted',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});tag('js',new Date());
    }
    tag('config',id,params);
    if (lastPath!==p.path) {
      lastPath=p.path;const event={send_to:id,page_location:p.url,page_title:p.title,page_referrer:s.referrer,site_id:c.siteId,source_bucket:s.bucket};
      if(p.campaign)Object.assign(event,{campaign_source:p.campaign.source,campaign_medium:p.campaign.medium,campaign_name:p.campaign.name});
      if(c.debugMode===true){event.debug_mode=true;event.traffic_type='internal';}
      tag('event','page_view',event);
    }
    if(!loading){loading=true;const script=document.createElement('script');script.async=true;script.referrerPolicy='no-referrer';script.src='https://www.googletagmanager.com/gtag/js?id='+id+'&l=suzumeDataLayer';document.head.append(script);}
  }
  function allow() { if(!page())return;writeChoice('yes');granted=true;panel.hidden=true;channel?.postMessage('yes');visit(); }
  function decline() {
    granted=false;disable();layer.length=0;writeChoice('no');panel.hidden=true;channel?.postMessage('no');
    for(const entry of document.cookie.split(';')){const name=entry.split('=')[0].trim();if(name.startsWith(gaPrefix))document.cookie=name+'=; Path='+c.basePath+'; Max-Age=0; SameSite=Lax; Secure';}
  }
  if (!page()) return;
  const api={visit,openSettings:()=>{if(panel)panel.hidden=false;}};
  window.__suzumeAnalyticsV1=api;window.SuzumeAnalytics=api;
  render();
  const choice=cookie();granted=choice==='yes';panel.hidden=choice==='yes'||choice==='no';
  for(const name of ['pushState','replaceState']){const original=history[name];history[name]=function(...args){disable();const value=original.apply(this,args);queueMicrotask(visit);return value;};}
  channel?.addEventListener('message', e => {
    if (e.data === 'no') { granted=false; disable(); layer.length=0; panel.hidden=true; }
    if (e.data === 'yes' && cookie() === 'yes') { panel.hidden=true; visit(); }
  });
  const checkChoice = () => { if(cookie() !== 'yes') { granted=false; disable(); layer.length=0; } };
  window.addEventListener('focus', checkChoice);
  document.addEventListener('visibilitychange', checkChoice);
  if (window.cookieStore) window.cookieStore.addEventListener('change', checkChoice);
  window.addEventListener('popstate',visit);window.addEventListener('hashchange',visit);window.addEventListener('suzume:page',visit);visit();
})();
