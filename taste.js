// ---- Taste game: photo swipes -> learned style -> best matches ----
// Stores ONLY in a separate textdb key (BIN+'-taste') + localStorage. The main shared
// data (BIN) is written only by the explicit "Add to Realtinder" tap, via mutate().
(function(){
const TBIN=BIN+'-taste', UNLOCK=15, DUEL_EVERY=7;
const LBL={'warmth:warm':'warm wood','warmth:cool':'white / grey finishes','style:modern':'modern','style:traditional':'classic / traditional','open':'open layouts','closed':'separate rooms',
 'ext:ranch':'block ranch exteriors','ext:new':'new builds','ext:bung':'bungalows / cottages','ext:mcm':'mid-century','pool':'pools','yard:big':'big yards','yard:small':'small yards','garage':'garages'};
const ROOM={ext:'Exterior',entry:'Entry',kit:'Kitchen',liv:'Living room',din:'Dining',bed:'Bedroom',bath:'Bathroom',pool:'Pool',yard:'Yard',garage:'Garage'};
let T=null, P=[], byId={}, tab=localStorage.getItem('tTab')||'play', cur=null, duel=null, tSw=false, tFl=false, saving=Promise.resolve(), dirty=false, shownCard=false;
let doc=null; // {v:1, people:{Tom:{swipes:[{p,d,ts}],duels:[{w,l,ts}]}}, scores:{Tom:{f:[pos,neg]}}, updated}
const who=()=>me||'Tom';
function mine(){ doc.people=doc.people||{}; return doc.people[who()]=doc.people[who()]||{swipes:[],duels:[]}; }
function feats(t){ const f=[]; if(!t)return f; if(t.warmth)f.push('warmth:'+t.warmth); if(t.style)f.push('style:'+t.style); if(t.open===true)f.push('open'); if(t.open===false)f.push('closed');
  if(t.ext)f.push('ext:'+t.ext); if(t.pool)f.push('pool'); if(t.yard)f.push('yard:'+t.yard); if(t.garage)f.push('garage'); if(t.hood)f.push('hood:'+t.hood); return f; }
function label(f){ return LBL[f]||(f.startsWith('hood:')?f.slice(5):f); }
// ---- learning ----
function counts(){ const c={}, add=(f,k,w)=>{ (c[f]=c[f]||[0,0])[k]+=w; }; const m=mine();
  for(const s of m.swipes){ const p=byId[s.p]; if(!p)continue; for(const f of feats(p.tags)) add(f,s.d>0?0:1,1); }
  for(const d of m.duels){ const a=byId[d.w], b=byId[d.l]; if(!a||!b)continue; const fa=feats(a.tags), fb=feats(b.tags);
    for(const f of fa) if(!fb.includes(f)) add(f,0,1.5); for(const f of fb) if(!fa.includes(f)) add(f,1,1.5); }
  return c; }
function scoresOf(c){ const s={}; for(const f in c){ const [p,n]=c[f]; s[f]={s:(p-n)/(p+n+2),n:p+n,pos:p,neg:n}; } return s; }
function profile(){ const s=scoresOf(counts()); const arr=Object.entries(s).filter(([f,v])=>v.n>=2);
  const likes=arr.filter(([f,v])=>v.s>=0.2).sort((a,b)=>b[1].s-a[1].s), nopes=arr.filter(([f,v])=>v.s<=-0.2).sort((a,b)=>a[1].s-b[1].s);
  // don't list both sides of a pair as likes
  return {s,likes,nopes}; }
function nSw(){ const m=mine(); return m.swipes.length+m.duels.length; }
// ---- home matching ----
const hoodOf=(lat,lon,zip)=>{ if(lat==null)return null; if(lat>=27.773)return 'North St. Pete'; if(lat>=27.745)return lon>-82.645?'Old Southeast / Downtown':(lon>-82.675?'Midtown / Central':'West / Childs Park');
  if(lon<-82.685)return 'West / Childs Park'; if(lat<27.7125)return 'Pinellas Point / Skyway'; if(lon>-82.645)return lon>-82.632?'Bahama Shores / Coquina Key':'South St. Pete (east)'; return 'Lakewood / South St. Pete'; };
function homes(){ const out=[], seen=new Set();
  for(const it of state.items){ const k=st(it); if(k==='discard')continue; seen.add(it.mls); out.push({it,kind:k}); }
  for(const e of (T.extra||[])) if(!seen.has(e.mls)){ seen.add(e.mls); out.push({it:e,kind:'extra'}); }
  return out; }
function scoreHome(it,S){ const ph=P.filter(p=>p.mls===it.mls); const contrib={}; let tot=0,w=0;
  const use=(f,wt)=>{ const v=S[f]; if(!v)return; const x=v.s*Math.min(1,v.n/3)*wt; contrib[f]=(contrib[f]||0)+x; tot+=x; };
  for(const p of ph){ for(const f of feats(p.tags)) if(!f.startsWith('hood:')) use(f,1/ph.length*2); }
  const h=ph[0]?ph[0].tags.hood:hoodOf(it.lat,it.lon,it.zip); if(h)use('hood:'+h,1);
  const why=Object.entries(contrib).filter(([f,x])=>x>0.05).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([f])=>label(f));
  const neg=Object.entries(contrib).filter(([f,x])=>x<-0.05).sort((a,b)=>a[1]-b[1]).slice(0,1).map(([f])=>label(f));
  const pct=Math.round(50+50*Math.tanh(tot/3)); return {pct,why,neg,photos:ph.length}; }
// ---- storage (separate key only) ----
async function tPull(){ const r=await fetch(TBIN+'?_='+Date.now(),{cache:'no-store'}); if(!r.ok)throw 0; const t=(await r.text()).trim(); if(!t)return {v:1,people:{}}; const o=JSON.parse(t); if(!o||typeof o!=='object')throw 0; o.people=o.people||{}; return o; }
function merge(a,b){ // union of b into a (swipes/duels keyed by ts+p)
  for(const who in (b.people||{})){ const A=a.people[who]=a.people[who]||{swipes:[],duels:[]}, B=b.people[who];
    const ks=new Set(A.swipes.map(s=>s.ts+'|'+s.p)); for(const s of B.swipes||[]) if(!ks.has(s.ts+'|'+s.p)) A.swipes.push(s);
    const kd=new Set(A.duels.map(s=>s.ts+'|'+s.w)); for(const s of B.duels||[]) if(!kd.has(s.ts+'|'+s.w)) A.duels.push(s);
    const un=new Set([...(A.undone||[]),...(B.undone||[])]); A.undone=[...un]; A.swipes=A.swipes.filter(s=>!un.has(s.ts)).sort((x,y)=>x.ts-y.ts); A.duels=A.duels.filter(s=>!un.has(s.ts)).sort((x,y)=>x.ts-y.ts); }
  return a; }
function saveLocal(){ localStorage.setItem('taste',JSON.stringify(doc)); }
function tPush(){ dirty=true; saveLocal(); clearTimeout(tPush.t); tPush.t=setTimeout(()=>{ saving=saving.then(async()=>{ if(!dirty)return; dirty=false;
  try{ const remote=await tPull(); const m=merge(remote,doc); const sc={}; const keep=doc; for(const w in m.people){ doc=m; const save=me; me=w; sc[w]=Object.fromEntries(Object.entries(scoresOf(counts())).map(([f,v])=>[f,Math.round(v.s*100)/100])); me=save; } doc=keep;
    m.scores=sc; m.v=1; m.updated=Date.now(); m.about='Taste game swipes. scores[person][feature] in -1..1 (feature names: warmth:warm|cool, style:modern|traditional, open|closed, ext:ranch|new|bung|mcm, pool, yard:big|small, garage, hood:<name>). Photos/tags: taste.json in the repo.';
    const r=await fetch(TBIN,{method:'POST',headers:{'Content-Type':'text/plain'},body:JSON.stringify(m)}); if(!r.ok)throw 0; doc=merge(m,doc); saveLocal(); }catch(e){ dirty=true; } }); },1200); }
async function tSync(){ try{ const r=await tPull(); const rj=JSON.stringify(r.people); doc=merge(r,doc); saveLocal(); return JSON.stringify(doc.people)!==rj; }catch(e){ return false; } }
// ---- deck ----
function seenSet(){ const m=mine(), s=new Set(m.swipes.map(x=>x.p)); for(const d of m.duels){ s.add(d.w); s.add(d.l); } return s; }
function shuffle(a,seed){ let x=seed||1; const r=()=>(x=(x*16807)%2147483647)/2147483647; for(let i=a.length-1;i>0;i--){ const j=Math.floor(r()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }
let order=[];
function buildOrder(){ // interleave rooms so it doesn't feel like 10 fronts in a row
  const g={}; for(const p of shuffle(P.slice(),(Number(localStorage.getItem('tSeed'))||7))){ const k=p.tags.room==='ext'?'ext':'in'; (g[k]=g[k]||[]).push(p); }
  order=[]; const e=g.ext||[], i=g.in||[]; while(e.length||i.length){ if(i.length)order.push(i.shift()); if(e.length)order.push(e.shift()); if(e.length)order.push(e.shift()); } }
function nextPhoto(){ const s=seenSet(); return order.find(p=>!s.has(p.id)&&(!cur||p.id!==cur.id)); }
const PAIRS=[['warmth:warm','warmth:cool'],['style:modern','style:traditional'],['ext:ranch','ext:new'],['ext:ranch','ext:bung'],['ext:mcm','ext:new'],['yard:big','yard:small'],['ext:new','ext:bung']];
function pickDuel(){ const m=mine(), k=m.duels.length; for(let t=0;t<PAIRS.length;t++){ const [fa,fb]=PAIRS[(k+t)%PAIRS.length];
   const room=fa.startsWith('warmth')||fa.startsWith('style')?null:'ext';
   const cand=f=>P.filter(p=>feats(p.tags).includes(f)&&(!room||p.tags.room===room)&&!m.duels.some(d=>d.w===p.id||d.l===p.id));
   let A=cand(fa), B=cand(fb); if(fa.startsWith('warmth')){ const rm=['kit','liv'][k%2]; const A2=A.filter(p=>p.tags.room===rm), B2=B.filter(p=>p.tags.room===rm); if(A2.length&&B2.length){A=A2;B=B2} }
   if(A.length&&B.length){ const a=A[(k*7)%A.length], b=B[(k*5)%B.length]; return Math.random()<.5?{a,b,q:fa}:{a:b,b:a,q:fa}; } } return null; }
// ---- render ----
function el(){ return document.getElementById('taste'); }
function progressHtml(){ const n=nSw(), tot=P.length+Math.floor(P.length/DUEL_EVERY); const goals=[UNLOCK,40,80,tot]; const g=goals.find(x=>x>n)||tot; const prev=[0,...goals].filter(x=>x<=n).pop()||0;
  const lab=n<UNLOCK?(UNLOCK-n)+' more to unlock your style':g===tot?n+' / '+tot+' · nearly done':n+' swiped · next level at '+g;
  return '<div class="tprog"><span>Lv '+(goals.filter(x=>x<=n).length+1)+'</span><div class="tb"><i style="width:'+Math.min(100,Math.round(100*(n-prev)/Math.max(1,g-prev)))+'%"></i></div><span>'+lab+'</span></div>'; }
function styleLine(){ const n=nSw(); if(n<UNLOCK)return '<div class="tstyle">&#129449; Your style unlocks after '+UNLOCK+' swipes</div>';
  const {likes,nopes}=profile(); const l=likes.slice(0,3).map(([f])=>label(f)).join(', ')||'still learning…'; const no=nopes.slice(0,2).map(([f])=>label(f)).join(', ');
  return '<div class="tstyle" data-style>&#129449; <b>Your style:</b> '+esc(l)+(no?' &middot; not '+esc(no):'')+'</div>'; }
function tabsHtml(){ const b=(k,t)=>'<button data-tab="'+k+'" class="'+(tab===k?'on':'')+'">'+t+'</button>'; return '<div class="tabs">'+b('play','Play')+b('style','Your style')+b('match','Best matches')+'</div>'; }
function render(){ const E=el(); if(!E)return; if(!P.length){ E.innerHTML=tabsHtml()+'<div class="empty">Loading photos…</div>'; return; }
  if(tab==='play')renderPlay(E); else if(tab==='style')E.innerHTML=tabsHtml()+'<div class="tscroll">'+styleCard(false)+'</div>'; else renderMatches(E); }
function renderPlay(E){ const n=nSw();
  if(!duel&&n>0&&n%DUEL_EVERY===0&&mine().swipes.length&&!mine().duels.some(d=>d.n===n)) duel=pickDuel();
  if(duel){ duel.n=n; E.innerHTML=tabsHtml()+progressHtml()+styleLine()+'<div class="duel"><h3>This or that?<small>Tap the one you&#39;d rather live with</small></h3><button data-pick="a" style="background-image:url(\''+esc(duel.a.url)+'\')"></button><div class="or">OR</div><button data-pick="b" style="background-image:url(\''+esc(duel.b.url)+'\')"></button></div>'; return; }
  cur=cur&&!seenSet().has(cur.id)?cur:nextPhoto();
  if(!cur){ E.innerHTML=tabsHtml()+progressHtml()+styleLine()+'<div class="empty" style="margin:auto">You swiped every photo! &#127881;<br><br><button class="btn" data-tab="match">See your best matches</button><br><br><span class="lbl">New photos get added as new listings come in.</span></div>'; return; }
  const nx=order.find(p=>p!==cur&&!seenSet().has(p.id)); const cap=p=>(ROOM[p.tags.room]||'Photo')+(p.tags.hood?' · '+p.tags.hood:'');
  E.innerHTML=tabsHtml()+progressHtml()+styleLine()+'<div class="tdeck">'+(nx?'<div class="pc back" style="background-image:url(\''+esc(nx.url)+'\')"></div>':'')+'<div class="pc" data-p="'+cur.id+'" style="background-image:url(\''+esc(cur.url)+'\')"><div class="stamp k">LOVE</div><div class="stamp l">NOPE</div><div class="cap">'+esc(cap(cur))+'</div></div></div>'+
   '<div class="tacts"><button class="no" data-sw="-1" aria-label="Nope">&#10005;</button><button class="un" data-undo aria-label="Undo"'+(mine().swipes.length?'':' disabled')+'>&#8630;</button><button class="yes" data-sw="1" aria-label="Love it">&#9829;</button></div>';
  const order2=order.filter(p=>!seenSet().has(p.id)).slice(1,4); for(const p of order2){ const i=new Image(); i.referrerPolicy='no-referrer'; i.src=p.url; }
  attach(E.querySelector('.pc:not(.back)')); }
function styleCard(popup){ const n=nSw(); if(n<UNLOCK)return '<div class="scard"><h2>Your style</h2><div class="lbl">Swipe '+(UNLOCK-n)+' more photos and I&#39;ll show what you like.</div></div>';
  const {s,likes,nopes}=profile(); const chips=(a,c)=>a.map(([f])=>'<span class="chip '+c+'">'+esc(label(f))+'</span>').join('')||'<span class="lbl">Nothing clear yet</span>';
  const rows=Object.entries(s).filter(([f,v])=>v.n>=2).sort((a,b)=>b[1].s-a[1].s).map(([f,v])=>{ const w=Math.round(Math.abs(v.s)*50); return '<div class="sbar"><span>'+esc(label(f))+'</span><div class="t"><i style="'+(v.s>=0?'left:50%;width:'+w+'%;background:#ec4899':'right:50%;width:'+w+'%;background:#9aa8b3')+'"></i></div></div>'; }).join('');
  const m=mine(); const loved=m.swipes.filter(x=>x.d>0).length;
  return '<div class="scard"><h2>&#129449; Your style</h2><div class="lbl" style="margin-top:0">From '+n+' picks ('+loved+' loves)</div><div class="lbl">You love</div>'+chips(likes.slice(0,6),'y')+'<div class="lbl">Not your thing</div>'+chips(nopes.slice(0,5),'n')+
   (popup?'<div class="row" style="margin-top:12px"><button class="btn g" data-close-style style="flex:1">Keep playing</button><button class="btn" data-tab="match" style="flex:1.3;background:#ec4899">Best matches</button></div>':'<details class="dt" open><summary>All features (pink = like, grey = nope)</summary>'+rows+'</details>')+'</div>'; }
function renderMatches(E){ const S=profile().s; const n=nSw();
  if(n<UNLOCK){ E.innerHTML=tabsHtml()+'<div class="tscroll"><div class="scard"><h2>Best matches</h2><div class="lbl">Swipe '+(UNLOCK-n)+' more photos to unlock your matches.</div><button class="btn" data-tab="play" style="background:#ec4899">Play</button></div></div>'; return; }
  const H=homes().map(h=>({...h,sc:scoreHome(h.it,S)})).sort((a,b)=>b.sc.pct-a.sc.pct).slice(0,20);
  const listRank=id=>state.items.filter(i=>st(i)==='list').findIndex(i=>i.id===id)+1;
  E.innerHTML=tabsHtml()+'<div class="tscroll"><div class="lbl" style="margin:2px 2px 8px">Your List, Realtinder queue and '+(T.extra||[]).length+' other active listings, ranked by your style.</div>'+H.map((h,i)=>{ const it=h.it, mi=miles(it.lat,it.lon);
   const btn=h.kind==='extra'?'<button class="tadd" data-add="'+esc(it.mls)+'"><b>+</b>Add to Realtinder</button>':h.kind==='queue'?'<button class="tadd" disabled>In Realtinder</button>':'<button class="tadd" disabled>List #'+listRank(it.id)+'</button>';
   return '<div class="item"><div class="bar"><div class="rank">'+(i+1)+'</div><div class="thumb">'+(it.img?'<img src="'+esc(it.img)+'" loading="lazy" referrerpolicy="no-referrer" alt="" onerror="this.remove()">':'&#127968;')+'</div><div class="main"><div class="addr"><span class="mt">'+h.sc.pct+'%</span>'+esc(it.addr||'Address not added')+'</div><div class="meta"><a href="'+zurl(it)+'" target="_blank" rel="noopener">'+esc(it.mls)+'</a>&thinsp;·&thinsp;<b>'+money(it.price)+'</b>'+(psfTxt(it)?'&thinsp;·&thinsp;'+psfTxt(it):'')+'&thinsp;·&thinsp;'+(mi==null?'? mi':mi.toFixed(1)+' mi')+'</div><div class="why">'+(h.sc.why.length?'&#9829; '+esc(h.sc.why.join(', ')):'')+(h.sc.neg.length?' &middot; &#10005; '+esc(h.sc.neg.join(', ')):'')+(h.sc.photos?'':' (location only)')+'</div></div>'+btn+'</div></div>'; }).join('')+'</div>'; }
// ---- actions ----
function record(id,d){ const m=mine(); m.swipes.push({p:id,d,ts:Date.now()}); cur=null; tPush(); afterPick(); }
function afterPick(){ const n=nSw(); render(); if(n===UNLOCK&&!shownCard){ shownCard=true; openStyle(); } $('#nT')&&($('#nT').textContent=n||''); }
function openStyle(){ const M=$('#styleM'); M.querySelector('.sheet').innerHTML=styleCard(true); M.classList.add('show'); }
function fl(E,d){ if(tFl)return; tFl=true; const id=E.dataset.p; E.style.transition='transform .25s ease-out,opacity .25s'; E.style.transform='translateX('+(d*innerWidth*1.2)+'px) rotate('+(d*22)+'deg)'; E.style.opacity='.2'; setTimeout(()=>{ tFl=false; record(id,d); },230); }
function attach(E){ if(!E)return; let sx=0,dx=0,on=false; const k=E.querySelector('.stamp.k'), l=E.querySelector('.stamp.l');
  E.addEventListener('pointerdown',e=>{ on=true; tSw=true; sx=e.clientX; dx=0; E.style.transition='none'; E.setPointerCapture(e.pointerId); });
  E.addEventListener('pointermove',e=>{ if(!on)return; dx=e.clientX-sx; E.style.transform='translateX('+dx+'px) rotate('+(dx/18)+'deg)'; k.style.opacity=Math.max(0,Math.min(1,dx/90)); l.style.opacity=Math.max(0,Math.min(1,-dx/90)); });
  const end=()=>{ if(!on)return; on=false; tSw=false; if(Math.abs(dx)>90) fl(E,dx>0?1:-1); else { E.style.transition='transform .2s'; E.style.transform=''; k.style.opacity=0; l.style.opacity=0; } };
  E.addEventListener('pointerup',end); E.addEventListener('pointercancel',end); }
async function addToRealtinder(mls,btn){ const e=(T.extra||[]).find(x=>x.mls===mls); if(!e)return; if(state.items.some(x=>x.mls===mls)){ toast('Already in your app'); return; }
  const sc=scoreHome(e,profile().s); btn.disabled=true; btn.innerHTML='Added';
  const it={id:e.mls,mls:e.mls,addr:e.addr,zip:e.zip,price:e.price||null,sqft:e.sqft||null,lat:e.lat,lon:e.lon,img:e.img||'',by:'Bot',status:'queue',notes:[{by:'Bot',text:'Taste game match '+sc.pct+'%'+(sc.why.length?': '+sc.why.join(', '):''),ts:Date.now()}]};
  curId=null; await mutate(s=>{ if(!s.items.some(x=>x.mls===it.mls)) s.items.unshift(it); }); toast('Added to the front of Realtinder'); render(); }
document.addEventListener('click',e=>{ const t=e.target; if(!t.closest('#taste')&&!t.closest('#styleM'))return;
  const tb=t.closest('[data-tab]'); if(tb){ tab=tb.dataset.tab; localStorage.setItem('tTab',tab); $('#styleM').classList.remove('show'); render(); return; }
  if(t.closest('[data-close-style]')||t.id==='styleM'){ $('#styleM').classList.remove('show'); return; }
  if(t.closest('[data-style]')){ openStyle(); return; }
  const sw=t.closest('[data-sw]'); if(sw){ const E=el().querySelector('.pc:not(.back)'); if(E)fl(E,+sw.dataset.sw); return; }
  if(t.closest('[data-undo]')){ const m=mine(); const last=m.swipes.pop(); if(last){ (m.undone=m.undone||[]).push(last.ts); cur=byId[last.p]; duel=null; tPush(); render(); } return; }
  const pk=t.closest('[data-pick]'); if(pk&&duel){ pk.classList.add('win'); const w=pk.dataset.pick==='a'?duel.a:duel.b, l=pk.dataset.pick==='a'?duel.b:duel.a; const n=duel.n; mine().duels.push({w:w.id,l:l.id,ts:Date.now(),n}); duel=null; tPush(); setTimeout(afterPick,250); return; }
  const ad=t.closest('[data-add]'); if(ad){ addToRealtinder(ad.dataset.add,ad); return; } });
document.getElementById('styleM').addEventListener('click',e=>{ if(e.target.id==='styleM')e.target.classList.remove('show'); });
window.tasteOnData=function(){ if(tSw||tFl)return; if(tab==='match'||!el().innerHTML)render(); };
// ---- boot ----
try{ doc=JSON.parse(localStorage.getItem('taste')||'null'); }catch(e){} if(!doc||!doc.people)doc={v:1,people:{}};
fetch('taste.json?v=1').then(r=>r.json()).then(async j=>{ T=j; P=j.photos; byId=Object.fromEntries(P.map(p=>[p.id,p])); buildOrder(); if(await tSync())tPush(); shownCard=nSw()>=UNLOCK; $('#nT').textContent=nSw()||''; if(view==='taste')render(); });
document.addEventListener('visibilitychange',()=>{ if(document.hidden&&dirty){ clearTimeout(tPush.t); tPush(); } if(!document.hidden&&view==='taste'&&tab!=='play')tSync().then(render); });
})();
