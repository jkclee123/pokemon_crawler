"""
Pokemon PDF Generator

This script generates PDF files from Pokemon web pages, applying various
formatting and styling modifications to create clean, readable documents.
"""

from typing import List
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from weasyprint import HTML

# Constants
INPUT_FILE = 'fully_evolved_urls.txt'
OUTPUT_DIR = Path('pokemon_pdfs')
CSS_STYLES = '''
<style>
    .tabset-moves-game { font-size: x-small; }
    .two-column {
        column-count: 2;
    }
    .two-column table {
        width: 100%;
    }
    .grid-col {
        height: fit-content;
    }
</style>
'''

# Selectors for elements to remove
ELEMENTS_TO_REMOVE = [
    '.sr-only', '.main-header', '.main-menu', '.entity-nav', '.list-nav',
    '.grid-col.span-md-12.span-lg-4:has(h2:-soup-contains("Training"))',
    'h2:-soup-contains("Evolution chart")', '.infocard-list-evo',
    'h2:-soup-contains("Pokédex entries")', 'footer',
    '.tabset-moves-game ~ *', '.sv-tabs-tab-list',
    '.grid-col.span-md-12.span-lg-4:has(h2:-soup-contains("Type defenses"))', 
    '.tabset-moves-game .sv-tabs-panel:not(.active):not(.tabset-moves-game-form .sv-tabs-panel)'
]

HEADERS_TO_REMOVE = ['National №', 'Height', 'Species', 'Local №']

class PokemonHTMLCleaner:
    """Handles the cleaning and formatting of Pokemon HTML content."""
    
    def __init__(self, soup: BeautifulSoup):
        """
        Initialize the cleaner with a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object containing the Pokemon page HTML
        """
        self.soup = soup

    def clean(self) -> None:
        """Apply all cleaning and formatting operations to the HTML."""
        self._remove_unwanted_elements()
        self._remove_specific_headers()
        self._remove_non_image_paragraphs()
        self._replace_move_type_icons()
        self._clean_hyperlinks()
        self._remove_changes_section()
        self._remove_pokedex_entries()
        self._resize_headings()
        self._format_move_lists()

    def _remove_unwanted_elements(self) -> None:
        """Remove elements specified in ELEMENTS_TO_REMOVE."""
        for selector in ELEMENTS_TO_REMOVE:
            for element in self.soup.select(selector):
                element.decompose()

    def _remove_specific_headers(self) -> None:
        """Remove table headers specified in HEADERS_TO_REMOVE."""
        for th in self.soup.find_all('th'):
            if th.get_text(strip=True) in HEADERS_TO_REMOVE:
                if tr := th.find_parent('tr'):
                    tr.decompose()

    def _remove_non_image_paragraphs(self) -> None:
        """Remove paragraphs that don't contain images."""
        for p in self.soup.find_all('p'):
            if not p.find('img'):
                p.decompose()

    def _replace_move_type_icons(self) -> None:
        """Replace move type icons with text."""
        icon_mappings = {
            'Physical': 'Physical',
            'Status': 'Status',
            'Special': 'Special'
        }
        for move_type, text in icon_mappings.items():
            for img in self.soup.find_all('img', title=move_type):
                img.replace_with(text)

    def _clean_hyperlinks(self) -> None:
        """Replace links with their text content."""
        for a in self.soup.find_all('a'):
            if 'ent-name' in a.get('class', []) or 'type-icon' in a.get('class', []):
                a.replace_with(a.get_text())
            elif href := a.get('href'):
                if any(term in href.lower() for term in ['tm', 'ability']):
                    a.replace_with(a.get_text())

    def _remove_changes_section(self) -> None:
        """Remove the 'Changes' section and its related elements."""
        for h2 in self.soup.find_all('h2'):
            if 'changes' in h2.get_text(strip=True).lower():
                next_elem = h2.find_next_sibling()
                while next_elem and next_elem.name == 'ul':
                    to_remove = next_elem
                    next_elem = next_elem.find_next_sibling()
                    to_remove.decompose()
                h2.decompose()

    def _remove_pokedex_entries(self) -> None:
        """Remove Pokedex entries section."""
        if dex_entries := self.soup.find('div', id='dex-flavor'):
            next_elem = dex_entries.find_next_sibling()
            while next_elem and next_elem.name in ['div', 'h3']:
                to_remove = next_elem
                next_elem = next_elem.find_next_sibling()
                to_remove.decompose()

    def _resize_headings(self) -> None:
        """Adjust heading sizes by converting h2->h3 and h3->h4."""
        for old_tag, new_tag in [('h3', 'h4'), ('h2', 'h3')]:
            for heading in self.soup.find_all(old_tag):
                new_heading = self.soup.new_tag(new_tag)
                new_heading.extend(heading.contents)
                heading.replace_with(new_heading)

    def _format_move_lists(self) -> None:
        """Format move lists into two columns."""
        for h4 in self.soup.find_all('h4'):
            if h4.get_text(strip=True).lower().startswith('moves learnt by'):
                if parent := h4.find_parent(['div', 'section']):
                    parent['class'] = parent.get('class', []) + ['two-column']

class PokemonPDFGenerator:
    """Handles the generation of Pokemon PDFs from URLs."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize the PDF generator.
        
        Args:
            output_dir: Directory where PDFs will be saved
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def generate_pdfs(self, urls: List[str]) -> None:
        """
        Generate PDFs for all provided Pokemon URLs.
        
        Args:
            urls: List of Pokemon URLs to process
        """
        for url in urls:
            try:
                self._generate_single_pdf(url)
            except Exception as e:
                print(f"An error occurred: {e}")

    def _generate_single_pdf(self, url: str) -> None:
        """
        Generate a PDF for a single Pokemon URL.
        
        Args:
            url: URL of the Pokemon page
        """
        
        # Fetch and parse HTML
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Clean and format HTML
        cleaner = PokemonHTMLCleaner(soup)
        cleaner.clean()
        
        # Generate PDF
        html_content = CSS_STYLES + str(soup)
        output_file = self.output_dir / f"{url.split('/')[-1]}.pdf"
        HTML(string=html_content).write_pdf(str(output_file))

def main() -> None:
    """Main execution function."""
    try:
        # Read Pokemon URLs
        with open(INPUT_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        # Generate PDFs
        generator = PokemonPDFGenerator()
        generator.generate_pdfs(urls)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()