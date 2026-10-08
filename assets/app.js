'use strict';
const menu=document.querySelector('#menu');
menu?.addEventListener('click',()=>{const open=document.body.classList.toggle('menu-open');menu.setAttribute('aria-expanded',String(open));});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){document.body.classList.remove('menu-open');menu?.setAttribute('aria-expanded','false');}});
const search=document.querySelector('#search'), results=document.querySelector('#results');
let indexPromise;
search?.addEventListener('input',async()=>{const query=search.value.trim().toLowerCase();results.replaceChildren();if(!query)return;try{indexPromise??=fetch('search.json').then(r=>{if(!r.ok)throw Error();return r.json();});const data=await indexPromise;if(query!==search.value.trim().toLowerCase())return;const found=data.filter(x=>`${x.title} ${x.goal} ${x.part}`.toLowerCase().includes(query));for(const x of found){const a=document.createElement('a');a.href=`${x.slug}.html`;a.textContent=x.title;results.append(a);}if(!found.length)results.textContent='該当する講義がありません。別の言葉を試してください。';}catch{indexPromise=undefined;results.textContent='検索を読み込めません。下の目次をご利用ください。';}});
function softmax(){const z=[...document.querySelectorAll('[data-logit]')].map(x=>Number(x.value));if(!z.length)return;const t=Number(document.querySelector('#temperature').value),m=Math.max(...z),e=z.map(x=>Math.exp((x-m)/t)),s=e.reduce((a,b)=>a+b,0);document.querySelector('#softmax-output').replaceChildren();e.forEach((x,i)=>{const row=document.createElement('div');row.className='bar-row';const label=document.createElement('span');label.textContent=`候補 ${i+1}: ${(x/s*100).toFixed(1)}%`;const bar=document.createElement('div');bar.className='bar';bar.style.width=`${x/s*55}%`;row.append(label,bar);document.querySelector('#softmax-output').append(row);});document.querySelector('#temperature-value').textContent=t.toFixed(1);}
document.querySelectorAll('[data-logit],#temperature').forEach(x=>x.addEventListener('input',softmax));softmax();

for(const panel of document.querySelectorAll('[data-lesson]')){
  const key=`llm-textbook-note:${panel.dataset.lesson}`;
  const field=panel.querySelector('textarea'), status=panel.querySelector('[data-note-status]');
  try{field.value=localStorage.getItem(key)||'';}catch{status.textContent='保存を使えない設定です。紙や端末のメモへ記録してください。';}
  panel.querySelector('[data-save-note]').addEventListener('click',()=>{
    try{localStorage.setItem(key,field.value);status.textContent='この端末へ保存しました。ページを開き直すと戻ります。';}
    catch{status.textContent='保存できませんでした。紙や端末のメモへ記録してください。';}
  });
  panel.querySelector('[data-clear-note]').addEventListener('click',()=>{
    try{localStorage.removeItem(key);field.value='';status.textContent='このページのメモを消しました。';}
    catch{status.textContent='削除できませんでした。ブラウザの保存設定をご確認ください。';}
  });
}

// Everything below is stored only in this browser; failures leave the page usable.
const store={get(k){try{return localStorage.getItem(k);}catch{return null;}},set(k,v){try{localStorage.setItem(k,v);return true;}catch{return false;}},remove(k){try{localStorage.removeItem(k);}catch{}}};
const page=document.body.dataset.page||'index';
const slugOf=href=>(href||'').split('#')[0].replace(/\.html$/,'').split('/').pop();

// Theme: an explicit choice wins over the system setting.
const themeButton=document.querySelector('#theme');
const darkQuery=window.matchMedia?.('(prefers-color-scheme: dark)');
function isDark(){const t=document.documentElement.dataset.theme;return t?t==='dark':!!darkQuery?.matches;}
function showTheme(){if(!themeButton)return;const dark=isDark();themeButton.textContent=dark?'明るい表示':'暗い表示';themeButton.setAttribute('aria-pressed',String(dark));}
themeButton?.addEventListener('click',()=>{const next=isDark()?'light':'dark';document.documentElement.dataset.theme=next;store.set('llm-textbook-theme',next);showTheme();});
darkQuery?.addEventListener?.('change',showTheme);showTheme();

// "/" jumps to search, as on many documentation sites.
document.addEventListener('keydown',event=>{
  if(event.key!=='/'||event.ctrlKey||event.metaKey||event.altKey||event.target.closest?.('input,textarea,select,[contenteditable]'))return;
  if(!search)return;event.preventDefault();
  if(getComputedStyle(document.querySelector('#sidebar')).display==='none'){document.body.classList.add('menu-open');menu?.setAttribute('aria-expanded','true');}
  search.focus();
});

