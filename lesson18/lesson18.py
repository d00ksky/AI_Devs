import json
import re
import requests
import openai
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from queue import PriorityQueue, Queue
import logging

import urllib3

logging.basicConfig(level=logging.INFO)

load_dotenv()

KLUCZ=os.getenv("KLUCZ")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY2")
REPORT_URL=os.getenv("REPORT_URL")
PYTANIA_Z_CENTRALI=os.getenv("PYTANIA_Z_CENTRALI")
SOFTOAI=os.getenv("SOFTOAI")


client = openai.OpenAI(api_key=OPENAI_API_KEY)

questions=requests.get(f"{PYTANIA_Z_CENTRALI}").json()
print(questions)

"""
!Answer format:
{
    "01": "zwięzła i konkretna odpowiedź na pierwsze pytanie",
    "02": "zwięzła i konkretna odpowiedź na drugie pytanie",
    "03": "zwięzła i konkretna odpowiedź na trzecie pytanie"
}

"""

visited_urls = set()
url_queue = Queue()
knowledge_base = {}

def scrape_page(url):
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.content, "html.parser")

        #extract content from html
        content = soup.get_text(separator="\n").strip()

        #extract links from html
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        links = set()
        for tag in soup.find_all("a", href=True):
            href = tag.get('href')
            full_url = urljoin(base_url, href)
            links.add(full_url)
        
        return content, links
    except Exception as e:
        logging.error(f"Error scraping page {url}: {e}")
        return None, set()


answers = {
    "01": None,  # Email address
    "02": None,  # Web interface URL
    "03": None   # ISO certifications
}



def analyze_content_with_openai(content, current_url):
    """Sends content to OpenAI and retrieves recommended URLs."""
    try:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {"role": "system", "content": """You are a web crawler helper. Your response must be a valid JSON object with exactly these fields:
                {
                    "found_answers": {
                        "01": null or "answer if found",
                        "02": null or "answer if found",
                        "03": null or "answer if found"
                    },
                    "next_urls": ["url1", "url2", ...],
                    "reasoning": "why these URLs might contain answers"
                }
                Do not include any other text outside the JSON structure. For next_urls, only include URLs found in the content. That could contain answers."""},
                {"role": "user", "content": f"""
                Questions to answer:
                01: {questions['01']}
                02: {questions['02']}
                03: {questions['03']}
                
                Current answers: {answers}
                
                
                Current URL: {current_url}
                Content to analyze: {content}
                Do you think that content contains any of the answers? Do you see link to web interface for robots in content? Do you think current page is interface for robots? If yes provide only it's url in answer 02.

                visited_urls: {visited_urls}
            """}
            ],
            response_format={"type": "json_object"}
        )
        
        
        # Get response content and ensure it's not None
        response_content = response.choices[0].message.content
        #print(response_content)
        if response_content is None:
            logging.error("OpenAI returned None response")
            return []
        
        
        # Parse JSON response
        try:
            result = json.loads(response_content)
            
            # Update answers with any new findings
            for key, value in result['found_answers'].items():
                if value and not answers[key]:
                    answers[key] = value
                    logging.info(f"Found answer for {key}: {value}")
            
            return result['next_urls']
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse OpenAI response: {e}")
            return []
            
    except Exception as e:
        logging.error(f"Error in OpenAI request: {e}")
        return []



def is_valid_url(url):
    """Filter out likely honeypot URLs"""
    parsed = urlparse(url)
    if 'loop' in parsed.path.lower():
        return False
    if re.search(r'\d+$', parsed.path):  
        return False
    return True




def main(seed_url, max_depth=4):
    """Main crawler function with intelligent URL selection."""
    url_queue = PriorityQueue()
    url_queue.put((0, seed_url))  # (Depth, URL)

    while not url_queue.empty():
        _, current_url = url_queue.get()

        if current_url in visited_urls or not is_valid_url(current_url):
            continue

        logging.info(f"Scraping: {current_url}")
        visited_urls.add(current_url)

        # Scrape the page
        content, links = scrape_page(current_url)

        if not content:
            continue

        # Get next URLs from OpenAI analysis
        suggested_urls = analyze_content_with_openai(content, current_url)

        # Check if we found all answers
        if all(answers.values()):
            logging.info("All answers found!")
            break

        # Add suggested URLs with higher priority
        for url in suggested_urls:
            if url not in visited_urls:
                url_queue.put((0, url))  # Priority 0 for AI-suggested URLs


        # Add discovered links with lower priority
        for url in links:
            if url not in visited_urls:
                url_queue.put((1, url))  # Priority 1 for regular links


def report_answers():
    answers_array = {}
    for question in questions:
        answers_array[question] = answers[question]
    
    """Reports answers to the report URL."""
    data = {
        "task": "softo",
        "apikey": KLUCZ,
        "answer": answers_array
    }
    response = requests.post(f"{REPORT_URL}", json=data)
    print(answers_array)
    print(response.json())


if __name__ == "__main__":
    seed_url = SOFTOAI
    main(seed_url)
    report_answers()



