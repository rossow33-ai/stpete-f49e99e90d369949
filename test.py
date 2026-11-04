import asyncio,sys
from playwright.async_api import async_playwright
URL=sys.argv[1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        pg=await ctx.new_page(); pg.on("console",lambda m:print("console",m.text) if m.type=="error" else None)
        await pg.goto(URL); await pg.wait_for_selector('[data-w="Tom"]'); await pg.click('[data-w="Tom"]')
        await pg.wait_for_selector('.item'); print("items",await pg.locator('.item').count())
        print(await pg.locator('.item').first.inner_text())
        await pg.screenshot(path="shot_list.png")
        await pg.click('.item:nth-child(3) .main'); await pg.screenshot(path="shot_open.png")
        # second user adds property
        c2=await b.new_context(viewport={"width":390,"height":844}); p2=await c2.new_page()
        await p2.goto(URL); await p2.click('[data-w="Realtor"]'); await p2.wait_for_selector('.item')
        await p2.click('#addBtn'); await p2.fill('#aMls','TEST123'); await p2.fill('#aAddr','100 Central Ave'); await p2.fill('#aZip','33701'); await p2.fill('#aPrice','500000')
        await p2.click('#aSave'); await p2.wait_for_timeout(3000)
        print("realtor count",await p2.locator('.item').count(), await p2.locator('.item:last-child .meta').inner_text())
        await p2.fill('.item:last-child textarea','realtor test note'); await p2.click('.item:last-child [data-add-note]'); await p2.wait_for_timeout(2500)
        await pg.wait_for_timeout(7500)
        print("tom count",await pg.locator('.item').count())
        # drag last item (via handle) to top using touch-ish mouse
        h=pg.locator('.item:last-child .handle'); bb=await h.bounding_box(); t=await pg.locator('.item:first-child').bounding_box()
        await pg.mouse.move(bb['x']+20,bb['y']+20); await pg.mouse.down(); 
        for i in range(1,21): await pg.mouse.move(bb['x']+20,bb['y']+20-(bb['y']-t['y'])*i/20); await pg.wait_for_timeout(30)
        await pg.mouse.up(); await pg.wait_for_timeout(3000)
        print("first after drag",await pg.locator('.item:first-child .addr').inner_text())
        await pg.screenshot(path="shot_after.png")
        await p2.wait_for_timeout(7000); print("realtor first",await p2.locator('.item:first-child .addr').inner_text())
        # cleanup: delete test item
        p2.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await p2.click('.item:first-child .main'); await p2.click('.item:first-child [data-del]'); await p2.wait_for_timeout(3000)
        print("after delete",await p2.locator('.item').count(), await p2.locator('.item:first-child .addr').inner_text())
        await b.close()
asyncio.run(main())
