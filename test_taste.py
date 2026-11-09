# Mocked test: textdb.dev is intercepted; nothing is written to the real store.
import asyncio,sys,json,urllib.request,glob
from playwright.async_api import async_playwright
KEY=open('tdkey.txt').read().strip(); BIN='https://textdb.dev/api/data/'+KEY
URL=sys.argv[1]; TAG=sys.argv[2]
bk=sorted(glob.glob('/workspace/stpete-backups/backup-*-pretaste.json'))[-1]
main=open(bk).read()   # mock copy of the main data (from backup file, not the live key)
store={'main':main,'taste':''}; posts=[]
async def handle(route):
    r=route.request; u=r.url.split('?')[0]; k='taste' if u.endswith('-taste') else ('main' if u.endswith(KEY) else None)
    h={'access-control-allow-origin':'*','content-type':'text/plain'}
    if k is None: return await route.fulfill(status=404,body='',headers=h)
    if r.method=='GET': return await route.fulfill(status=200,body=store[k],headers=h)
    if r.method=='POST': posts.append((k,r.post_data)); store[k]=r.post_data; return await route.fulfill(status=200,body='ok',headers=h)
    return await route.fulfill(status=200,body='',headers=h)
async def main_():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        await ctx.route('**/textdb.dev/**',handle)
        await ctx.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','list')")
        pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:(errs.append(str(e)),print("ERR",e)))
        await pg.goto(URL); await pg.wait_for_selector('.item'); await pg.wait_for_timeout(800)
        await pg.click('#burger'); await pg.screenshot(path=f"/workspace/shots/{TAG}_menu.png"); await pg.click('[data-v=taste]'); await pg.wait_for_selector('.pc'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"/workspace/shots/{TAG}_game.png")
        # play: love warm/ranch/bigyard, nope cool/new
        duels=0
        for i in range(40):
            if await pg.locator('#styleM.show').count():
                await pg.screenshot(path=f"/workspace/shots/{TAG}_stylecard.png"); await pg.click('[data-close-style]'); await pg.wait_for_timeout(200)
            if await pg.locator('.duel').count():
                if duels==0: await pg.screenshot(path=f"/workspace/shots/{TAG}_duel.png")
                duels+=1; await pg.click('[data-pick=a]'); await pg.wait_for_timeout(450); continue
            pid=await pg.get_attribute('.pc:not(.back)','data-p')
            t=await pg.evaluate("id=>fetch('taste.json?v=1').then(r=>r.json()).then(j=>j.photos.find(p=>p.id===id).tags)",pid)
            like=(t.get('warmth')=='warm' or t.get('ext') in ('ranch','mcm') or t.get('yard')=='big') and t.get('warmth')!='cool' and t.get('ext')!='new'
            if i==3:  # real swipe gesture
                bb=await pg.locator('.pc:not(.back)').bounding_box(); x,y=bb['x']+bb['width']/2,bb['y']+bb['height']/2
                await pg.mouse.move(x,y); await pg.mouse.down(); await pg.mouse.move(x+(160 if like else -160),y,steps=8); await pg.mouse.up()
            else: await pg.click('[data-sw="%d"]'%(1 if like else -1))
            await pg.wait_for_timeout(300)
        await pg.screenshot(path=f"/workspace/shots/{TAG}_game_later.png")
        await pg.click('[data-tab=style]'); await pg.wait_for_timeout(300); await pg.screenshot(path=f"/workspace/shots/{TAG}_style.png",full_page=False)
        await pg.click('[data-tab=match]'); await pg.wait_for_timeout(1200); await pg.screenshot(path=f"/workspace/shots/{TAG}_matches.png")
        await pg.wait_for_timeout(2000)
        mainposts=[x for x in posts if x[0]=='main']; print('main posts before add:',len(mainposts),'taste posts:',len([x for x in posts if x[0]=='taste']),'duels',duels)
        btn=pg.locator('[data-add]').first
        if await btn.count():
            mls=await btn.get_attribute('data-add'); await btn.click(); await pg.wait_for_timeout(1500)
            mainposts=[x for x in posts if x[0]=='main']; print('main posts after add:',len(mainposts))
            new=json.loads(mainposts[-1][1]); old=json.loads(main)
            print('prepended:',new['items'][0]['mls']==mls, new['items'][0]['by'], new['items'][0]['status'], 'rest identical:', new['items'][1:]==old['items'], len(new['items']),len(old['items']))
            await pg.screenshot(path=f"/workspace/shots/{TAG}_matches_added.png")
        td=json.loads(store['taste']); print('taste doc people:',list(td['people']), 'swipes',len(td['people']['Tom']['swipes']),'duels',len(td['people']['Tom']['duels'])); print('top scores',sorted(td['scores']['Tom'].items(),key=lambda x:-x[1])[:5],sorted(td['scores']['Tom'].items(),key=lambda x:x[1])[:3])
        # reload: state persists & no main write on load
        n0=len([x for x in posts if x[0]=='main']); await pg.reload(); await pg.wait_for_timeout(3000); print('main posts on reload:',len([x for x in posts if x[0]=='main'])-n0)
        print('errors',errs); await b.close()
asyncio.run(main_())
