# utils/pse_web_search.py
from typing import Optional
from langchain.tools import Tool
import requests
import json

class WebSearch:
    def __init__(
        self,
        pse_api_key: str,
        pse_cx: str,
    ):
        self.pse_api_key = pse_api_key
        self.pse_cx = pse_cx

    def run(self, query: str, exact_term:str="", start_page: int = 1, end_page: int = 1,) -> str:
        all_results = []
        for page in range(start_page, end_page + 1):
            start = 1 + (page - 1) * 10
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.pse_api_key}&cx={self.pse_cx}&start={start}&key={exact_term}"
            response = requests.get(url)
            data = response.json()
            
            # print error if exitsts
            if "error" in data:
                if data['error']['message']:
                    print(f"Error in google PSE search api: {data['error']['message']}")
                
            items = data.get("items", [])
            for item in items:
                all_results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", "")
                })
        return all_results



# initalize the web search tool with your API keys
import os
from dotenv import load_dotenv
load_dotenv()
pse_api_key = os.getenv("PSE_API_KEY")
pse_cx = os.getenv("PSE_ENGINE_ID")
web_search = WebSearch(pse_api_key=pse_api_key, pse_cx=pse_cx)
if __name__=="__main__":
    query = "best construction company in hyderabad"
    exact_term = "hyderabad"
    results=web_search.run(query = query,exact_term = "hyderabad",start_page=3,end_page=3)

    from pprint import pprint
    pprint(results)



