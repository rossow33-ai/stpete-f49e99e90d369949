import asyncio,sys,json,urllib.request
from playwright.async_api import async_playwright
BIN='https://textdb.dev/api/data/'+open('tdkey.txt').read().strip()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        # use a route-mocked data copy so shared data is NOT touched
        d=json.load(urllib.request.urlopen(BIN+'?_=2'))
        for k,it in enumerate(d['items']): it['status']='list' if k<9 else 'discard'
        d['items'][0]['notes'].append(dict(by='Realtor',text='Showing is Saturday at 11, lockbox code in MLS remarks, bring shoe covers',ts=1762400000000))
        d['items'][2]['by']='Bot'; d['items'][2]['notes']=[]
        body=json.dumps(d)
        await ctx.route('**/textdb.dev/**',lambda r: r.fulfill(status=200,body=body,headers={'access-control-allow-origin':'*','content-type':'text/plain'}) if r.request.method=='GET' else r.fulfill(status=200,body='ok',headers={'access-control-allow-origin':'*'}))
        await ctx.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','list')")
        pg=await ctx.new_page(); pg.on("pageerror",lambda e:print("ERR",e))
        await pg.goto(sys.argv[1]); await pg.wait_for_selector('.item'); await pg.wait_for_timeout(1500)
        print("bar heights",[round((await x.bounding_box())['height']) for x in await pg.locator('.item').all()][:3])
        await pg.screenshot(path="/workspace/shots/s_list_notes.png")
        await pg.click('#burger'); await pg.click('[data-v=discard]'); await pg.wait_for_timeout(1000); await pg.screenshot(path="/workspace/shots/s_disc_notes.png")
        await b.close()
asyncio.run(main())
