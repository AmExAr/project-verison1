import asyncio
from playwright.async_api import async_playwright
import pandas as pd

BASE_URL = "https://ontico.ru/events.html"


async def parse():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(BASE_URL)
        await page.wait_for_load_state("networkidle")

        data = []

        # 1. собираем все ссылки на конференции
        links = await page.query_selector_all("a")

        event_urls = []
        for link in links:
            href = await link.get_attribute("href")
            if href and ("conf" in href.lower() or "load" in href.lower()):
                if href.startswith("http"):
                    event_urls.append(href)
                else:
                    event_urls.append("https://ontico.ru" + href)

        event_urls = list(set(event_urls))

        print(f"Найдено конференций: {len(event_urls)}")

        # 2. идем в каждую конференцию
        for url in event_urls:
            try:
                await page.goto(url)
                await page.wait_for_timeout(2000)

                # ищем ссылки на спикеров / программу
                sublinks = await page.query_selector_all("a")

                target_pages = []
                for sl in sublinks:
                    href = await sl.get_attribute("href")
                    if href and any(x in href.lower() for x in ["speaker", "program", "abstract"]):
                        if href.startswith("http"):
                            target_pages.append(href)
                        else:
                            target_pages.append(url.rstrip("/") + "/" + href.lstrip("/"))

                target_pages = list(set(target_pages))

                # 3. парсим страницы со спикерами
                for tp in target_pages:
                    try:
                        await page.goto(tp)
                        await page.wait_for_timeout(2000)

                        blocks = await page.query_selector_all("h2, h3")

                        for b in blocks:
                            name = await b.inner_text()

                            parent = await b.evaluate_handle("el => el.parentElement")

                            try:
                                desc_el = await parent.query_selector("p")
                                desc = await desc_el.inner_text() if desc_el else ""
                            except:
                                desc = ""

                            data.append({
                                "event_url": url,
                                "page_url": tp,
                                "speaker_or_title": name.strip(),
                                "description": desc.strip()
                            })

                    except:
                        continue

            except:
                continue

        await browser.close()

        df = pd.DataFrame(data)

        df = df[df["speaker_or_title"].str.len() > 5]

        df.to_csv("ontico_speakers.csv", index=False, encoding="utf-8-sig")

        print("✅ Готово! ontico_speakers.csv")


asyncio.run(parse())
