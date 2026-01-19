## Amazon & Flipkart Web Scraper

This repository contains web scraping scripts for **Amazon** and **Flipkart**.

### Amazon Scraper
- Built using **Playwright** for browser automation
- Uses **BeautifulSoup (BS4)** for DOM parsing
- Data is extracted using **CSS selectors**
- Works on rendered HTML (dynamic content)

⚠️ **Note:**  
Amazon frequently changes its DOM structure.  
Because of this, **CSS selectors may expire over time** and must be updated periodically to keep the script working.

### Flipkart Scraper
- Uses **request-based scraping**
- No browser automation required
- Faster and lightweight
- Works only on supported request endpoints

### Status
- ✅ Both scripts are **working**
- ✅ Both scripts are **tested**

This project is intended for learning and educational purposes.
