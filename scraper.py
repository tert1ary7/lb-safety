import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

def update_tracker():
    url = 'https://longbeach.gov/news-archive/?cid=6697'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # The specific systemic failures we are tracking
        keywords = ['stabbing', 'shooting', 'fatal traffic', 'murder']
        latest_date_str = None

        # Parse the DOM for the most recent occurrence
        for element in soup.find_all(['p', 'div', 'li', 'a']):
            text = element.get_text().lower()
            if any(kw in text for kw in keywords):
                # Isolate the date (Format found in LBPD DOM: m/d/yyyy)
                match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', text)
                if match:
                    latest_date_str = match.group(0)
                    break 

        if latest_date_str:
            date_obj = datetime.strptime(latest_date_str, '%m/%d/%Y')
            iso_date = date_obj.strftime('%Y-%m-%dT00:00:00')

            # Inject the new reality into the front-end
            with open('index.html', 'r') as file:
                html = file.read()

            new_html = re.sub(
                r'const lastIncidentDate = new Date\(".*?"\);',
                f'const lastIncidentDate = new Date("{iso_date}");', 
                html
            )

            with open('index.html', 'w') as file:
                file.write(new_html)
                
            print(f"System updated. Last incident recorded on: {iso_date}")
        else:
            print("No matching incidents found in current parsing window.")

    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    update_tracker()
