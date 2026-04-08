"""
============================================
Mandi Prices Module - Data.gov.in API
============================================
Fetches real-time commodity market prices for farmers.
Falls back to curated mock data if API is unavailable.
"""

import os
import requests
from datetime import datetime, timedelta
from database import get_database
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

MANDI_API_KEY = os.getenv("MANDI_API_KEY")
MANDI_API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"


def get_prices_collection():
    db = get_database()
    return db['mandi_prices']


# ---- Mock data for grapes (used as fallback) -----------------------
MOCK_PRICES = [
    {"commodity": "Grapes", "variety": "Thompson Seedless", "market": "Nashik", "state": "Maharashtra", "price_min": 4200, "price_max": 5800, "price_modal": 5100, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Grapes", "variety": "Bangalore Blue", "market": "Pune", "state": "Maharashtra", "price_min": 3800, "price_max": 4600, "price_modal": 4200, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Grapes", "variety": "Anab-E-Shahi", "market": "Solapur", "state": "Maharashtra", "price_min": 5200, "price_max": 7000, "price_modal": 6100, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Grapes", "variety": "Sharad Seedless", "market": "Sangli", "state": "Maharashtra", "price_min": 4800, "price_max": 6500, "price_modal": 5800, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Grapes", "variety": "Local", "market": "Kolhapur", "state": "Maharashtra", "price_min": 3200, "price_max": 4100, "price_modal": 3700, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Wheat", "variety": "Lok-1", "market": "Nagpur", "state": "Maharashtra", "price_min": 2150, "price_max": 2350, "price_modal": 2250, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Rice", "variety": "Basmati", "market": "Amravati", "state": "Maharashtra", "price_min": 3500, "price_max": 4200, "price_modal": 3850, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Onion", "variety": "Red", "market": "Lasalgaon", "state": "Maharashtra", "price_min": 800, "price_max": 1400, "price_modal": 1100, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Tomato", "variety": "Hybrid", "market": "Pune", "state": "Maharashtra", "price_min": 600, "price_max": 1300, "price_modal": 950, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Cotton", "variety": "Medium Staple", "market": "Akola", "state": "Maharashtra", "price_min": 6500, "price_max": 7200, "price_modal": 6850, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Soybean", "variety": "Yellow", "market": "Latur", "state": "Maharashtra", "price_min": 4100, "price_max": 4600, "price_modal": 4350, "unit": "Quintal", "arrival_date": ""},
    {"commodity": "Pomegranate", "variety": "Bhagwa", "market": "Solapur", "state": "Maharashtra", "price_min": 7000, "price_max": 10000, "price_modal": 8500, "unit": "Quintal", "arrival_date": ""},
]


def fetch_live_prices(commodity: str = "Grape", state: str = "Maharashtra", limit: int = 50) -> list:
    """
    Fetch live mandi prices from data.gov.in API.
    Returns mock data as fallback.
    """
    today = datetime.now().strftime("%d/%m/%Y")
    for item in MOCK_PRICES:
        item['arrival_date'] = today

    try:
        params = {
            'api-key': MANDI_API_KEY,
            'format': 'json',
            'filters[state]': state,
            'filters[commodity]': commodity,
            'limit': limit,
            'offset': 0
        }
        resp = requests.get(MANDI_API_URL, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get('records', [])
            if records:
                # Store in DB for caching
                col = get_prices_collection()
                for r in records:
                    r['fetched_at'] = datetime.utcnow()
                col.delete_many({'state': state, 'commodity': commodity})
                col.insert_many(records)
                return records
    except Exception as e:
        print(f"[WARN] Live price fetch failed, using mock: {str(e)}")

    return MOCK_PRICES


def get_prices(commodity: str = None, state: str = "Maharashtra") -> dict:
    """
    Get mandi prices - tries cache first, then live, then mock.
    """
    try:
        col = get_prices_collection()
        query = {'state': state}
        if commodity:
            query['commodity'] = {'$regex': commodity, '$options': 'i'}

        cached = list(col.find(query, {'_id': 0}).sort('price_modal', -1).limit(30))

        # If we have recent cache (within 6 hours), use it
        if cached:
            last_fetch = cached[0].get('fetched_at')
            if last_fetch and (datetime.utcnow() - last_fetch) < timedelta(hours=6):
                return {'success': True, 'source': 'cache', 'data': cached, 'total': len(cached)}

        # Try live data
        live = fetch_live_prices(commodity or "Grape", state)
        return {'success': True, 'source': 'live', 'data': live, 'total': len(live)}

    except Exception as e:
        print(f"[ERROR] get_prices: {str(e)}")
        return {'success': True, 'source': 'mock', 'data': MOCK_PRICES, 'total': len(MOCK_PRICES)}


def get_all_commodities() -> list:
    """Return list of available commodities."""
    return ["Grapes", "Wheat", "Rice", "Onion", "Tomato", "Cotton", "Soybean", "Pomegranate"]
