# pokemon_crawler

## Features

- Scrapes the Pokemon evolution chains from pokemondb.net
- Extracts URLs of fully evolved Pokemon
- Generates clean, formatted PDF files for each Pokemon
- Customizes PDF layout with proper styling and formatting

## Requirements

- Python 3.13
- BeautifulSoup4
- Requests
- WeasyPrint

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pokemon_crawler.git
   cd pokemon_crawler
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install requests beautifulsoup4 weasyprint
   ```

## Usage

1. First, collect the URLs of fully evolved Pokemon:
   ```
   python get_links.py
   ```
   This will create a file named `fully_evolved_urls.txt` containing the URLs.

2. Generate PDF files for each Pokemon:
   ```
   python write_pdf.py
   ```
   The PDFs will be saved in the `pokemon_pdfs` directory.

## Project Structure

- `get_links.py`: Scrapes Pokemon evolution chains and extracts fully evolved Pokemon URLs
- `write_pdf.py`: Generates formatted PDF files from the Pokemon web pages
- `fully_evolved_urls.txt`: List of URLs for fully evolved Pokemon
- `pokemon_pdfs/`: Directory where generated PDFs are stored
