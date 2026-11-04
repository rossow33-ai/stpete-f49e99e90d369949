import asyncio,sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        pg=await ctx.new_page(); pg.on("pageerror",lambda e:print("ERR",e))
        await ctx.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','tinder')")
        await pg.goto(sys.argv[1]); await pg.wait_for_selector('.card'); await pg.wait_for_timeout(1500)
        print("queue",await pg.locator('#nQ').inner_text() if False else await pg.evaluate("document.querySelector('#nQ').textContent"), await pg.evaluate("[document.querySelector('#nList').textContent,document.querySelector('#nDis').textContent]"))
        await pg.screenshot(path="s_q.png")
        for i in range(3):
            await pg.click('#bYes'); await pg.wait_for_timeout(900)
        for i in range(3):
            await pg.click('#bNo'); await pg.wait_for_timeout(900)
        await pg.click('#burger'); await pg.click('[data-v=list]'); await pg.wait_for_timeout(1500)
        print("thumbs",await pg.locator('.thumb img').count(),"of",await pg.locator('.item').count(),"bar h",(await pg.locator('.bar').first.bounding_box())['height'])
        await pg.screenshot(path="s_thumbs.png")
        await pg.click('#burger'); await pg.click('[data-v=discard]'); await pg.wait_for_timeout(1500); await pg.screenshot(path="s_thumbs_disc.png")
        first=await pg.locator('.item .addr').all_inner_texts(); print("disc before",first)
        h=pg.locator('.item:last-child .handle'); bb=await h.bounding_box(); t=await pg.locator('.item:first-child').bounding_box()
        await pg.mouse.move(bb['x']+20,bb['y']+20); await pg.mouse.down()
        for i in range(1,21): await pg.mouse.move(bb['x']+20,bb['y']+20-(bb['y']-t['y'])*i/20); await pg.wait_for_timeout(30)
        await pg.mouse.up(); await pg.wait_for_timeout(3500)
        print("disc after",await pg.locator('.item .addr').all_inner_texts())
        await pg.screenshot(path="s_disc_after.png")
        await b.close()
asyncio.run(main())