// Reading progress: pages marked as read, and the last page opened.
const DONE='llm-textbook-done', LAST='llm-textbook-last';
function readDone(){try{const v=JSON.parse(store.get(DONE)||'[]');return new Set(Array.isArray(v)?v:[]);}catch{return new Set();}}
function writeDone(set){return store.set(DONE,JSON.stringify([...set]));}
function markLinks(){
  const done=readDone();
  document.querySelectorAll('#sidebar nav a, .part li a').forEach(a=>a.classList.toggle('is-done',done.has(slugOf(a.getAttribute('href')))));
}
const article=document.querySelector('article');
if(page!=='index'&&article){
  const heading=article.querySelector('h1')?.textContent.trim()||document.title;
  store.set(LAST,JSON.stringify({slug:page,title:heading}));
  const box=document.createElement('div');box.className='done-toggle';
  const button=document.createElement('button');button.type='button';
  const status=document.createElement('p');status.setAttribute('role','status');
  const show=()=>{const on=readDone().has(page);button.textContent=on?'✓ 読み終えた（取り消す）':'このページを読み終えた';button.setAttribute('aria-pressed',String(on));};
  button.addEventListener('click',()=>{const done=readDone();const on=!done.has(page);on?done.add(page):done.delete(page);
    status.textContent=writeDone(done)?(on?'印を付けました。目次に ✓ が表示されます。':'印を外しました。'):'保存できない設定です。紙やメモに記録してください。';show();markLinks();});
  show();box.append(button,status);
  const pager=article.querySelector('.pager');pager?pager.before(box):article.append(box);
}
markLinks();

const progress=document.querySelector('[data-progress]');
if(progress){
  const chapters=[...document.querySelectorAll('#curriculum .part li a')].map(a=>slugOf(a.getAttribute('href')));
  const render=()=>{
    const done=readDone();let last=null;try{last=JSON.parse(store.get(LAST)||'null');}catch{}
    progress.replaceChildren();
    const read=chapters.filter(s=>done.has(s)).length;
    if(!done.size&&!last){progress.hidden=true;return;}
    progress.hidden=false;
    const count=document.createElement('span');count.textContent=`講義 ${read} / ${chapters.length} を読了`;
    const bar=document.createElement('span');bar.className='progress-bar';bar.setAttribute('aria-hidden','true');bar.style.setProperty('--value',`${chapters.length?read/chapters.length*100:0}%`);
    progress.append(count,bar);
    if(last?.slug&&/^[\w-]+$/.test(last.slug)){const a=document.createElement('a');a.href=`${last.slug}.html`;a.textContent=`続きから：${last.title||last.slug}`;progress.append(a);}
    const clear=document.createElement('button');clear.type='button';clear.textContent='進み具合の記録を消す';
    clear.addEventListener('click',()=>{if(!confirm('読了の印と最後に開いたページの記録を、この端末から消します。メモは残ります。'))return;store.remove(DONE);store.remove(LAST);render();markLinks();});
    progress.append(clear);
  };
  render();
}

// Copy buttons for code blocks.
document.querySelectorAll('article pre > code').forEach(code=>{
  const pre=code.parentElement, button=document.createElement('button');
  button.type='button';button.className='copy-code';button.textContent='コピー';
  button.addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(code.textContent);button.textContent='コピーしました';}
    catch{const range=document.createRange();range.selectNodeContents(code);const sel=getSelection();sel.removeAllRanges();sel.addRange(range);button.textContent='選択しました。Ctrl+Cでコピー';}
    setTimeout(()=>{button.textContent='コピー';},2000);
  });
  const wrap=document.createElement('div');wrap.className='code-wrap';pre.before(wrap);wrap.append(pre,button);
});

// A thin bar under the header showing how far down the page you are.
if(article&&page!=='index'){
  const bar=document.createElement('div');bar.className='read-progress';bar.setAttribute('aria-hidden','true');document.body.append(bar);
  let ticking=false;
  const update=()=>{const max=document.documentElement.scrollHeight-innerHeight;bar.style.transform=`scaleX(${max>0?Math.min(1,scrollY/max):0})`;ticking=false;};
  addEventListener('scroll',()=>{if(!ticking){ticking=true;requestAnimationFrame(update);}},{passive:true});addEventListener('resize',update);update();
}
