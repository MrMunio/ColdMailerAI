import os
import requests
from typing import Optional
from dotenv import load_dotenv

class WebSearch:
    def __init__(self, serper_api_key: str):
        self.serper_api_key = serper_api_key
        self.api_url = "https://google.serper.dev/search"

    def run(self, query: str, exact_term: str = "", start_page: int = 1, end_page: int = 1) -> list:
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        all_results = []
        for page in range(start_page, end_page + 1):
            search_query = f'{query} in {exact_term}' if exact_term else query
            payload = {
                "q": search_query,
                "page": page
            }
            response = requests.post(self.api_url, headers=headers, json=payload)
            data = response.json()

            if "error" in data:
                print(f"Error in Serper API: {data['error']}")
                continue

            for item in data.get("organic", []):
                all_results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", "")
                })

        return all_results

# Load Serper API key
load_dotenv()
serper_api_key = os.getenv("SERPER_API_KEY")
web_search = WebSearch(serper_api_key=serper_api_key)

# Test
if __name__ == "__main__":
    results = web_search.run(query="best construction company", exact_term="hyderabad", start_page=1, end_page=1)
    from pprint import pprint
    pprint(results)
