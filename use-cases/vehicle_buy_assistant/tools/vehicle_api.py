"""
Parse.bot API Integration for Riyasewana Vehicle Data
Uses the managed REST API at api.parse.bot to fetch real Sri Lankan car listings
"""

import requests
import re
import os
from datetime import datetime

# Parse.bot scraper endpoint for Riyasewana
PARSE_BOT_SCRAPER_ID = "a20b5c9d-d197-43eb-a622-4b464d151c87"
BASE_URL = f"https://api.parse.bot/scraper/{PARSE_BOT_SCRAPER_ID}"

# Known Sri Lankan car makes for better parsing
CAR_MAKES = [
    'Toyota', 'Honda', 'Suzuki', 'Nissan', 'Hyundai', 'Mitsubishi', 'Mazda',
    'BMW', 'Mercedes', 'Audi', 'Ford', 'Kia', 'Volkswagen', 'Subaru', 'Lexus',
    'Daihatsu', 'Isuzu', 'Tata', 'Perodua', 'Proton', 'Chevrolet', 'Jeep',
    'Land Rover', 'Volvo', 'Peugeot', 'Renault', 'Skoda', 'Seat', 'Fiat'
]

VEHICLE_TYPES = {
    'SUV': ['vezel', 'rav4', 'crv', 'cr-v', 'tucson', 'sportage', 'q5', 'gla',
            'x3', 'suv', 'hrv', 'hr-v', 'outlander', 'rush', 'terios', 'defender'],
    'Sedan': ['aqua', 'camry', 'accord', 'civic', 'altima', 'corolla', 'elantra',
              'a4', '3 series', 'lancer', 'premio', 'allion', 'axio', 'grace',
              'insight', 'fit aria'],
    'Hatchback': ['fit', 'jazz', 'swift', 'i10', 'i20', 'polo', 'golf', 'fiesta',
                  'vitz', 'yaris', 'wagon r', 'alto', 'celerio', 'passo'],
    'Truck': ['f-150', 'tacoma', 'hilux', 'ranger', 'pickup', 'd-max', 'navara'],
    'Van': ['van', 'minivan', 'odyssey', 'caravan', 'hiace', 'delica', 'alphard',
            'voxy', 'noah', 'stepwagon'],
    'Electric': ['tesla', 'bolt', 'leaf', 'ioniq', 'e-golf', 'prius prime', 'kona ev'],
    'Hybrid': ['prius', 'aqua', 'insight', 'grace hybrid', 'axio hybrid', 'vitz hybrid'],
}


def get_api_key():
    """Get the Parse.bot API key from environment or default"""
    return os.environ.get('PARSE_API_KEY', 'pmx_020706817f1d193349a3351c154a9c4f')


def extract_make_model(title):
    """Extract make and model from listing title"""
    for make in CAR_MAKES:
        if make.lower() in title.lower():
            model_part = re.sub(re.escape(make), '', title, flags=re.IGNORECASE).strip()
            model_part = re.sub(r'\b(19|20)\d{2}\b', '', model_part).strip()
            model_part = re.sub(r'\s+', ' ', model_part).strip(' ,-')
            return make, model_part if model_part else 'Unknown'
    parts = title.split()
    return (parts[0] if parts else 'Unknown'), (' '.join(parts[1:]) if len(parts) > 1 else '')


def infer_vehicle_type(title, model):
    """Infer vehicle type from title/model keywords"""
    combined = f"{title} {model}".lower()
    for vtype, keywords in VEHICLE_TYPES.items():
        if any(kw in combined for kw in keywords):
            return vtype
    return 'Sedan'


def parse_price(raw):
    """Safely parse a price value to integer"""
    if not raw:
        return 0
    digits = re.sub(r'[^\d]', '', str(raw))
    return int(digits) if digits else 0


def parse_mileage(raw):
    """Safely parse mileage value"""
    if not raw:
        return None
    digits = re.sub(r'[^\d]', '', str(raw))
    return int(digits) if digits else None


def fetch_listings_page(api_key, page=1, category='cars'):
    """Fetch one page of listings from Parse.bot API.
    
    Actual response shape:
      {"status": "success", "data": {"listings": [...], "total_results": N, ...}}
    """
    headers = {'X-API-Key': api_key}
    params = {'page': page, 'category': category}
    url = f"{BASE_URL}/get_listings"
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    body = response.json()

    # Unwrap the envelope: {"status":"success","data":{"listings":[...]}}
    if isinstance(body, dict):
        if 'data' in body and isinstance(body['data'], dict):
            inner = body['data']
            for key in ('listings', 'results', 'items', 'vehicles'):
                if key in inner and isinstance(inner[key], list):
                    return inner[key]
        # Flat list at top level
        for key in ('listings', 'results', 'items', 'vehicles'):
            if key in body and isinstance(body[key], list):
                return body[key]
        # If the body itself contains a flat list value, use first list
        for v in body.values():
            if isinstance(v, list):
                return v
    elif isinstance(body, list):
        return body

    return []


