import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
import time

URL = "https://www.flipkart.com/search?q=mobiles&as=on&as-show=on&otracker=AS_Query_TrendingAutoSuggest_1_0_na_na_na&otracker1=AS_Query_TrendingAutoSuggest_1_0_na_na_na&as-pos=1&as-type=TRENDING&suggestionId=mobiles&requestId=7d1bdabf-7016-4dcf-989e-1ebcad879418"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
products_data = []

page = 1

while len(products_data) < 100:
    print(f"Scraping page {page}...")

    response = requests.get(URL + f"&page={page}", headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    products = soup.select("div.nZIRY7")

    if not products:
        break

    for p in products:
        if len(products_data) >= 100:
            break

        name = p.select_one("div.RG5Slk")
        price = p.select_one("div.hZ3P6w.DeU9vF")
        rating = p.select_one("div.MKiFS6")
        rating_count = p.select_one("span.PvbNMB")
        specs = p.select("ul.HwRTzP li.DTBslk")
        offer = p.select_one("div.HQe8jr span")

        if not name or not price:
            continue

        products_data.append([
            name.text[:45].strip(),
            rating.text.strip() if rating else "N/A",
            rating_count.text.strip() if rating_count else "N/A",
            price.text.strip(),
            offer.text.strip() if offer else "N/A"
        ])

    page += 1
    time.sleep(1)  # polite delay

# 📊 Print table in terminal
headers = [
    "Product Name",
    "Rating",
    "Ratings & Reviews",
    "Key Specs",
    "Price",
    "Offer"
]

print("\nFLIPKART MOBILE PRODUCTS (TOP 100)\n")
print(tabulate(products_data, headers=headers, tablefmt="grid"))
