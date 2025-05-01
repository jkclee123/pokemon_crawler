import requests
from bs4 import BeautifulSoup

url = "https://pokemondb.net/evolution"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Find all infocard-list-evo divs
# This is where the Pokémon evolution chains are listed
infocards_list_evo = soup.find_all("div", class_="infocard-list-evo")
fully_evolved_hrefs = set()

# Iterate through each evolution chain
# and find the last Pokémon in the chain
for evo_chain in infocards_list_evo:
    infocard_list = evo_chain.find_all("div", class_="infocard")
    if not infocard_list:
        continue
    last_infocard = infocard_list[-1]
    
    # Get the href from the Pokémon's link
    link = last_infocard.find("a", class_="ent-name")
    if link and link.get("href"):
        href = link["href"]
        # Ensure the href is complete
        if href.startswith("/pokedex/"):
            full_href = f"https://pokemondb.net{href}"
            fully_evolved_hrefs.add(full_href)

# Write the fully evolved hrefs to a file
with open('fully_evolved_hrefs.txt', 'w') as f:
    for href in sorted(fully_evolved_hrefs):
        f.write(f"{href}\n")

'''
# Print the collected hrefs
for href in fully_evolved_hrefs:
    print(href)
'''