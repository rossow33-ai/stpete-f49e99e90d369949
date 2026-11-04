import asyncio,sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        pg=await (await b.new_context(viewport={"width":390,"height":844})).new_page()
        pg.on("console",lambda m:print("console",m.type,m.text)); pg.on("pageerror",lambda e:print("ERR",e))
        pg.on("response",lambda r:print(r.status,r.request.method,r.url[:90]))
        pg.on("requestfailed",lambda r:print("FAIL",r.url[:90],r.failure))
        await pg.goto(sys.argv[1]); await pg.click('[data-w="Realtor"]'); await pg.wait_for_selector('.item')
        await pg.click('#addBtn'); await pg.fill('#aMls','TEST123'); await pg.fill('#aAddr','100 Central Ave'); await pg.fill('#aZip','33701')
        await pg.click('#aSave'); await pg.wait_for_timeout(5000); await b.close()
asyncio.run(main())
