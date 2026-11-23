import json
import os
import time
import requests
from bs4 import BeautifulSoup

HILTON_URL = "https://hilton.com"
NOMINATIM_URL = "https://" + "nominatim.openstreetmap.org/search"
HOTELS_FILE = "hotels.json"

BRAND_MAP = {
    "waldorf astoria": "Waldorf Astoria",
    "conrad": "Conrad",
    "lxr": "LXR Hotels & Resorts",
    "signia": "Signia by Hilton",
    "curio": "Curio Collection",
    "tapestry": "Tapestry Collection",
    "hilton grand vacations": "Hilton Grand Vacations",
    "hilton vacation club": "Hilton Grand Vacations",
    "hilton club": "Hilton Grand Vacations",
    "doubletree": "DoubleTree",
    "embassy suites": "Embassy Suites",
    "hampton": "Hampton by Hilton",
    "homewood suites": "Homewood Suites",
}


def detect_brand(name, section_brand=""):
    lower_name = name.lower()
    for key, label in BRAND_MAP.items():
        if key in lower_name:
            return label
    return section_brand or "Hilton Hotels & Resorts"


def load_existing_hotels():
    if not os.path.exists(HOTELS_FILE):
        return {}
    with open(HOTELS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data}


def geocode_hotel(name):
    headers = {"User-Agent": "AspireResortDirectoryBot/1.0"}
    params = {"q": name, "format": "json", "addressdetails": 1, "limit": 1}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        results = resp.json()
        if results:
            addr = results[0].get("address", {})
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("county", "")
            )
            return {
                "city": city,
                "state": addr.get("state", ""),
                "country": addr.get("country", ""),
                "lat": float(results[0]["lat"]),
                "lng": float(results[0]["lon"]),
            }
    except Exception as e:
        print(f"Geocoding failed for {name}: {e}")
    return {"city": "", "state": "", "country": "", "lat": None, "lng": None}


def scrape_hilton_resorts():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(HILTON_URL, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    scraped = list()
    seen = set()
    current_brand = "Hilton Hotels & Resorts"

    for tag in soup.find_all(["h2", "h3", "li", "p"]):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue

        if tag.name in ["h2", "h3"]:
            for key, label in BRAND_MAP.items():
                if key in text.lower():
                    current_brand = label
                    break
            if "hilton hotels" in text.lower():
                current_brand = "Hilton Hotels & Resorts"
        elif tag.name == "li" and len(text) > 5 and len(text) < 120:
            # Filter out navigation/footer links
            if any(
                k in text.lower()
                for k in [
                    "hilton",
                    "waldorf",
                    "conrad",
                    "doubletree",
                    "embassy",
                    "hampton",
                    "homewood",
                    "curio",
                    "tapestry",
                    "lxr",
                    "signia",
                    "resort",
                    "hotel",
                    "beach",
                    "villas",
                    "club",
                ]
            ):
                if text not in seen and "resort credit" not in text.lower():
                    seen.add(text)
                    scraped.append({"name": text, "brand": detect_brand(text, current_brand)})

    return scraped


def main():
    existing = load_existing_hotels()
    scraped = scrape_hilton_resorts()

    # Safety guard: abort if Hilton blocks the request and returns too few hotels
    if len(scraped) < 200:
        print(f"Aborting update: only {len(scraped)} hotels parsed (expected 300+).")
        return

    updated_list = list()
    new_count = 0

    for item in scraped:
        name = item["name"]
        if name in existing and existing[name].get("lat") is not None:
            updated_list.append(existing[name])
        else:
            print(f"Geocoding new property: {name}")
            geo = geocode_hotel(name)
            updated_list.append({
                "name": name,
                "brand": item["brand"],
                **geo,
            })
            new_count += 1
            time.sleep(1.1)  # Respect Nominatim 1 req/sec rate limit

    updated_list.sort(key=lambda x: x["name"].lower())

    with open(HOTELS_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_list, f, indent=2, ensure_ascii=False)

    print(f"Update complete: {len(updated_list)} total resorts ({new_count} newly geocoded).")


if __name__ == "__main__":
    main()
