#import requests
from bs4 import BeautifulSoup

#URLs of Veeam documentation pages
urls = [
"https://helpcenter.veeam.com/docs/backup/vsphere/used_ports.html?ver=120",
"https://helpcenter.veeam.com/docs/backup/agents/used_ports.html?ver=120",
"https://helpcenter.veeam.com/docs/vbr/userguide/used_ports.html?ver=13"
]

def fetch_port_requirements(url):
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

#Extract port information (this part may need to be adjusted based on the actual HTML structure)
port_info = soup.find_all('table')
for table in port_info:
headers = [header.text for header in table.find_all('th')]
rows = table.find_all('tr')
for row in rows:
columns = row.find_all('td')
if columns:
print(dict(zip(headers, [col.text for col in columns])))

#Fetch and display port requirements from each URL
for url in urls:
fetch_port_requirements(url)
