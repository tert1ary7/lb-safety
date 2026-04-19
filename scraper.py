import requests
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime

def extract_context(text, keyword):
    """Isolates the sentence or phrase containing the keyword for cleaner UI context."""
    sentences = re.split(r'(?<=[.!?]) +', text)
    for sentence in sentences:
        if keyword in sentence.lower():
            # Clean up excessive whitespace and limit length for aesthetic UI fit
            clean = re.sub(r'\s+', ' ', sentence).strip()
            return clean[:80] + '...' if len(clean) > 80 else clean
    return f"{keyword.capitalize()} Investigation"

def update_tracker():
    url = 'https://longbeach.gov/news-archive/?cid=6697'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    print("Initiating multi-vector scrape of LBPD Blotter...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        keywords = ['stabbing', 'shooting', 'fatal traffic', 'homicide', 'murder']
        extracted_events = []

        # Iterate through the DOM to build the history array
        for item in soup.find_all(['div', 'p', 'li']):
            text = item.get_text()
            text_lower = text.lower()
            
            for kw in keywords:
                if kw in text_lower:
                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                    if date_match:
                        found_date = date_match.group(1)
                        date_obj = datetime.strptime(found_date, '%m/%d/%Y')
                        iso_date = date_obj.strftime('%Y-%m-%dT00:00:00')
                        
                        # Prevent duplicates (sometimes blotter posts multiple tags for one event)
                        if not any(e['date'] == iso_date for e in extracted_events):
                            context = extract_context(text, kw)
                            extracted_events.append({
                                "date": iso_date,
                                "type": context.title() # Title case for better UI typography
                            })
                        break # Break inner loop to move to next HTML item
            
            # Cap the array at 5 historical items for visual balance
            if len(extracted_events) >= 5:
                break

        if not extracted_events:
            print("No actionable events found in current parsing window.")
            return

        # Sort chronologically, newest first (failsafe against bad HTML structuring)
        extracted_events.sort(key=lambda x: x['date'], reverse=True)
        
        # Serialize to formatted JSON string
        json_data = json.dumps(extracted_events, indent=6)

        # Inject into HTML
        with open('index.html', 'r') as f:
            content = f.read()

        # Regex targets the specific JavaScript array declaration and replaces its contents
        pattern = r'const incidentData = \[.*?\];'
        replacement = f'const incidentData = {json_data};'
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open('index.html', 'w') as f:
            f.write(updated_content)
        
        print(f"System updated. {len(extracted_events)} events written to telemetry log.")

    except Exception as e:
        print(f"Systemic Error: {e}")
        exit(1)

if __name__ == "__main__":
    update_tracker()
