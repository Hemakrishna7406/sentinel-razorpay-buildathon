import asyncio
from playwright.async_api import async_playwright
import os


async def capture_screenshots():
    out_dir = "C:/Users/hemak/.gemini/antigravity-ide/brain/1153572e-5323-4271-af60-812d006f7637/scratch/screenshots"
    os.makedirs(out_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Desktop
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(2000)  # wait for initial animations

        # A. Hero - initial viewport
        await page.screenshot(path=f"{out_dir}/A_hero.png")

        # B. Hero - 50% scroll (simulate small scroll)
        await page.evaluate("window.scrollBy(0, 300)")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{out_dir}/B_hero_scrolled.png")

        # C. Behavioral Risk section
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{out_dir}/C_behavioral_risk.png")

        # D. Policy evaluation
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{out_dir}/D_policy.png")

        # E. Containment moment
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{out_dir}/E_containment.png")

        # F. Capability Token
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{out_dir}/F_capability_token.png")

        # G. Architecture
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{out_dir}/G_architecture.png")

        # H. Live Simulation open
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollBy(0, 300)")
        await page.click(".fixed.bottom-8.right-8 button", force=True)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{out_dir}/H_live_sim_open.png")

        # I. Live Simulation -> CONTAIN result
        await page.click('button:has-text("RUN EVALUATION")', force=True)
        await page.wait_for_timeout(4000)  # wait for evaluation
        await page.screenshot(path=f"{out_dir}/I_live_sim_result.png")

        # Mobile
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto("http://localhost:5173")
        await mobile_page.wait_for_timeout(2000)

        # J. Mobile 390px hero
        await mobile_page.screenshot(path=f"{out_dir}/J_mobile_hero.png")

        await browser.close()
        print("Screenshots captured successfully.")


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
