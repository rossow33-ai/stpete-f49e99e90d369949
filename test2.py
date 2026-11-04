import asyncio,sys
from playwright.async_api import async_playwright
URL=sys.argv[1]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        pg=await ctx.new_page(); pg.on("console",lambda m:print("console",m.text) if m.type=="error" else None); pg.on("pageerror",lambda e:print("ERR",e))
        await pg.goto(URL); await pg.click('[data-w="Tom"]'); await pg.wait_for_selector('.item')
        print("list",await pg.locator('.item').count()); await pg.wait_for_timeout(500); await pg.screenshot(path="s_list.png")
        await pg.click('#burger'); await pg.screenshot(path="s_menu.png")
        await pg.click('[data-v=discard]'); print("disc",await pg.locator('.item').count()); await pg.screenshot(path="s_disc.png")
        await pg.click('#burger'); await pg.click('[data-v=tinder]'); await pg.wait_for_timeout(1500); await pg.screenshot(path="s_tinder.png")
        # realtor adds
        c2=await b.new_context(viewport={"width":390,"height":844}); p2=await c2.new_page()
        await p2.goto(URL); await p2.click('[data-w="Realtor"]'); await p2.wait_for_selector('.item')
        await p2.click('#burger'); await p2.click('[data-v=add]'); await p2.fill('#aMls','TEST123'); await p2.fill('#aAddr','2645 Roy Hanna Dr S'); await p2.fill('#aZip','33712')
        await p2.click('#aSave'); await p2.wait_for_timeout(9000)
        print("p2 view card:",await p2.locator('.card:not(.back) .a').inner_text(), await p2.locator('.card:not(.back) .p').inner_text(), await p2.locator('.card:not(.back) .m').first.inner_text())
        await p2.screenshot(path="s_added.png")
        await pg.wait_for_timeout(8000); print("tom sees first:",await pg.locator('.card:not(.back) .a').inner_text())
        # tom swipes right with mouse drag
        card=pg.locator('.card:not(.back)'); bb=await card.bounding_box(); y=bb['y']+150
        await pg.mouse.move(bb['x']+100,y); await pg.mouse.down()
        for i in range(1,16): await pg.mouse.move(bb['x']+100+i*12,y); await pg.wait_for_timeout(20)
        await pg.screenshot(path="s_swipe.png"); await pg.mouse.up(); await pg.wait_for_timeout(2500)
        print("next card:",await pg.locator('.card:not(.back) .a').inner_text())
        await pg.click('#burger'); await pg.click('[data-v=list]'); print("list now",await pg.locator('.item').count(),"last:",await pg.locator('.item:last-child .meta').inner_text())
        # left swipe the next one via button, check discard count, then restore state
        await pg.click('#burger'); await pg.click('[data-v=tinder]'); await pg.wait_for_timeout(500)
        # cleanup via direct API restore done outside
        await b.close()
asyncio.run(main())
