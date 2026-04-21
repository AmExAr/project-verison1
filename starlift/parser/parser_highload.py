import asyncio
from playwright.async_api import async_playwright
import pandas as pd

URL = "https://highload.ru/moscow/2025/abstracts"

async def parse():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        for _ in range(10):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(500)

        talks = await page.query_selector_all("h2, h3")

        data = []

        for talk in talks:
            title = await talk.inner_text()
            parent = await talk.evaluate_handle("el => el.parentElement")

            try:
                text_block = await parent.query_selector("p")
                description = await text_block.inner_text() if text_block else ""
            except:
                description = ""
            try:
                speaker_el = await parent.query_selector("strong, b")
                speaker = await speaker_el.inner_text() if speaker_el else ""
            except:
                speaker = ""

            data.append({
                "title": title.strip(),
                "speaker": speaker.strip(),
                "description": description.strip()
            })

        await browser.close()

        df = pd.DataFrame(data)

        df = df[df["title"].str.len() > 5]

        df.to_csv("highload_speakers.csv", index=False, encoding="utf-8-sig")

        print("✅ Готово! Файл: highload_speakers.csv")

asyncio.run(parse())