def fetch_vehicles_from_api(limit=20):
    """
    Fetch vehicle data from Riyasewana via the Parse.bot API.

    Args:
        limit: Maximum number of vehicles to fetch

    Returns:
        List of vehicle dictionaries, or [] on failure
    """
    vehicles = []
    api_key = get_api_key()

    try:
        print("  Connecting to Parse.bot / Riyasewana API...")
        page = 1

        while len(vehicles) < limit:
            items = fetch_listings_page(api_key, page=page)

            if not items:
                print(f"  No items found on page {page}")
                break

            for item in items:
                if len(vehicles) >= limit:
                    break

                try:
                    # Flexible field name resolution - matches actual API response
                    title = (item.get('title') or item.get('name') or
                             item.get('listing_title') or '')
                    if not title:
                        continue

                    raw_price = (item.get('price') or item.get('price_lkr') or
                                 item.get('amount') or 0)
                    raw_mileage = (item.get('mileage') or item.get('km') or
                                   item.get('kilometers') or None)
                    city = (item.get('city') or item.get('location') or
                            item.get('district') or None)
                    fuel = (item.get('fuel') or item.get('fuel_type') or None)
                    image_url = (item.get('thumbnail') or item.get('image') or None)
                    listing_url = (item.get('url') or item.get('link') or None)

                    # Year may arrive as string "2015" from API
                    raw_year = item.get('year') or None
                    if raw_year:
                        try:
                            year = int(str(raw_year).strip())
                        except ValueError:
                            year = None
                    if not raw_year or not year:
                        m = re.search(r'\b(19|20)\d{2}\b', title)
                        year = int(m.group()) if m else 2020

                    make, model = extract_make_model(title)
                    vtype = infer_vehicle_type(title, model)

                    vehicles.append({
                        'id': len(vehicles) + 1,
                        'make': make,
                        'model': model,
                        'year': year,
                        'type': vtype,
                        'price': parse_price(raw_price),
                        'mileage': parse_mileage(raw_mileage),
                        'mpg': 25,
                        'safety_rating': 4,
                        'fuel': fuel,
                        'city': city,
                        'image_url': image_url,
                        'listing_url': listing_url,
                        'features': ['Riyasewana Listing'],
                        'description': title,
                        'source': 'Riyasewana API',
                        'scraped_at': datetime.now().isoformat(),
                    })

                except Exception:
                    continue

            # Stop if we got fewer items than expected (last page)
            if len(items) < 10:
                break
            page += 1

        print(f"  ✅ Fetched {len(vehicles)} vehicles from Parse.bot API")

    except requests.exceptions.HTTPError as e:
        print(f"  ⚠️ API HTTP error: {e.response.status_code} - {e.response.text[:120]}")
    except requests.exceptions.ConnectionError:
        print("  ⚠️ API connection failed (no internet or service down)")
    except Exception as e:
        print(f"  ⚠️ API call failed: {e}")

    return vehicles


def search_vehicles_api(make=None, model=None, min_price=None, max_price=None,
                         fuel_type=None, limit=20):
    """
    Search vehicles with filters via Parse.bot search endpoint.

    Args:
        make: Car brand (e.g., 'Toyota')
        model: Car model (e.g., 'Aqua')
        min_price: Minimum price in LKR
        max_price: Maximum price in LKR
        fuel_type: Fuel type (e.g., 'Petrol', 'Hybrid', 'Electric')
        limit: Max results

    Returns:
        List of vehicle dictionaries
    """
    api_key = get_api_key()
    headers = {'X-API-Key': api_key}
    params = {'page': 1}

    if make:
        params['make'] = make
    if model:
        params['model'] = model
    if min_price:
        params['min_price'] = min_price
    if max_price:
        params['max_price'] = max_price
    if fuel_type:
        params['fuel_type'] = fuel_type

    try:
        url = f"{BASE_URL}/search_vehicles"
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ⚠️ Search API failed: {e}")
        return []


if __name__ == '__main__':
    import sys
    import io
    # Force UTF-8 output on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("[TEST] Parse.bot API integration\n")
    cars = fetch_vehicles_from_api(limit=10)
    print(f"\n[RESULTS] {len(cars)} vehicles fetched:")
    for c in cars[:5]:
        price_str = f"Rs. {c['price']:,}" if c['price'] else "Price N/A"
        print(f"  {c['make']} {c['model']} ({c['year']}) - {price_str} [{c.get('city', '')}]")
