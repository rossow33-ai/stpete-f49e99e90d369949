import json,re,subprocess,urllib.parse,sys
def z(addr,zip_):
    a=re.sub(r'\s+','-',re.sub(r'[^A-Za-z0-9 ]','',f"{addr} Saint Petersburg FL {zip_}").strip())
    return f"https://www.zillow.com/homes/{a}_rb/"
def info(addr,zip_):
    u="https://r.jina.ai/"+z(addr,zip_)
    for t in range(2):
        try:
            txt=subprocess.run(['curl','-s','-m','45',u],capture_output=True,text=True).stdout
        except Exception: continue
        m=re.search(r'1st image of [^\]]*\]\((https://photos\.zillowstatic\.com/[^)\s]+)\)',txt) or re.search(r'image of [^\]]*\]\((https://photos\.zillowstatic\.com/fp/[^)\s]+?(?:cc_ft|p_e|uncropped)[^)\s]*)\)',txt)
        mls=re.search(r'MLS#:\s*([A-Z]*\d+)',txt); pr=re.search(r'^\$([\d,]+)\s*$',txt,re.M)
        if m: return dict(img=m.group(1),mls=mls and mls.group(1),price=pr and int(pr.group(1).replace(',','')),ok=True)
    return dict(ok=False)
if __name__=="__main__":
    g=json.load(open('geo.json')); out={}
    for x in g:
        r=info(x['addr'],x['zip']); out[x['mls']]=r; print(x['mls'],x['addr'],r)
    for a,zp in [("4946 Dr M L King Jr St S","33705")]:
        r=info(a,zp); out['MLK']=r; print(a,r)
    json.dump(out,open('photos.json','w'),indent=1)
