# 🗺️ Tamil Nadu Google Maps Scraper

A Python-based web scraper that collects business data (name, phone number, address) for **Medical Shops** and **Startup Agencies** across all **38 districts of Tamil Nadu** using Google Maps — with anti-bot detection built in.

---

## 📸 What It Does

- Searches Google Maps for each district × category combination
- Scrolls the sidebar to load more results (lazy-loading handled automatically)
- Parses listing cards using **BeautifulSoup**
- Visits each place's detail page to extract **phone number** and **full address**
- Exports results to **Excel, CSV, and JSON**

---

## 🏗️ Tech Stack

| Tool | Purpose |
|---|---|
| `selenium` | Browser automation |
| `selenium-stealth` | Anti-bot detection bypass |
| `webdriver-manager` | Auto-matches ChromeDriver to your Chrome version |
| `beautifulsoup4` | HTML parsing |
| `pandas` | Data processing & export |
| `openpyxl` | Excel file output |

---

## 📦 Installation

**Prerequisites:** Python 3.8+ and Google Chrome installed.

```bash
pip install selenium selenium-stealth webdriver-manager beautifulsoup4 pandas openpyxl
```

> No need to manually download ChromeDriver — `webdriver-manager` handles it automatically and matches your installed Chrome version.

---

## 🚀 Usage

```bash
python tamilnadu_gmaps_scraper.py
```

That's it. The scraper will run through all district × category combinations and save results when done (or if interrupted with `Ctrl+C`).

---

## ⚙️ Configuration

All tunable settings are at the top of the script:

```python
TAMIL_NADU_DISTRICTS  = [...]   # All 38 districts (edit to target specific ones)
SEARCH_CATEGORIES     = [...]   # e.g. "medical shop", "startup agency"
RESULTS_PER_QUERY     = 12      # How many results to collect per district/category
WAIT_TIMEOUT          = 20      # Seconds to wait for page elements
SCROLL_PAUSE          = 2.0     # Seconds between scroll steps
QUERY_PAUSE           = 5       # Seconds between search queries
DETAIL_PAUSE          = 1.2     # Seconds between detail page visits
```

To run with a **visible browser** (useful for debugging), comment out this line in `build_driver()`:

```python
# options.add_argument("--headless=new")
```

---

## 📁 Output Files

| File | Description |
|---|---|
| `tamilnadu_results.xlsx` | Excel file with auto-sized columns |
| `tamilnadu_results.csv` | UTF-8 CSV (Excel-compatible) |
| `tamilnadu_results.json` | JSON array of records |
| `scraper.log` | Full run log with timestamps |

### Output Columns

```
district | category | name | phone | address | place_url
```

---

## 🔍 How It Works (Step by Step)

```
Step 1 → Navigate to Google Maps search URL for the query
Step 2 → Scroll the sidebar feed to lazy-load result cards
Step 3 → Parse cards with BeautifulSoup (name + place URL)
Step 4 → Visit each place's detail page to get phone & full address
```

Phone numbers are only available on individual place detail pages, not on listing cards — so the scraper visits each one separately.

---

## 🛡️ Anti-Detection

The scraper uses `selenium-stealth` to mimic a real browser:

- Masks WebDriver automation flags
- Spoofs `navigator.platform`, `vendor`, `WebGL` renderer
- Sets a realistic User-Agent string
- Disables automation extension indicators

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. Scraping Google Maps may violate [Google's Terms of Service](https://policies.google.com/terms). Use responsibly and ensure compliance with applicable laws before deploying this in any production or commercial context.

---

## 📊 Sample Summary Output

```
=======================================================
  SCRAPE COMPLETE
=======================================================
  Total records     : 408
  Districts covered : 17 / 38
  With phone number : 312
  With address      : 389
=======================================================
```

---

## 🤝 Contributing

Pull requests are welcome! If Google Maps updates its HTML structure and selectors break, feel free to open an issue or submit a fix.

---

## 📄 License

MIT License — free to use, modify, and distribute.
