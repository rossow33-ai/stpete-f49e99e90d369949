import asyncio,sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        mk=lambda who,view: b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        ctx=await mk('Tom','tinder'); pg=await ctx.new_page(); pg.on("pageerror",lambda e:print("ERR",e)); pg.on("console",lambda m: m.type=='error' and print("CON",m.text))
        await ctx.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','tinder')")
        await pg.goto(sys.argv[1]); await pg.wait_for_selector('.card'); await pg.wait_for_timeout(1200)
        txt=lambda s: pg.evaluate(f"document.querySelector('{s}').textContent")
        print("counts q/list/dis",await txt('#nQ'),await txt('#nList'),await txt('#nDis'))
        await pg.screenshot(path="s_q.png")
        await pg.click('#bNote'); await pg.wait_for_timeout(500); await pg.screenshot(path="s_notes_tinder.png")
        await pg.fill('#nTa','Test note from Tom via Realtinder'); await pg.click('[data-add-note]'); await pg.wait_for_timeout(2500)
        print("notes in sheet",await pg.locator('#notesM .note').count(), "card still same:", await pg.locator('.card:not(.back) .a').inner_text())
        await pg.screenshot(path="s_notes_tinder2.png")
        await pg.click('[data-close]')
        # realtor sees it
        c2=await mk('Realtor','list'); p2=await c2.new_page(); await c2.add_init_script("localStorage.setItem('who','Realtor');localStorage.setItem('view','tinder')")
        await p2.goto(sys.argv[1]); await p2.wait_for_selector('.card'); await p2.wait_for_timeout(1500)
        await p2.click('#bNote'); await p2.wait_for_timeout(400)
        print("realtor sees notes:",await p2.locator('#notesM .note').all_inner_texts())
        await p2.fill('#nTa','Realtor reply'); await p2.click('[data-add-note]'); await p2.wait_for_timeout(2500)
        await p2.close()
        # tom: swipe right 2, left 1, then list
        await pg.click('#bYes'); await pg.wait_for_timeout(900); await pg.click('#bYes'); await pg.wait_for_timeout(900); await pg.click('#bNo'); await pg.wait_for_timeout(900)
        await pg.click('#burger'); await pg.click('[data-v=list]'); await pg.wait_for_timeout(1500)
        await pg.screenshot(path="s_thumbs.png")
        await pg.locator('.item .main').first.click(); await pg.wait_for_timeout(600)
        print("list sheet notes:",await pg.locator('#notesM .note').all_inner_texts()); await pg.screenshot(path="s_notes_list.png")
        await pg.click('[data-close]')
        await pg.click('#burger'); await pg.click('[data-v=discard]'); await pg.wait_for_timeout(1200); await pg.screenshot(path="s_thumbs_disc.png")
        await b.close()
asyncio.run(main())
