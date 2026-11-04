import asyncio,sys,json,urllib.request
from playwright.async_api import async_playwright
K=open('tdkey.txt').read().strip(); BIN='https://textdb.dev/api/data/'+K
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        await ctx.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','tinder')")
        pg=await ctx.new_page(); pg.on("pageerror",lambda e:print("ERR",e))
        await pg.goto(sys.argv[1]); await pg.wait_for_selector('.card'); await pg.wait_for_timeout(1000)
        a=lambda: pg.locator('.card:not(.back) .a').inner_text()
        before=await a()
        d=json.load(urllib.request.urlopen(BIN+'?_=1'))
        d['items'].insert(0,dict(id='BOT1',mls='BOT1',addr='1 Bot Test St',zip='33701',price=300000,sqft=1000,lat=27.77,lon=-82.64,img='',by='Bot',status='queue',notes=[]))
        urllib.request.urlopen(urllib.request.Request(BIN,data=json.dumps(d).encode(),headers={'Content-Type':'text/plain'}))
        await pg.wait_for_timeout(14000)
        print("before",before,"after 14s",await a(),"count",await pg.evaluate("document.querySelector('#nQ').textContent"))
        await pg.click('#bNo'); await pg.wait_for_timeout(1200)
        print("next card (should be Bot):",await a()); await pg.screenshot(path="s_bot_card.png")
        await pg.click('#bNo'); await pg.wait_for_timeout(1000); await pg.click('#bNo'); await pg.wait_for_timeout(1000); await pg.click('#bNo'); await pg.wait_for_timeout(1000)
        await pg.click('#burger'); await pg.click('[data-v=discard]'); await pg.wait_for_timeout(1500)
        print("disc before",await pg.locator('.item .addr').all_inner_texts())
        bb=await pg.locator('.item:last-child .handle').bounding_box(); t=await pg.locator('.item:first-child').bounding_box()
        x=bb['x']+bb['width']/2; y=bb['y']+bb['height']/2
        await pg.mouse.move(x,y); await pg.mouse.down()
        for i in range(1,21): await pg.mouse.move(x,y-(y-t['y']-10)*i/20); await pg.wait_for_timeout(30)
        await pg.mouse.up(); await pg.wait_for_timeout(3500)
        print("disc after ",await pg.locator('.item .addr').all_inner_texts())
        await pg.screenshot(path="s_thumbs_disc.png")
        await b.close()
asyncio.run(main())
