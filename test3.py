import asyncio,sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        pg=await ctx.new_page(); pg.on("pageerror",lambda e:print("ERR",e))
        await ctx.add_init_script("localStorage.setItem('who','Tom')")
        await pg.goto(sys.argv[1]); await pg.wait_for_selector('.item'); await pg.wait_for_timeout(3000)
        print("thumbs",await pg.locator('.thumb img').count(),"of",await pg.locator('.item').count(),"bar h",(await pg.locator('.bar').first.bounding_box())['height'])
        await pg.screenshot(path="s_thumbs.png")
        await pg.click('#burger'); await pg.click('[data-v=discard]'); await pg.wait_for_timeout(2500); await pg.screenshot(path="s_thumbs_disc.png")
        await b.close()
asyncio.run(main())
