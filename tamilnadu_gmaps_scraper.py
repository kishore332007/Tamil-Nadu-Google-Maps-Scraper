"""
===============================================================
 Google Maps Scraper — Tamil Nadu Medical Shops & Startup Agencies
 Target   : All 38 Districts of Tamil Nadu
 Fields   : Name, Phone Number, Address
 Per District: 10–15 results per category
 Tools    : selenium + selenium-stealth (for anti-detection)

 FIX: Uses selenium-stealth which applies stealth techniques to avoid
      bot detection and CAPTCHAs. webdriver-manager auto-matches your
      installed Chrome version — NO version mismatch errors.
===============================================================

STEP 1 — INSTALL REQUIREMENTS:
    pip install selenium selenium-stealth webdriver-manager beautifulsoup4 pandas openpyxl

STEP 2 — CHECK YOUR CHROME VERSION (optional, auto-detected):
    Open Chrome → Address bar → type:  chrome://version

STEP 3 — RUN:
    python tamilnadu_gmaps_scraper.py

OUTPUT FILES:
    tamilnadu_results.xlsx
    tamilnadu_results.csv
    tamilnadu_results.json
    scraper.log
"""

# ── Standard Library ──────────────────────────────────────────
import time
import re
import json
import logging
import subprocess
import sys
import os

# ── Third-Party ───────────────────────────────────────────────
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager


# ══════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  CONFIGURATION  (edit these if needed)
# ══════════════════════════════════════════════════════════════

# All 38 Districts of Tamil Nadu
TAMIL_NADU_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
    "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal",
]

# What to search in each district
SEARCH_CATEGORIES = [
    "medical shop",
    "startup agency",
]

RESULTS_PER_QUERY = 12    # 10-15 per district per category
WAIT_TIMEOUT      = 20    # seconds to wait for page elements
SCROLL_PAUSE      = 2.0   # seconds between each scroll step
QUERY_PAUSE       = 5     # seconds between search queries
DETAIL_PAUSE      = 1.2   # seconds between detail page visits


# ══════════════════════════════════════════════════════════════
#  AUTO-DETECT CHROME VERSION
# ══════════════════════════════════════════════════════════════

def get_chrome_version():
    """
    Tries to detect the major Chrome version on Windows/macOS/Linux.
    Returns integer like 136, or None if detection fails.
    undetected_chromedriver uses this to download the exact driver.
    """
    if sys.platform == "win32":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run(
                        ["powershell", "-command",
                         f"(Get-Item '{path}').VersionInfo.FileVersion"],
                        capture_output=True, text=True, timeout=5
                    )
                    version_str = result.stdout.strip().split(".")[0]
                    return int(version_str)
                except Exception:
                    pass

    elif sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "--version"],
                capture_output=True, text=True, timeout=5
            )
            version_str = result.stdout.strip().split()[-1].split(".")[0]
            return int(version_str)
        except Exception:
            pass

    else:  # Linux
        try:
            result = subprocess.run(
                ["google-chrome", "--version"],
                capture_output=True, text=True, timeout=5
            )
            version_str = result.stdout.strip().split()[-1].split(".")[0]
            return int(version_str)
        except Exception:
            pass

    return None


# ══════════════════════════════════════════════════════════════
#  BUILD DRIVER  (undetected-chromedriver)
# ══════════════════════════════════════════════════════════════

def build_driver():
    """
    Creates a Chrome WebDriver using selenium with stealth.

    WHY selenium + stealth instead of undetected-chromedriver?
    ------------------------------------------------------------------
    1. Auto-manages ChromeDriver binary to match YOUR Chrome version
       so the version mismatch error never occurs.
    2. Applies stealth techniques to avoid bot-detection.
    3. Compatible with modern Python versions.

    Set headless=False below if you want to WATCH the browser live.
    """
    chrome_version = get_chrome_version()
    if chrome_version:
        log.info(f"Detected Chrome major version: {chrome_version}")
    else:
        log.warning("Chrome version not auto-detected — webdriver-manager will handle.")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")           # remove this line to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=webdriver.ChromeService(ChromeDriverManager().install()),
        options=options
    )

    # Apply stealth
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    )

    driver.set_page_load_timeout(30)
    log.info("Chrome WebDriver ready.")
    return driver


# ══════════════════════════════════════════════════════════════
#  STEP 1 — OPEN GOOGLE MAPS AND SEARCH
# ══════════════════════════════════════════════════════════════

def search_google_maps(driver, query):
    """
    Navigate to Google Maps results page for the given query.
    Waits for the left sidebar (div[role='feed']) to appear.
    """
    encoded = query.replace(" ", "+")
    url = f"https://www.google.com/maps/search/{encoded}"
    log.info(f"  Navigating: {url}")
    driver.get(url)

    # Dismiss cookie consent if it appears
    try:
        consent_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Accept') or contains(., 'Agree')]")
            )
        )
        consent_btn.click()
        time.sleep(1)
        log.info("  Cookie consent dismissed.")
    except TimeoutException:
        pass  # No dialog — that's fine

    # Wait for results feed
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
        )
        log.info("  Results feed loaded.")
    except TimeoutException:
        log.warning("  Feed not found — page may be slow or captcha'd.")


