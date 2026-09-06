import asyncio
from playwright.async_api import async_playwright


async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(2000)
        await page.screenshot(
            path="C:/Users/hemak/.gemini/antigravity-ide/brain/1153572e-5323-4271-af60-812d006f7637/scratch/debug.png"
        )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture())
