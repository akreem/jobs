import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.keejob.com/offres-emploi/"

def scrape_keejob(max_pages=None, start_page=1):
    """
    Scrape all job listings from Keejob.
    
    Args:
        max_pages: Maximum number of pages to scrape. If None, scrapes all pages.
        start_page: Page number to start from (default: 1)
    """
    all_jobs = []
    page = start_page
    pages_scraped = 0
    
    while True:
        # Build URL with page parameter
        url = f"{BASE_URL}?page={page}" if page > 1 else BASE_URL
        
        print(f"Scraping page {page}...")
        res = requests.get(url)
        
        if res.status_code != 200:
            print(f"Failed to fetch page {page}, stopping.")
            break
            
        soup = BeautifulSoup(res.text, "html.parser")
        jobs_html = soup.select("article")
        
        # If no jobs found, we've reached the end
        if not jobs_html:
            print(f"No more jobs found on page {page}, stopping.")
            break

        page_jobs = []
        for j in jobs_html:
            # Title - in h2 > a
            title_el = j.select_one("h2 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = "https://www.keejob.com" + title_el["href"]
            
            # Extract keejob_id from URL (e.g., /offres-emploi/231807/...)
            keejob_id = title_el["href"].split("/")[2] if len(title_el["href"].split("/")) > 2 else None

            # Company - paragraph after h2
            company_el = j.select_one("h2 + p a, h2 + p span")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Location - find the map marker icon and get next text
            location_el = j.select_one(".fa-map-marker-alt")
            if location_el:
                location_parent = location_el.find_parent()
                location = location_parent.get_text(strip=True).replace("📍", "").strip()
            else:
                location = "N/A"

            # Date - find clock icon and get text
            date_el = j.select_one(".fa-clock")
            if date_el:
                date_parent = date_el.find_parent()
                date_posted = date_parent.get_text(strip=True)
            else:
                date_posted = None

            # Description - the paragraph in the description section
            desc_el = j.select_one("div.mb-3 p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            page_jobs.append({
                "keejob_id": keejob_id,
                "source": "keejob",
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": description,
                "date_posted": date_posted,
            })
        
        all_jobs.extend(page_jobs)
        pages_scraped += 1
        print(f"Found {len(page_jobs)} jobs on page {page} (total: {len(all_jobs)})")
        
        # Check if we've reached max_pages
        if max_pages and pages_scraped >= max_pages:
            print(f"Reached maximum pages ({max_pages}), stopping.")
            break
        
        page += 1

    return all_jobs
