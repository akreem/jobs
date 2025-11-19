from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import time

BASE_URL = "https://www.mosaiquefm.net/ar/actualites/1"

def scrape_mosaique_news():
    """
    Scrape the latest news article from Mosaique FM using Selenium.
    Returns list with single article (title and URL) if found.
    """
    driver = None
    try:
        print("Scraping Mosaique FM latest news with Selenium...")
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(BASE_URL)
        
        # Wait for the main item to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mainItem")))
        
        # Give it a moment to fully render
        time.sleep(2)
        
        # Get the page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find the main item (latest article)
        main_item = soup.select_one(".mainItem")
        
        if not main_item:
            print("Could not find main article element")
            return []
        
        # Extract title from h3 > a
        title_el = main_item.select_one("h3 a")
        if not title_el:
            print("Could not find title element")
            return []
        
        title = title_el.get_text(strip=True)
        
        # Extract URL from h3 > a href
        url = title_el.get("href")
        if not url:
            print("Could not find URL")
            return []
        
        # Make URL absolute
        if url.startswith("/"):
            url = "https://www.mosaiquefm.net" + url
        
        article = {
            "title": title,
            "url": url,
            "source": "mosaiquefm",
            "scraped_at": datetime.now().isoformat()
        }
        
        print(f"Found latest article: {title[:50]}...")
        return [article]
        
    except Exception as e:
        print(f"Error scraping news: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()
