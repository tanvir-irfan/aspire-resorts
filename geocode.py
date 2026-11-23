import csv
import json
import time
import urllib.parse
import urllib.request

results = []
base_url = "https://" + "nominatim.openstreetmap.org/search"

with open("raw_resorts.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row["name"].strip()
        brand = row["brand"].strip()
        
        params = urllib.parse.urlencode({
            "q": name,
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        })
        url = f"{base_url}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "AspireResortDirectory/1.0"})

        entry = {"name": name, "brand": brand, "city": "", "state": "", "country": "", "lat": None, "lng": None}
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data:
                    addr = data[0].get("address", {})
                    entry["city"] = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", "")
                    entry["state"] = addr.get("state", "")
                    entry["country"] = addr.get("country", "")
                    entry["lat"] = float(data[0]["lat"])
                    entry["lng"] = float(data[0]["lon"])
                    print(f"Found: {name} -> {entry['city']}, {entry['country']}")
                else:
                    print(f"No match: {name}")
        except Exception as e:
            print(f"Error on {name}: {e}")

        results.append(entry)
        time.sleep(1.1)  # Required 1-second delay per Nominatim usage policy

with open("hotels.json", "w", encoding="utf-8") as out:
    json.dump(results, out, indent=2, ensure_ascii=False)

print(f"Done! Saved {len(results)} resorts to hotels.json")
