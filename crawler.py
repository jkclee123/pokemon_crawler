import requests
from bs4 import BeautifulSoup
from weasyprint import HTML

to_remove_list = ['.sr-only', '.main-header', '.main-menu', '.entity-nav', '.list-nav', '.grid-col.span-md-12.span-lg-4:has(h2:-soup-contains("Training"))', 'h2:-soup-contains("Evolution chart")', '.infocard-list-evo', 'h2:-soup-contains("Pokédex entries")', 'footer', '.tabset-moves-game ~ *', '.sv-tabs-tab-list', '.grid-col.span-md-12.span-lg-4:has(h2:-soup-contains("Type defenses"))']
def general_remove(soup):
    for to_remove in to_remove_list:
        for section in soup.select(to_remove):
            section.decompose()


headers_to_remove = ['National №', 'Height', 'Species', 'Local №']
def remove_headers_from_data(soup):
    # Remove table rows with specific headers
    for th in soup.find_all('th'):
        if th.get_text(strip=True) in headers_to_remove:
            tr = th.find_parent('tr')
            if tr:
                tr.decompose()

def remove_paragraphs(soup):
    # Remove paragraphs that don't contain images
    for p in soup.find_all('p'):
        if not p.find('img'):
            p.decompose()

def replace_skilltype_icon(soup):
    # Replace images with text
    for img in soup.find_all('img', title='Physical'):
        img.replace_with('Physical')
    for img in soup.find_all('img', title='Status'):
        img.replace_with('Status')
    for img in soup.find_all('img', title='Special'):
        img.replace_with('Special')

def replace_hyperlink(soup):
    # Replace links with their text
    for a in soup.find_all('a', class_='ent-name'):
        a.replace_with(a.get_text())
    for a in soup.find_all('a', class_='type-icon'):
        a.replace_with(a.get_text())
    for a in soup.find_all('a'):
        if a.get('href'):
            if 'tm' in a.get('href').lower() or 'ability' in a.get('href').lower():
                a.replace_with(a.get_text())

def remove_changes(soup):
    # Remove the h2 with text 'Changes' and all following ul siblings
    for h2 in soup.find_all('h2'):
        if 'changes' in h2.get_text(strip=True):
            # Remove all following ul siblings
            next_sibling = h2.find_next_sibling()
            while next_sibling and next_sibling.name == 'ul':
                to_remove = next_sibling
                next_sibling = next_sibling.find_next_sibling()
                to_remove.decompose()
            h2.decompose()

def remove_pokedex_entries(soup):
    dex_entries = soup.find('div', id='dex-flavor')
    next_sibling = dex_entries.find_next_sibling()
    while next_sibling and (next_sibling.name == 'div' or next_sibling.name == 'h3'):
        to_remove = next_sibling
        next_sibling = next_sibling.find_next_sibling()
        to_remove.decompose()

def resize_title(soup):
    for h3 in soup.find_all('h3'):
        h4 = soup.new_tag('h4')
        h4.extend(h3.contents)
        h3.replace_with(h4)
    for h2 in soup.find_all('h2'):
        h3 = soup.new_tag('h3')
        h3.extend(h2.contents)
        h2.replace_with(h3)

def moves_two_column(soup): 
    for h4 in soup.find_all('h4'):
        if h4.get_text(strip=True).lower().startswith('moves learnt by'):
            parent = h4.find_parent(['div', 'section'])
            if parent:
                parent['class'] = parent.get('class', []) + ['two-column']


def main():
    # Read the fully evolved hrefs from file
    with open('fully_evolved_hrefs.txt', 'r') as f:
        fully_evolved_hrefs = [line.strip() for line in f]

    for url in fully_evolved_hrefs:
        # Send a request to the webpage
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        general_remove(soup)
        remove_headers_from_data(soup)
        remove_paragraphs(soup)
        replace_skilltype_icon(soup)
        replace_hyperlink(soup)
        remove_changes(soup)
        remove_pokedex_entries(soup)
        resize_title(soup)
        moves_two_column(soup)

        # Convert the modified HTML to PDF
        style = '''<style>
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
        html_content = style + str(soup)
        name = url.split('/')[-1]
        HTML(string=html_content).write_pdf(f'{name}.pdf')

if __name__ == "__main__":
    main()