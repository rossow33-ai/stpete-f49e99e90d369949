#!/usr/bin/env python3
"""Read-only: GET the taste key (tdkey.txt + '-taste') and write taste-summary.md.
Never writes to textdb. Usage: python3 taste_summary.py [person=Tom]"""
import json,sys,urllib.request,time,collections
who=sys.argv[1] if len(sys.argv)>1 else 'Tom'
KEY=open('tdkey.txt').read().strip()+'-taste'
raw=urllib.request.urlopen(f'https://textdb.dev/api/data/{KEY}?_={int(time.time())}').read().decode().strip()
doc=json.loads(raw) if raw else {'people':{}}
T=json.load(open('taste.json')); P={p['id']:p for p in T['photos']}
LBL={'warmth:warm':'warm wood','warmth:cool':'white / grey finishes','style:modern':'modern','style:traditional':'classic / traditional','open':'open layouts','closed':'separate rooms','ext:ranch':'block ranch exteriors','ext:new':'new builds','ext:bung':'bungalows / cottages','ext:mcm':'mid-century','pool':'pools','yard:big':'big yards','yard:small':'small yards','garage':'garages'}
lab=lambda f:LBL.get(f,f[5:] if f.startswith('hood:') else f)
def feats(t):
    f=[]
    if t.get('warmth'):f.append('warmth:'+t['warmth'])
    if t.get('style'):f.append('style:'+t['style'])
    if t.get('open') is True:f.append('open')
    if t.get('open') is False:f.append('closed')
    if t.get('ext'):f.append('ext:'+t['ext'])
    if t.get('pool'):f.append('pool')
    if t.get('yard'):f.append('yard:'+t['yard'])
    if t.get('garage'):f.append('garage')
    if t.get('hood'):f.append('hood:'+t['hood'])
    return f
m=doc.get('people',{}).get(who,{'swipes':[],'duels':[]})
c=collections.defaultdict(lambda:[0.0,0.0])
for s in m.get('swipes',[]):
    p=P.get(s['p'])
    if p:
        for f in feats(p['tags']): c[f][0 if s['d']>0 else 1]+=1
for d in m.get('duels',[]):
    a,b=P.get(d['w']),P.get(d['l'])
    if a and b:
        fa,fb=feats(a['tags']),feats(b['tags'])
        for f in fa:
            if f not in fb: c[f][0]+=1.5
        for f in fb:
            if f not in fa: c[f][1]+=1.5
S={f:((p-n)/(p+n+2),p+n) for f,(p,n) in c.items()}
rows=sorted([(f,s,n) for f,(s,n) in S.items() if n>=2],key=lambda x:-x[1])
loves=[r for r in rows if r[1]>=0.2]; nopes=[r for r in rows if r[1]<=-0.2][::-1]
out=[f"# {who}'s house taste (from the Taste game)",'',f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} from {len(m.get('swipes',[]))} photo swipes and {len(m.get('duels',[]))} this-or-that picks ({sum(1 for s in m.get('swipes',[]) if s['d']>0)} loves).",'']
if not rows: out.append('_No swipes yet. Play the Taste game in the app (≡ → Taste game) and re-run `python3 taste_summary.py`._')
else:
    out+=['**Loves:** '+(', '.join(lab(f) for f,_,_ in loves) or '—'),'','**Not into:** '+(', '.join(lab(f) for f,_,_ in nopes) or '—'),'','| feature | score (-1..1) | picks |','|---|---|---|']
    out+=[f"| {lab(f)} | {s:+.2f} | {n:g} |" for f,s,n in rows]
open('taste-summary.md','w').write('\n'.join(out)+'\n'); print('\n'.join(out))
