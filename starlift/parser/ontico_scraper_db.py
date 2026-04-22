import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any

from playwright.async_api import async_playwright
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1. SETUP & CONFIGURATION (DJANGO ORM)
# ---------------------------------------------------------
# Load environment variables, including DB credentials
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Set up properly to use Django's settings and ORM
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "starlift.settings")
import django

try:
    django.setup()
except Exception as e:
    print(f"Failed to setup Django: {e}")

from asgiref.sync import sync_to_async
from starlift.models import Event

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 3. DATABASE SETUP & UPSERT LOGIC
# ---------------------------------------------------------
def save_to_db(events_data: List[Dict[str, Any]]) -> None:
    """
    Save parsed events to the database using Django ORM (starlift_event table).
    Uses update_or_create to perform UPSERT logic mapping parsed data safely.
    """
    if not events_data:
        logger.info("No events data to save.")
        return

    saved_count = 0
    for data in events_data:
        try:
            # Map parser fields to Django 'Event' model fields
            event_obj, created = Event.objects.update_or_create(
                title=data['title'],
                defaults={
                    'status': 'future', # Conferences from this page are future by default
                    'date': data.get('event_dates'),
                    'location': data.get('location'),
                    'link': data.get('event_url'),
                    'description': data.get('description', ''),
                }
            )
            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to upsert event '{data.get('title')}': {e}")
    
    logger.info(f"Successfully saved/updated {saved_count} events in the database.")

# ---------------------------------------------------------
# 4. PARSING LOGIC
# ---------------------------------------------------------
async def parse_events(base_url: str = "https://ontico.ru/events.html") -> List[Dict[str, str]]:
    """Parse HTML using Playwright and extract event information."""
    events = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"Navigating to {base_url}")
            await page.goto(base_url)
            await page.wait_for_load_state("networkidle")
            
            # The events seem to be loaded in <li class="conferences__item"> based on SSR or JS rendering
            # We wait for the container to be present
            try:
                await page.wait_for_selector(".conferences__item", timeout=10000)
            except Exception as e:
                logger.warning(f"Timeout waiting for elements: {e}")

            # Grab all event blocks
            event_blocks = await page.query_selector_all(".conferences__item")
            
            if not event_blocks:
                logger.warning("No event blocks found on the page! The structure might have changed.")
                await browser.close()
                return events
                
            for block in event_blocks:
                try:
                    # Title
                    title_elem = await block.query_selector(".conferences__title")
                    title = await title_elem.inner_text() if title_elem else ""
                    if not title:
                        continue
                    
                    # Description - some have .conferences__descr and some have .conferences__text
                    # usually .conferences__text has the full description. Let's take the first valid paragraph.
                    desc_elems = await block.query_selector_all("p")
                    description = "\\n".join([await d.inner_text() for d in desc_elems]).strip()

                    # Dates and Location - Often date/location on Ontico's event list is not easily parseable directly
                    # from the main list unless it's in a specific span. Let's setup default blanks.
                    event_dates = "TBD" 
                    location = "TBD" 

                    # URL
                    url_elem = await block.query_selector("a.conferences__btn--more")
                    event_url = ""
                    if url_elem:
                        href = await url_elem.get_attribute("href")
                        if href:
                            if href.startswith("http"):
                                event_url = href
                            else:
                                event_url = f"https://ontico.ru{href}"
                    
                    # Alternative URL if "more" button isn't found
                    if not event_url:
                         url_elem = await block.query_selector("a.conferences__link")
                         if url_elem:
                            href = await url_elem.get_attribute("href")
                            if href:
                                if href.startswith("http"):
                                    event_url = href
                                else:
                                    event_url = f"https://ontico.ru{href}"
                                
                    title = title.strip()
                    
                    # Ontico's cards might have combined locations or dates in p tags, we extracted all 'p' texts to description.
                    
                    events.append({
                        "title": title,
                        "event_dates": event_dates,
                        "description": description,
                        "location": location,
                        "event_url": event_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing a single event block: {e}")
                    continue
                    
            logger.info(f"Successfully parsed {len(events)} events.")
            await browser.close()
            return events
    except Exception as e:
        logger.error(f"Playwright initialization error: {e}")
        return []

# ---------------------------------------------------------
# 5. MAIN EXECUTION
# ---------------------------------------------------------
async def main_async():
    logger.info("Starting Ontico Events Scraper...")
    
    target_url = "https://ontico.ru/events.html"
    
    # 1. Parse Events
    events_data = await parse_events(base_url=target_url)
    
    if not events_data:
        logger.warning("No events were parsed. Ensure standard HTML contains the data or consider changing parser strategy.")
        return
        
    # 2. Save to Database
    save_to_db(events_data)
        
    logger.info("Done.")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
