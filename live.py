import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,has_touch=True,is_mobile=True)
        await ctx.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','tinder')")
        pg=await ctx.new_page(); pg.on("pageerror",lambda e:print("ERR",e))
        await pg.goto(open('/dev/stdin').read().strip() if False else "https://rossow33-ai.github.io/"+open('repo.txt').read().strip()+"/"); await pg.wait_for_selector('.card'); await pg.wait_for_timeout(2000)
        print(await pg.evaluate("[nQ.textContent,nList.textContent,nDis.textContent]"))
        await pg.screenshot(path="/workspace/shots/live_realtinder.png")
        await b.close()
asyncio.run(main())