# ══════════════════════════════════════════════════════════════
#  STEP 2 — SCROLL SIDEBAR TO LOAD MORE CARDS
# ══════════════════════════════════════════════════════════════

def scroll_results_panel(driver, target_count):
    """
    Google Maps lazy-loads place cards as you scroll the LEFT sidebar.
    We scroll the 'div[role=feed]' element (not the whole window)
    until at least target_count cards appear in the DOM.
    """
    try:
        feed = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
    except NoSuchElementException:
        log.warning("  Scroll panel not found.")
        return

    prev_count = 0
    stall_count = 0

    for attempt in range(40):
        cards = driver.find_elements(
            By.CSS_SELECTOR, "div[role='feed'] a[href*='/maps/place/']"
        )
        current_count = len(cards)
        log.info(f"  Scroll #{attempt+1}: {current_count} cards (target {target_count})")

        if current_count >= target_count:
            break

        if "end of the list" in driver.page_source.lower():
            log.info("  End of results list reached.")
            break

        # Stop if no new cards after 3 scrolls
        if current_count == prev_count:
            stall_count += 1
            if stall_count >= 3:
                log.info("  No new cards loading — scroll stopped.")
                break
        else:
            stall_count = 0

        prev_count = current_count

        # Scroll the sidebar feed element down
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", feed
        )
        time.sleep(SCROLL_PAUSE)


# ══════════════════════════════════════════════════════════════
#  STEP 3 — PARSE LISTING CARDS WITH BEAUTIFULSOUP
# ══════════════════════════════════════════════════════════════

def parse_listing_cards(page_source, max_results):
    """
    Uses BeautifulSoup to parse the rendered HTML from Google Maps.

    Each place card is an <a href="/maps/place/..."> element.
    We extract:
      - name         : from aria-label or bold headline span
      - address      : short snippet visible in the card
      - place_url    : full URL to the detail page (used in Step 4)

    Phone number is NOT on the card — only on the detail page.
    """
    soup = BeautifulSoup(page_source, "html.parser")

    feed = soup.find("div", {"role": "feed"})
    if not feed:
        log.warning("  BS4: feed panel not found in HTML.")
        return []

    raw_cards = feed.find_all("a", href=re.compile(r"/maps/place/"))
    log.info(f"  BS4 found {len(raw_cards)} raw card elements.")

    results = []
    seen_names = set()

    for card in raw_cards:
        if len(results) >= max_results:
            break

        # ── Name: Method 1 — aria-label on the <a> tag ────────
        aria = card.get("aria-label", "").strip()
        name = aria.split("·")[0].strip() if aria else ""

        # ── Name: Method 2 — headline span inside card ─────────
        if not name:
            for cls_pattern in [r"fontHeadlineSmall", r"NrDZNb", r"qBF1Pd"]:
                span = card.find("span", class_=re.compile(cls_pattern))
                if span:
                    name = span.get_text(strip=True)
                    break

        # ── Name: Method 3 — first text node (last resort) ─────
        if not name:
            texts = [t.strip() for t in card.stripped_strings]
            name = texts[0] if texts else ""

        if not name or name in seen_names:
            continue
        seen_names.add(name)

        # ── Address snippet visible in the card ────────────────
        address_snippet = ""
        for div in card.find_all("div", class_=re.compile(r"fontBodyMedium|W4Efsd")):
            text = div.get_text(" ", strip=True)
            if text and text != name and len(text) > 5:
                address_snippet = text
                break

        # ── Place detail URL ───────────────────────────────────
        href = card.get("href", "")
        place_url = (
            "https://www.google.com" + href if href.startswith("/") else href
        )

        results.append({
            "name":      name,
            "address":   address_snippet,
            "phone":     "",
            "place_url": place_url,
        })

    log.info(f"  BS4 parsed {len(results)} unique places.")
    return results


# ══════════════════════════════════════════════════════════════
#  STEP 4 — DETAIL PAGE: FULL ADDRESS + PHONE NUMBER
# ══════════════════════════════════════════════════════════════

