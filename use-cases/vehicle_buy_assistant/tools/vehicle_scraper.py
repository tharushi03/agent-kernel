"""
Vehicle Web Scraper - Updated Riyasewana & PatPat Integration
Fetches real-time car listings from local vehicle marketplaces with improved selectors
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import random
import json
from datetime import datetime

# Known car makes for better parsing
CAR_MAKES = ['Toyota', 'Honda', 'Suzuki', 'Nissan', 'Hyundai', 'BMW', 'Mercedes',
             'Audi', 'Ford', 'Mitsubishi', 'Mazda', 'Tesla', 'Chevrolet', 'KIA',
             'Volkswagen', 'Subaru', 'Lexus', 'Daihatsu', 'Isuzu', 'Tata',
             'Perodua', 'Proton', 'Kia', 'Jeep', 'Land Rover', 'Volvo',
             'Peugeot', 'Renault', 'Skoda']

VEHICLE_TYPES = {
    'SUV': ['vezel', 'rav4', 'cr-v', 'suv', 'tucson', 'q5', 'gla', 'x3',
            'hrv', 'hr-v', 'outlander', 'rush', 'terios', 'sportage'],
    'Sedan': ['aqua', 'camry', 'accord', 'civic', 'altima', 'corolla', 'elantra',
              'a4', '3 series', 'lancer', 'premio', 'allion', 'axio', 'grace'],
    'Hatchback': ['fit', 'jazz', 'swift', 'i10', 'i20', 'polo', 'golf', 'fiesta',
                  'vitz', 'yaris', 'wagon r', 'alto', 'celerio', 'passo'],
    'Truck': ['f-150', 'tacoma', 'hilux', 'ranger', 'pickup', 'd-max', 'navara'],
    'Van': ['van', 'minivan', 'odyssey', 'hiace', 'delica', 'alphard', 'voxy', 'noah'],
    'Electric': ['leaf', 'ioniq', 'e-golf', 'prius prime', 'kona ev'],
    'Hybrid': ['prius', 'aqua hybrid', 'insight', 'grace hybrid'],
}

DESKTOP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


# ── Utility helpers ──────────────────────────────────────────────────────────

def extract_make_model(title):
    for make in CAR_MAKES:
        if make.lower() in title.lower():
            model_part = re.sub(re.escape(make), '', title, flags=re.IGNORECASE).strip()
            model_part = re.sub(r'\b(19|20)\d{2}\b', '', model_part).strip()
            model_part = re.sub(r'\s+', ' ', model_part).strip(' ,-')
            return make, model_part if model_part else 'Unknown'
    parts = title.split()
    make = parts[0] if parts else 'Unknown'
    model = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return make, model


def infer_vehicle_type(title, model):
    combined = f"{title} {model}".lower()
    for vtype, keywords in VEHICLE_TYPES.items():
        if any(kw in combined for kw in keywords):
            return vtype
    return 'Sedan'


def extract_year(title):
    m = re.search(r'\b(19|20)\d{2}\b', title)
    return int(m.group()) if m else None


def extract_price(price_text):
    if not price_text:
        return 0
    digits = re.sub(r'[^\d]', '', price_text)
    return int(digits) if digits else 0


def first(elements, default=None):
    """Return first non-None result from a list of BeautifulSoup elements."""
    for e in elements:
        if e:
            return e
    return default


# ── Riyasewana Scraper ───────────────────────────────────────────────────────

RIYASEWANA_URLS = [
    "https://riyasewana.com/search/cars",
    "https://riyasewana.com/search/suv",
    "https://riyasewana.com/search/hybrid-cars",
]

RIYASEWANA_LISTING_SELECTORS = [
    'li[class*="item"]',
    'div[class*="listing-item"]',
    'div[class*="item"]',
    '.box',
    'article',
]

RIYASEWANA_TITLE_SELECTORS = [
    'h2 a', 'h3 a', 'h2', 'h3',
    '.heading a', '.title a',
    '.heading', '.title',
    'a[href*="/cars/"]',
]

RIYASEWANA_PRICE_SELECTORS = [
    '.price', '.price-info', '.amount',
    '[class*="price"]',
]


def scrape_riyasewana(limit=10):
    """
    Scrape car listings from Riyasewana.com with updated selectors.

    Returns:
        List of vehicle dictionaries
    """
    vehicles = []

    for url in RIYASEWANA_URLS:
        if len(vehicles) >= limit:
            break

        try:
            print(f"  🔍 Trying Riyasewana: {url}")
            resp = requests.get(url, headers=DESKTOP_HEADERS, timeout=12)

            if resp.status_code != 200:
                print(f"  ⚠️ HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Find listings using multiple possible selectors
            listings = []
            for sel in RIYASEWANA_LISTING_SELECTORS:
                listings = soup.select(sel)
                if len(listings) >= 3:
                    print(f"  ✅ Found {len(listings)} items with '{sel}'")
                    break

            if not listings:
                print("  ⚠️ No listings found with any selector on this URL")
                continue

            for item in listings[:limit - len(vehicles)]:
                try:
                    # Title
                    title_elem = None
                    for sel in RIYASEWANA_TITLE_SELECTORS:
                        title_elem = item.select_one(sel)
                        if title_elem and title_elem.get_text(strip=True):
                            break

                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    if len(title) < 4:
                        continue

                    # Price
                    price_text = ''
                    for sel in RIYASEWANA_PRICE_SELECTORS:
                        pe = item.select_one(sel)
                        if pe:
                            price_text = pe.get_text(strip=True)
                            break

                    make, model = extract_make_model(title)
                    year = extract_year(title)
                    vtype = infer_vehicle_type(title, model)

                    vehicles.append({
                        'id': len(vehicles) + 1,
                        'make': make,
                        'model': model,
                        'year': year or 2020,
                        'type': vtype,
                        'price': extract_price(price_text),
                        'mpg': 25,
                        'safety_rating': 4,
                        'features': ['Riyasewana Verified'],
                        'description': title,
                        'source': 'Riyasewana',
                        'scraped_at': datetime.now().isoformat(),
                    })

                except Exception:
                    continue

            if vehicles:
                print(f"  ✅ Got {len(vehicles)} vehicles from Riyasewana")

        except Exception as e:
            print(f"  ⚠️ Riyasewana error: {str(e)[:80]}")

        time.sleep(random.uniform(1.5, 3.0))

    return vehicles


# ── PatPat Scraper (disabled — returns 404; using Parse.bot API instead) ─────
#
# PATPAT_URLS = [
#     "https://patpat.lk/vehicles/cars",
#     "https://patpat.lk/vehicles",
#     "https://patpat.lk/cars",
# ]
#
# PATPAT_LISTING_SELECTORS = [
#     '.vehicle-card', '.ad-item', '.listing',
#     '[class*="vehicle"]', '[class*="listing"]',
#     '.card', 'article',
# ]
#
# PATPAT_TITLE_SELECTORS = [
#     '.title', '.name', '.vehicle-title',
#     'h2', 'h3', 'h4', 'a',
# ]
#
# PATPAT_PRICE_SELECTORS = [
#     '.price', '.amount', '[class*="price"]',
# ]
#
#
# def scrape_patpat(limit=10):
#     """
#     Scrape car listings from PatPat.lk with updated selectors.
#     NOTE: Disabled — PatPat returns 404 for vehicle pages.
#           The Parse.bot API covers Riyasewana data reliably instead.
#     Returns:
#         List of vehicle dictionaries
#     """
#     vehicles = []
#     for url in PATPAT_URLS:
#         if len(vehicles) >= limit:
#             break
#         try:
#             resp = requests.get(url, headers=DESKTOP_HEADERS, timeout=12)
#             if resp.status_code != 200:
#                 continue
#             soup = BeautifulSoup(resp.text, 'html.parser')
#             listings = []
#             for sel in PATPAT_LISTING_SELECTORS:
#                 listings = soup.select(sel)
#                 if len(listings) >= 3:
#                     break
#             if not listings:
#                 continue
#             for item in listings[:limit - len(vehicles)]:
#                 try:
#                     title_elem = None
#                     for sel in PATPAT_TITLE_SELECTORS:
#                         title_elem = item.select_one(sel)
#                         if title_elem and title_elem.get_text(strip=True):
#                             break
#                     if not title_elem:
#                         continue
#                     title = title_elem.get_text(strip=True)
#                     if len(title) < 4:
#                         continue
#                     price_text = ''
#                     for sel in PATPAT_PRICE_SELECTORS:
#                         pe = item.select_one(sel)
#                         if pe:
#                             price_text = pe.get_text(strip=True)
#                             break
#                     make, model = extract_make_model(title)
#                     year = extract_year(title)
#                     vtype = infer_vehicle_type(title, model)
#                     vehicles.append({
#                         'id': len(vehicles) + 1,
#                         'make': make, 'model': model,
#                         'year': year or 2020, 'type': vtype,
#                         'price': extract_price(price_text),
#                         'mpg': 25, 'safety_rating': 4,
#                         'features': ['PatPat Verified'],
#                         'description': title, 'source': 'PatPat',
#                         'scraped_at': datetime.now().isoformat(),
#                     })
#                 except Exception:
#                     continue
#         except Exception:
#             continue
#         time.sleep(random.uniform(1.5, 3.0))
#     return vehicles


