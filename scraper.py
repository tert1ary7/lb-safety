import requests
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

def clean_context(text, keyword):
    """Aggressively filters bureaucratic metadata to extract the core event."""
    # 1. Purge repetitive formatting (e.g., "Apr 17, 2026 | Lbpd Blotter - April 17, 2026 4/17/2026")
    text = re.sub(r'(?i)[a-z]{3}\s\d{1,2},?\s\d{4}', '', text)  # Purge "Apr 17, 2026"
    text = re.sub(r'(?i)lbpd\s*blotter\s*-\s*[a-z]+\s*\d{1,2},?\s*\d{4}', '', text)  # Purge "Lbpd Blotter - April 17, 2026"
    text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}', '', text)  # Purge raw dates
    text = text.replace('|', '')
    
    # 2. Isolate the operational sentence
    sentences = re.split(r'(?<=[.!?]) +|\n+', text)
    for sentence in sentences:
        if keyword in sentence.lower():
            clean = re.sub(r'\s+', ' ', sentence).strip()
            # Strip leading non-alphanumeric artifacts left by the purge
            clean = re.sub(r'^[^a-zA-Z0-9]+', '', clean)
            if not clean:
                return f"{keyword.title()} Incident"
            return clean[:85] + '...' if len(clean) > 85 else clean
            
    return f"{keyword.title()} Incident"

def update_tracker():
    base_url = 'https://longbeach.gov'
    archive_url = f'{base_url}/news-archive/?cid=6697'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print("Initiating filtered multi-vector scrape...")
    
    try:
        response = requests.get(archive_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        keywords = ['stabbing', 'shooting', 'fatal traffic', 'homicide', 'murder']
        extracted_events = []

        # Parse DOM prioritizing link extraction
        for item in soup.find_all('div', class_=re.compile('news-archive-item|list-item', re.I)):
            text = item.get_text()
            text_lower = text.lower()
            
            for kw in keywords:
                if kw in text_lower:
                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                    if date_match:
                        found_date = date_match.group(1)
                        date_obj = datetime.strptime(found_date, '%m/%d/%Y')
                        iso_date = date_obj.strftime('%Y-%m-%dT00:00:00')
                        
                        # Extract exact hyper-link for the specific blotter entry
                        item_url = archive_url
                        link_tag = item.find('a', href=True)
                        if link_tag:
                            item_url = urljoin(base_url, link_tag['href'])
                        
                        if not any(e['date'] == iso_date for e in extracted_events):
                            context = clean_context(text, kw)
                            extracted_events.append({
                                "date": iso_date,
                                "type": context.title(),
                                "url": item_url
                            })
                        break
            
            if len(extracted_events) >= 5:
                break

        if not extracted_events:
            print("No anomalies detected in current window.")
            return

        extracted_events.sort(key=lambda x: x['date'], reverse=True)
        json_data = json.dumps(extracted_events, indent=6)

        with open('index.html', 'r') as f:
            content = f.read()

        pattern = r'const incidentData = \[.*?\];'
        replacement = f'const incidentData = {json_data};'
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open('index.html', 'w') as f:
            f.write(updated_content)
        
        print("System log injected successfully.")

    except Exception as e:
        print(f"Systemic Error: {e}")
        exit(1)

if __name__ == "__main__":
    update_tracker()