def scrape_place_detail(driver, record):
    """
    Visits the individual Google Maps page for ONE business.

    Google only renders phone number and full address on the
    place detail page — not on the search result cards.

    Selectors used:
      Phone   → div[data-item-id^='phone:tel:']  (aria-label holds the number)
      Address → div[data-item-id='address']       (aria-label holds full address)
    """
    url = record.get("place_url", "")
    if not url:
        record["phone"]   = "N/A"
        record["address"] = record.get("address", "N/A") or "N/A"
        return record

    try:
        driver.get(url)

        # Wait for at least one data-item-id element to be present
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id]"))
        )
        time.sleep(DETAIL_PAUSE)  # let remaining JS finish rendering

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ── Phone Number ──────────────────────────────────────
        phone_div = soup.find(attrs={"data-item-id": re.compile(r"^phone:tel:")})
        if phone_div:
            raw = phone_div.get("aria-label", "")
            phone = re.sub(r"(?i)phone\s*:", "", raw).strip()
        else:
            # Fallback: <a href="tel:+91...">
            tel_link = soup.find("a", href=re.compile(r"^tel:"))
            phone = tel_link["href"].replace("tel:", "").strip() if tel_link else "N/A"

        if not phone:
            phone = "N/A"

        # ── Full Address ──────────────────────────────────────
        addr_elem = soup.find(attrs={"data-item-id": "address"})
        if addr_elem:
            raw_addr = addr_elem.get("aria-label", "")
            full_address = re.sub(r"(?i)address\s*:", "", raw_addr).strip()
        else:
            full_address = ""

        # Keep card snippet if detail page has nothing
        if not full_address:
            full_address = record.get("address", "") or "N/A"

        record["phone"]   = phone
        record["address"] = full_address

    except TimeoutException:
        log.warning(f"  Timeout on detail page for '{record['name']}'")
        record.setdefault("phone", "N/A")
        if not record.get("address"):
            record["address"] = "N/A"

    except Exception as exc:
        log.warning(f"  Detail error for '{record['name']}': {exc}")
        record.setdefault("phone", "N/A")
        if not record.get("address"):
            record["address"] = "N/A"

    return record


# ══════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════

def scrape_all():
    """
    Loops over every district × category combination.
    Runs all 4 steps for each pair and collects results.
    """
    driver = build_driver()
    all_records = []

    total = len(TAMIL_NADU_DISTRICTS) * len(SEARCH_CATEGORIES)
    done = 0

    try:
        for district in TAMIL_NADU_DISTRICTS:
            for category in SEARCH_CATEGORIES:
                done += 1
                query = f"{category} in {district} Tamil Nadu"
                print(f"\n[{done}/{total}] Searching: {query}")

                # Step 1: Load the search page
                try:
                    search_google_maps(driver, query)
                except InvalidSessionIdException:
                    log.warning("Session invalid, rebuilding driver")
                    driver.quit()
                    driver = build_driver()
                    try:
                        search_google_maps(driver, query)
                    except Exception as e:
                        log.error(f"Error searching {query} after rebuild: {e}")
                        continue

                # Step 2: Scroll sidebar to load enough cards
                scroll_results_panel(driver, RESULTS_PER_QUERY)

                # Step 3: Parse cards with BeautifulSoup
                cards = parse_listing_cards(driver.page_source, RESULTS_PER_QUERY)

                if not cards:
                    log.warning(f"  No results found — skipping.")
                    continue

                # Step 4: Visit each place detail page
                enriched = []
                for i, card in enumerate(cards, 1):
                    print(f"    [{i}/{len(cards)}] {card['name']}")
                    try:
                        card = scrape_place_detail(driver, card)
                    except InvalidSessionIdException:
                        log.warning(f"Session invalid during detail for {card['name']}, skipping")
                        card.setdefault("phone", "N/A")
                        if not card.get("address"):
                            card["address"] = "N/A"
                    card["district"] = district
                    card["category"] = category.title()
                    enriched.append(card)
                    time.sleep(0.5)

                all_records.extend(enriched)
                print(f"  Collected {len(enriched)} records.")
                time.sleep(QUERY_PAUSE)

    except KeyboardInterrupt:
        print("\nInterrupted — saving collected data...")

    finally:
        driver.quit()
        log.info("WebDriver closed.")

    return all_records


# ══════════════════════════════════════════════════════════════
#  SAVE RESULTS
# ══════════════════════════════════════════════════════════════

def save_results(records):
    """
    Saves all records to Excel, CSV, and JSON files.
    """
    if not records:
        print("\nNo records collected. Nothing saved.")
        return

    cols = ["district", "category", "name", "phone", "address", "place_url"]
    df = pd.DataFrame(records)

    for col in cols:
        if col not in df.columns:
            df[col] = "N/A"

    df = df[cols]
    df.dropna(subset=["name"], inplace=True)
    df.replace("", "N/A", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Excel
    xlsx_path = "tamilnadu_results.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
        ws = writer.sheets["Results"]
        for col_cells in ws.columns:
            width = max(len(str(c.value or "")) for c in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(width + 4, 70)
    print(f"\nExcel saved  -> {xlsx_path}")

    # CSV
    csv_path = "tamilnadu_results.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSV saved    -> {csv_path}")

    # JSON
    json_path = "tamilnadu_results.json"
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"JSON saved   -> {json_path}")

    # Summary
    print("\n" + "=" * 55)
    print("  SCRAPE COMPLETE")
    print("=" * 55)
    print(f"  Total records     : {len(df)}")
    print(f"  Districts covered : {df['district'].nunique()} / 38")
    print(f"  With phone number : {(df['phone'] != 'N/A').sum()}")
    print(f"  With address      : {(df['address'] != 'N/A').sum()}")
    print("=" * 55)


# ══════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  Tamil Nadu Google Maps Scraper")
    print("  Medical Shops & Startup Agencies - 38 Districts")
    print("=" * 55)

    records = scrape_all()
    save_results(records)