# ── Main entry point ─────────────────────────────────────────────────────────

def get_realtime_vehicles(limit_per_site=10, use_cache=True,
                           cache_file='data/cached_vehicles.json'):
    """
    Fetch vehicles from real-time sources with caching.

    Priority:
      1. Parse.bot API (primary — 22,000+ live Riyasewana listings)
      2. Riyasewana web scraping (secondary fallback)
      Caching applied before live fetches when enabled.

    Returns:
        List of unique vehicle dictionaries
    """
    import os

    # Serve from cache if available
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            if cached and isinstance(cached, list) and len(cached) >= 5:
                print(f"📦 Using cached vehicles ({len(cached)} vehicles)")
                return cached
        except Exception:
            pass

    all_vehicles = []
    print("🌐 Fetching real-time vehicle listings...")

    # --- Attempt 1: Parse.bot API ---
    try:
        from tools.vehicle_api import fetch_vehicles_from_api
        api_cars = fetch_vehicles_from_api(limit=limit_per_site * 2)
        if api_cars:
            all_vehicles.extend(api_cars)
            print(f"✅ Got {len(api_cars)} vehicles from Parse.bot API")
    except Exception as e:
        print(f"⚠️ API import/fetch failed: {e}")

    # --- Attempt 2: Riyasewana scraping (fallback only if API fails) ---
    if len(all_vehicles) < limit_per_site:
        riya_cars = scrape_riyasewana(limit_per_site)
        if riya_cars:
            all_vehicles.extend(riya_cars)
            print(f"✅ Got {len(riya_cars)} vehicles from Riyasewana scraping")
        else:
            print("⚠️ Riyasewana scraping returned 0 results")

    # PatPat scraper is disabled (returns 404 — replaced by Parse.bot API)
    # To re-enable: uncomment scrape_patpat() above and call it here.

    # Deduplicate by (make, model, year, price)
    seen = set()
    unique = []
    for v in all_vehicles:
        key = (v['make'].lower(), str(v.get('model', '')).lower(),
               v.get('year'), v.get('price', 0))
        if key not in seen:
            seen.add(key)
            unique.append(v)

    print(f"📊 Total unique vehicles fetched: {len(unique)}")

    # Cache results for subsequent runs
    if unique:
        try:
            dir_name = os.path.dirname(cache_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(unique, f, indent=2)
            print(f"💾 Cached {len(unique)} vehicles to {cache_file}")
        except Exception:
            pass

    return unique


if __name__ == '__main__':
    print("🧪 Testing vehicle scraper...\n")
    cars = get_realtime_vehicles(limit_per_site=5, use_cache=False)
    print(f"\n📋 Sample results ({len(cars)} vehicles):")
    for c in cars[:5]:
        price_str = f"Rs. {c['price']:,}" if c.get('price') else "Price N/A"
        print(f"  {c['make']} {c['model']} ({c['year']}) - {price_str} [{c['source']}]")
