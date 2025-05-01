"""
Pokemon Evolution Chain Scraper

This script scrapes the Pokemon evolution chains from pokemondb.net
and saves the URLs of fully evolved Pokemon to a file.
"""

import requests
from bs4 import BeautifulSoup
from typing import Set
from pathlib import Path

# Constants
BASE_URL = "https://pokemondb.net"
EVOLUTION_URL = f"{BASE_URL}/evolution"
OUTPUT_FILE = "fully_evolved_urls.txt"

def get_soup(url: str) -> BeautifulSoup:
    """
    Fetch and parse the HTML content of a URL.
    
    Args:
        url: The URL to fetch
        
    Returns:
        BeautifulSoup object of the parsed HTML
        
    Raises:
        requests.RequestException: If the URL fetch fails
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        raise

def get_fully_evolved_urls(soup: BeautifulSoup) -> Set[str]:
    """
    Extract URLs of fully evolved Pokemon from the evolution chains.
    
    Args:
        soup: BeautifulSoup object of the evolution page
        
    Returns:
        Set of URLs for fully evolved Pokemon
    """
    fully_evolved_hrefs = set()
    
    # Find all evolution chain containers
    for evo_chain in soup.find_all("div", class_="infocard-list-evo"):
        # Get all Pokemon cards in this chain
        infocard_list = evo_chain.find_all("div", class_="infocard")
        if not infocard_list:
            continue
            
        # Get the last Pokemon in the chain (fully evolved)
        last_infocard = infocard_list[-1]
        link = last_infocard.find("a", class_="ent-name")
        
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("/pokedex/"):
                full_href = f"{BASE_URL}{href}"
                fully_evolved_hrefs.add(full_href)
    
    return fully_evolved_hrefs

def save_urls_to_file(urls: Set[str], filename: str) -> None:
    """
    Save the collected URLs to a file in sorted order.
    
    Args:
        urls: Set of URLs to save
        filename: Name of the output file
    """
    output_path = Path(filename)
    try:
        with output_path.open('w') as f:
            f.write("\n".join(sorted(urls)))
        print(f"Successfully saved {len(urls)} URLs to {filename}")
    except IOError as e:
        print(f"Error writing to {filename}: {e}")
        raise

def main() -> None:
    """Main execution function."""
    try:
        # Get and parse the evolution page
        soup = get_soup(EVOLUTION_URL)
        
        # Extract fully evolved Pokemon URLs
        fully_evolved_urls = get_fully_evolved_urls(soup)
        
        # Save URLs to file
        save_urls_to_file(fully_evolved_urls, OUTPUT_FILE)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()