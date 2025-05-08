"""
Pokemon PDF Generator (ReportLab Version)

This script generates PDF files from Pokemon web pages using ReportLab instead of WeasyPrint,
while aiming to maintain the same output appearance as the original WeasyPrint version.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import requests
from bs4 import BeautifulSoup, Tag
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, Flowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import HRFlowable
import io
from urllib.parse import urljoin

# Constants
INPUT_FILE = 'fully_evolved_urls.txt'
OUTPUT_DIR = Path('pokemon_pdfs')
BASE_URL = "https://pokemondb.net"

# Elements to skip in HTML to PDF conversion
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


class HTMLTableToReportLabTable:
    """Converts HTML tables to ReportLab Table objects."""
    
    def __init__(self, styles):
        """
        Initialize the table converter.
        
        Args:
            styles: ReportLab stylesheet to use
        """
        self.styles = styles
        
    def convert(self, table_tag: Tag) -> Optional[Table]:
        """
        Convert an HTML table to a ReportLab Table.
        
        Args:
            table_tag: The BeautifulSoup Tag representing an HTML table
            
        Returns:
            A ReportLab Table object or None if table is empty
        """
        # Extract table data
        data = []
        
        # Process all rows
        for tr in table_tag.find_all('tr'):
            row = []
            
            # Process header cells
            for th in tr.find_all('th'):
                cell_text = th.get_text(strip=True)
                row.append(Paragraph(f"<b>{cell_text}</b>", self.styles['Normal']))
                
            # Process data cells
            for td in tr.find_all('td'):
                cell_text = td.get_text(strip=True)
                row.append(Paragraph(cell_text, self.styles['Normal']))
                
            if row:
                data.append(row)
                
        if not data:
            return None
            
        # Calculate column widths (equal distribution)
        num_cols = max(len(row) for row in data)
        col_width = 6.5 * inch / num_cols
        col_widths = [col_width] * num_cols
        
        # Create table and apply basic styling
        table = Table(data, colWidths=col_widths)
        style = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]
        table.setStyle(TableStyle(style))
        
        return table


class PokemonHTMLToReportLab:
    """Converts cleaned Pokemon HTML to ReportLab flowables for PDF generation."""
    
    def __init__(self, soup: BeautifulSoup):
        """
        Initialize the converter with a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object containing the cleaned Pokemon page HTML
        """
        self.soup = soup
        
        # Create custom styles based on the standard stylesheet
        base_styles = getSampleStyleSheet()
        self.styles = {}
        
        # Copy all styles to our custom dictionary
        for style_name, style in base_styles.byName.items():
            self.styles[style_name] = style
            
        # Add custom styles
        self.styles['PokemonTitle'] = ParagraphStyle(
            'PokemonTitle',
            parent=base_styles['Title'],
            fontSize=18,
            spaceAfter=12
        )
        
        self.styles['PokemonHeading2'] = ParagraphStyle(
            'PokemonHeading2',
            parent=base_styles['Heading2'],
            fontSize=16,
            spaceAfter=10
        )
        
        self.styles['PokemonHeading3'] = ParagraphStyle(
            'PokemonHeading3',
            parent=base_styles['Heading3'],
            fontSize=14,
            spaceAfter=10
        )
        
        self.styles['PokemonHeading4'] = ParagraphStyle(
            'PokemonHeading4',
            parent=base_styles['Heading3'],
            fontSize=12,
            spaceAfter=8
        )
        
        # For move lists that should be two columns
        self.styles['MoveList'] = ParagraphStyle(
            'MoveList',
            parent=base_styles['Normal'],
            fontSize=9,
            spaceAfter=4
        )
        
        self.table_converter = HTMLTableToReportLabTable(self.styles)
    
    def convert(self) -> List[Flowable]:
        """
        Convert the cleaned HTML to ReportLab flowables.
        
        Returns:
            List of ReportLab flowables for building the PDF
        """
        elements = []
        
        # Start with the title (Pokemon name)
        title_elem = self.soup.find('h1')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            elements.append(Paragraph(title_text, self.styles['PokemonTitle']))
            elements.append(Spacer(1, 0.2 * inch))
        
        # Process main content in document order
        main_div = self.soup.find('main')
        if main_div:
            self._process_element(main_div, elements)
            
        return elements
    
    def _process_element(self, element: Tag, elements: List[Flowable]) -> None:
        """
        Process an HTML element and its children, adding flowables to the elements list.
        
        Args:
            element: BeautifulSoup Tag to process
            elements: List of flowables to append to
        """
        # Skip comments
        if isinstance(element, str) or element.name is None:
            return
            
        # Process element based on tag type
        if element.name == 'h2':
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(element.get_text(strip=True), self.styles['PokemonHeading2']))
            
        elif element.name == 'h3':
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(element.get_text(strip=True), self.styles['PokemonHeading3']))
            
        elif element.name == 'h4':
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(element.get_text(strip=True), self.styles['PokemonHeading4']))
            
        elif element.name == 'table':
            # Convert HTML table to ReportLab Table
            table = self.table_converter.convert(element)
            if table:
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(table)
                elements.append(Spacer(1, 0.1 * inch))
                
        elif element.name == 'div' and 'two-column' in element.get('class', []):
            # For two-column layout (mainly move lists)
            self._process_two_column_div(element, elements)
            
        elif element.name == 'div':
            # Regular divs - process children
            for child in element.children:
                self._process_element(child, elements)
                
        elif element.name == 'p' and element.find('img'):
            # Only process paragraphs with images (as per original cleaner)
            img_tag = element.find('img')
            if img_tag and img_tag.get('src'):
                try:
                    img_url = urljoin(BASE_URL, img_tag['src'])
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        img_data = io.BytesIO(response.content)
                        img = Image(img_data, width=100, height=100)
                        img.hAlign = 'CENTER'
                        elements.append(img)
                except Exception:
                    pass
        
        # Process other elements with children
        elif element.contents and element.name not in ['script', 'style']:
            for child in element.children:
                self._process_element(child, elements)
    
    def _process_two_column_div(self, element: Tag, elements: List[Flowable]) -> None:
        """
        Process a div that should be formatted as two columns (like move lists).
        
        Args:
            element: BeautifulSoup Tag representing a two-column div
            elements: List of flowables to append to
        """
        # Find the heading
        heading = element.find(['h3', 'h4'])
        if heading:
            elements.append(Paragraph(heading.get_text(strip=True), self.styles['PokemonHeading3']))
        
        # Find tables
        tables = element.find_all('table')
        if not tables:
            return
            
        # For simplicity, we'll put the tables one after another but with smaller fonts
        for table in tables:
            # Extract table data
            table_data = []
            for tr in table.find_all('tr'):
                row = []
                for cell in tr.find_all(['th', 'td']):
                    row.append(cell.get_text(strip=True))
                if row:
                    table_data.append(row)
            
            if not table_data:
                continue
                
            # Create a ReportLab table with small font size
            if table_data and table_data[0]:
                col_widths = [1.5*inch] * len(table_data[0])
                rl_table = Table(table_data, colWidths=col_widths)
                rl_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),  # Small font for move lists
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ]))
                elements.append(rl_table)
                elements.append(Spacer(1, 0.1 * inch))


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
                print(f"Generated PDF for {url.split('/')[-1]}")
            except Exception as e:
                print(f"An error occurred processing {url}: {e}")

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
        
        # Convert HTML to ReportLab elements
        converter = PokemonHTMLToReportLab(soup)
        elements = converter.convert()
        
        # Generate PDF
        pokemon_name = url.split('/')[-1]
        output_file = self.output_dir / f"{pokemon_name}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build the PDF
        doc.build(elements)


def main() -> None:
    """Main execution function."""
    try:
        # Read Pokemon URLs
        with open(INPUT_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        # Generate PDFs
        generator = PokemonPDFGenerator()
        generator.generate_pdfs(urls)
        
        # Report success
        print(f"PDF files are available in the '{OUTPUT_DIR}' directory.")
        
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()