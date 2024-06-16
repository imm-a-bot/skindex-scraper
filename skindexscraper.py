import json
import os
import functools
import cloudscraper
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

from config import SKINS_PATH, SKINDEX_URL

def run_until_complete(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        attempts = 0
        while True:
            attempts += 1
            print(f"Attempt {attempts}")
            output = func(*args, **kwargs)
            if output:
                return output
    return wrapper

@run_until_complete
def get_skin_urls(page):
    scraper = cloudscraper.create_scraper()
    
    page_url = f"{SKINDEX_URL}/{page}/"
    response = scraper.get(page_url)
    
    if response.status_code != 200:
        print(f"Failed to get skin urls Status Code {response.status_code}")
        return []
 
    skindex_page = BeautifulSoup(response.content, "html.parser")
    links = skindex_page.find_all("a")
    skin_urls = []
    
    for link in links:
        skin_endpoint = link.get("href")
        if "/skin/" not in skin_endpoint:
            continue
        if "/#comments" in skin_endpoint:
            continue
        skin_url = f"{SKINDEX_URL}{skin_endpoint}"
        skin_urls.append(skin_url)
    print("Got skin urls")
    return skin_urls

@run_until_complete
def get_download_url(skin_url):
    scraper = cloudscraper.create_scraper()
    response = scraper.get(skin_url)
    if response.status_code != 200:
        print(f"Failed to get {skin_url} Status Code {response.status_code}")
        return ""
 
    skindex_page = BeautifulSoup(response.content, "html.parser")
    links = skindex_page.find_all("a")
    
    try:
        download_endpoint = next(link.get("href") for link in links if "/download" in link.get("href"))
        download_url = SKINDEX_URL + download_endpoint
       
        return download_url
    except Exception as e:
        print(f"Failed to get {skin_url} Exception {e}")
        return ""

@run_until_complete
def get_skin_image(download_url):
    scraper = cloudscraper.create_scraper()
    
    response = scraper.get(download_url)
    
    if response.status_code != 200:
        print(f"Failed to download {download_url} Status Code {response.status_code}")
        return None
    
    image = Image.open(BytesIO(response.content))
    
    return image
    
def save_page(page):
    cached_image_paths = os.listdir(SKINS_PATH)
    skin_urls = get_skin_urls(page)
    for skin_url in skin_urls:
        skin_id = skin_url[skin_url.index("skin/") + 5:-1]
        skin_id = skin_id[0:skin_id.index("/")]
        image_path = f"{skin_id}.png"
        
        if image_path in cached_image_paths:
            continue
        cached_image_paths.append(image_path)
            
        download_url = get_download_url(skin_url)
           
        image = get_skin_image(download_url)

        image.save(SKINS_PATH + image_path)
            
