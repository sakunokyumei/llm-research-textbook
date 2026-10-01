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
