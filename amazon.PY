#!/usr/bin/env python3
"""Fast Amazon Product Scraper - Optimized for speed"""

import asyncio
import math
import textwrap
import json
from typing import List, Tuple
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from tabulate import tabulate
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


async def fetch_html(url: str, page_num: int) -> str:
    """Fetch HTML using Playwright with stealth settings."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
        )
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
        """)

        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Quick scroll for lazy loading
            await page.mouse.wheel(0, 1500)
            await page.wait_for_timeout(800)
            
            html = await page.content()
            return html
            
        except Exception as e:
            print(f"Error on page {page_num}: {e}")
            return ""
        finally:
            await browser.close()


def get_next_page_url(url: str, page_num: int) -> str:
    """Generate next page URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params['page'] = [str(page_num)]
    new_query = urlencode(params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def extract_products(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    """Extract products from page."""
    products = []
    
    # Try multiple selectors to catch all products
    selectors = [
        "div[data-component-type='s-search-result']",
        "div.s-result-item[data-asin]",
        "div.puis-card-container",
        "div[data-asin]:not([data-asin=''])"
    ]
    
    product_elements = []
    for selector in selectors:
        product_elements = soup.select(selector)
        if product_elements:
            break
    
    for product in product_elements:
        # Get ASIN to ensure it's a real product
        asin = product.get('data-asin', '')
        if not asin or len(asin) < 10:
            continue
        
        # Get title - try multiple selectors
        name = None
        title_selectors = [
            "h2 a span",
            "h2 span.a-text-normal",
            "a span.a-text-normal",
            "h2.a-size-mini a span",
            ".a-color-base.a-text-normal"
        ]
        for sel in title_selectors:
            title_elem = product.select_one(sel)
            if title_elem:
                name = title_elem.get_text(strip=True)
                if name and len(name) > 5:
                    break
        
        if not name:
            continue
        
        # Get price
        price = "N/A"
        price_selectors = [
            "span.a-price-whole",
            "span.a-price .a-offscreen",
            ".a-price .a-offscreen",
            "span.a-color-price"
        ]
        for sel in price_selectors:
            price_elem = product.select_one(sel)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if price_text and any(c.isdigit() for c in price_text):
                    price = price_text
                    break
        
        # Get rating
        rating = "N/A"
        rating_selectors = [
            "span.a-icon-alt",
            "i.a-icon-star-small span",
            ".a-icon-star span",
            "span[aria-label*='star']"
        ]
        for sel in rating_selectors:
            rating_elem = product.select_one(sel)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True) or rating_elem.get('aria-label', '')
                if rating_text and ('star' in rating_text.lower() or 'out of' in rating_text):
                    rating = rating_text
                    break
        
        products.append((name, price, rating))
    
    return products


async def scrape_amazon(url: str, num_products: int):
    """Main scraping function."""
    all_products = []
    max_pages = math.ceil(num_products / 60) + 1
    
    print(f"Scraping {num_products} products...\n")
    
    for page_num in range(1, max_pages + 1):
        current_url = url if page_num == 1 else get_next_page_url(url, page_num)
        
        html = await fetch_html(current_url, page_num)
        if not html:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        page_products = extract_products(soup)
        
        if not page_products:
            break
        
        remaining = num_products - len(all_products)
        all_products.extend(page_products[:remaining])
        
        print(f"Page {page_num}: {len(all_products)}/{num_products} products")
        
        if len(all_products) >= num_products:
            break
        
        await asyncio.sleep(1.5)
    
    # Save to JSON for AI processing
    products_data = {
        "total_products": len(all_products),
        "source_url": url,
        "pages_scraped": page_num,
        "products": [
            {
                "id": i,
                "name": name,
                "price": price,
                "rating": rating
            }
            for i, (name, price, rating) in enumerate(all_products[:num_products], 1)
        ]
    }
    
    with open('amazon_products2.json', 'w', encoding='utf-8') as f:
        json.dump(products_data, f, indent=2, ensure_ascii=False)
    
    # Display results
    print(f"\n{'='*80}\n")
    
    table_data = []
    for i, (name, price, rating) in enumerate(all_products[:num_products], 1):
        wrapped_name = "\n".join(textwrap.wrap(name, width=60))
        table_data.append([i, wrapped_name, price, rating])
    
    print(tabulate(table_data, headers=["#", "Product", "Price", "Rating"], 
                   tablefmt="grid", stralign="left"))
    print(f"\n{'='*80}")
    print(f"Total: {len(all_products)} products from {page_num} page(s)")
    print(f"Saved to: amazon_products2.json")


async def main():
    url = input("Amazon URL: ").strip()
    try:
        num = int(input("Number of products: ").strip())
        if num <= 0:
            print("Enter a positive number")
            return
        await scrape_amazon(url, num)
    except ValueError:
        print("Invalid number")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled")
    except Exception as e:
        print(f"Error: {e}")