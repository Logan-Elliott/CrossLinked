# file path: src/optimized_crosslinked.py

import logging
import asyncio
import aiohttp
import random
import time
from random import choice
from bs4 import BeautifulSoup
from unidecode import unidecode
from urllib.parse import urlparse
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    filename="crosslinked_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# List of User-Agent strings for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12.5; rv:104.0) Gecko/20100101 Firefox/104.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    # Add more User-Agents as needed
]

# List of proxies to rotate
PROXIES = [
    "http://proxy1:port",
    "http://proxy2:port",
    "http://proxy3:port"
]

# Introduce random sleep between 1 and 5 seconds between requests
time.sleep(random.uniform(1, 5))

# Function to get a random User-Agent
def get_random_user_agent():
    return {"User-Agent": choice(USER_AGENTS)}

# Function to get a random proxy
def get_random_proxy(proxies):
    if proxies:
        proxy = choice(proxies)
        return {"http": proxy, "https": proxy}
    return None

# Function to make web requests
async def web_request(url, timeout, headers, proxies):
    proxy_settings = get_random_proxy(proxies)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy_settings.get('http') if proxy_settings else None, timeout=timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    return html
                else:
                    logging.warning(f"Non-200 response: {response.status} for URL: {url}")
                    return None
    except Exception as e:
        logging.error(f"Request failed for URL: {url} with error: {e}")
        return None

# Class for handling searches
class CrossLinked:
    def __init__(self, search_engine, target, timeout, conn_timeout=3, proxies=None, jitter=0):
        self.results = []
        self.url_templates = {
            'google': 'https://www.google.com/search?q=site:linkedin.com/in+"{}"&num=100&start={}',
            'bing': 'http://www.bing.com/search?q="{}"+site:linkedin.com/in&first={}',
            'duckduckgo': 'https://duckduckgo.com/html?q="{}"+site:linkedin.com/in'
        }
        self.search_engine = search_engine
        self.target = target
        self.timeout = timeout
        self.conn_timeout = conn_timeout
        self.proxies = proxies if proxies else []
        self.jitter = jitter

    async def search(self):
        for page in range(0, 300, 10):  # Adjust the range and step as needed
            url = self.url_templates[self.search_engine].format(self.target, page)
            headers = get_random_user_agent()
            html = await web_request(url, self.timeout, headers, self.proxies)
            if html:
                self.page_parser(html)
                await asyncio.sleep(random.uniform(1, 5))  # Add random delay between requests

    def page_parser(self, html):
        soup = BeautifulSoup(html, "lxml")
        links = soup.find_all("a")
        if not links:
            print("No links found on the page.")  # Add debugging output
        for link in links:
            self.results_handler(link)

    def results_handler(self, link):
        url = str(link.get('href')).lower()
        if not urlparse(url).netloc.endswith('linkedin.com') or 'linkedin.com/in' not in url:
            return
        data = self.link_parser(url, link)
        if data['name']:
            self.log_results(data)

    def link_parser(self, url, link):
        u = {'url': url}
        u['text'] = unidecode(link.text.split("|")[0].split("...")[0])
        u['title'] = self.parse_linkedin_title(u['text'])
        u['name'] = self.parse_linkedin_name(u['text'])
        return u

    def parse_linkedin_title(self, data):
        try:
            return data.split("-")[1].split('https:')[0].split("...")[0].split("|")[0].strip()
        except:
            return 'N/A'

    def parse_linkedin_name(self, data):
        try:
            return unidecode(data.split("-")[0].strip()).lower()
        except:
            return False

    def log_results(self, d):
        if d not in self.results and 'linkedin.com' not in d['name']:
            self.results.append(d)
            logging.info(f"Verified name: {d['name']} | Title: {d['title']} | URL: {d['url']}")

# Main function to run the search
async def main():
    target = "Target Organization"
    search = CrossLinked(search_engine="duckduckgo", target=target, timeout=10, proxies=PROXIES)
    await search.search()
    print("Verified Results:", search.results)

# Run the main function
asyncio.run(main())
