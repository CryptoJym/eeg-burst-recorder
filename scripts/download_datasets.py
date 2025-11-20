#!/usr/bin/env python3
"""
Dataset Downloader
------------------
Attempts to download sample data for the Gold Standard validation.
1. Nature 2025 (Figshare): "Phase Speech Acoustic Clean EEG Dataset"
2. ICASSP 2023: Checks for availability (often requires login/form).

Usage: python scripts/download_datasets.py
"""

import os
import sys
import requests
import logging
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Downloader")

# Figshare Article ID for "Phase Speech Acoustic Clean EEG Dataset"
# Based on search: "Speech prediction of a listener via EEG-based classification"
# We will use the public API to find the files.
FIGSHARE_ARTICLE_ID = "26838352" # Found via search for the paper title on Figshare
# Note: If ID is incorrect, script will search.

DATA_ROOT = Path("data")

def download_file(url, dest_path):
    """Download a file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(dest_path, 'wb') as file, tqdm(
        desc=dest_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            size = file.write(data)
            bar.update(size)

def fetch_nature_2025_sample():
    """Attempt to download a sample from Figshare"""
    logger.info("🔍 Searching Figshare for Nature 2025 dataset...")
    
    # 1. Search for the article if ID is not certain, or use known ID
    # We'll try a search first to be robust
    search_url = "https://api.figshare.com/v2/articles/search"
    search_data = {
        "search_for": "Speech prediction of a listener via EEG-based classification",
        "limit": 1
    }
    
    try:
        r = requests.post(search_url, json=search_data)
        results = r.json()
        
        if not results:
            logger.warning("⚠️ Could not find dataset on Figshare via search.")
            return
            
        article_id = results[0]['id']
        logger.info(f"✓ Found Article ID: {article_id}")
        
        # 2. Get file list
        files_url = f"https://api.figshare.com/v2/articles/{article_id}/files"
        r_files = requests.get(files_url)
        files = r_files.json()
        
        if not files:
            logger.warning("⚠️ No files found in article.")
            return
            
        # 3. Download the smallest file as a sample (likely a description or single subject)
        # Sort by size
        files.sort(key=lambda x: x['size'])
        target_file = files[0] # Smallest file
        
        download_url = target_file['download_url']
        filename = target_file['name']
        dest = DATA_ROOT / "nature_2025" / filename
        
        logger.info(f"⬇️ Downloading sample: {filename} ({target_file['size'] / 1024 / 1024:.2f} MB)")
        download_file(download_url, dest)
        logger.info("✅ Download complete.")
        
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")

def main():
    logger.info("=== Dataset Downloader ===")
    
    # Ensure requests is installed
    try:
        import requests
    except ImportError:
        logger.error("requests library not found. Please run: pip install requests tqdm")
        return

    fetch_nature_2025_sample()
    
    logger.info("\nNote: ICASSP 2023 data often requires a challenge login.")
    logger.info("Please manually place large files in data/icassp_2023/ if needed.")

if __name__ == "__main__":
    main()
