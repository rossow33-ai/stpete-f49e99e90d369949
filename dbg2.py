import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        pg=await (await b.new_context(viewport={"width":390,"height":844})).new_page()
        pg.on("pageerror",lambda e:print("ERR",e)); pg.on("console",lambda m:print("CON",m.text))
        await pg.add_init_script("localStorage.setItem('who','Tom');localStorage.setItem('view','tinder')")
        await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(4000)
        print(await pg.evaluate("document.querySelector('#tinder').innerHTML.slice(0,200)"))
        await b.close()
asyncio.run(main())
