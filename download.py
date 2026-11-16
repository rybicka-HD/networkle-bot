import requests
import json

BASE_URL = "https://networkle.fun/data/"
BASE_DIR = "data/"

def download(name):
    response = requests.get(BASE_URL+name)
    response.raise_for_status()

    with open(BASE_DIR+name, "wb") as f:
        f.write(response.content)

    return response.content

print("Downloading cities.json...")
cities = json.loads(download("cities.json"))

n = len(cities)
for i, city in enumerate(cities):
    if city["id"] == "london-tube": continue # no london tube map
    print(f"Downloading city {i+1}/{n} {city['id']}            ", end="\r")
    download(city["id"]+".json")

print()
