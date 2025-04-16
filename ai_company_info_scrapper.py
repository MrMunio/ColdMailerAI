# ai_company_info_scrapper.py
import csv
import os
import json
from typing import List, Dict, Optional, Tuple
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import BaseMessage
from langchain_deepseek import ChatDeepSeek
import pprint

# webtools
from langchain.tools import Tool
# from utils.serper_web_search import web_search
from utils.pse_web_search import web_search
from utils.url_scrapper import scrape_page

class CompanyExtractor:
    def __init__(self, model_name: str, provider: str, api_key: Optional[str] = None):
        self.llm = self._init_llm(provider, model_name, api_key)

    def _init_llm(self, provider: str, model_name: str, api_key: Optional[str]):
        if provider == "openai":
            return ChatOpenAI(model=model_name, openai_api_key=api_key)
        elif provider == "ollama":
            return ChatOllama(model=model_name)
        elif provider == "deepseek":
            return ChatDeepSeek(model=model_name, api_key=api_key)
        elif provider == "groq":
            return ChatGroq(model=model_name, api_key=api_key)
        elif provider == "google":
            return ChatGoogleGenerativeAI(model=model_name,api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _construct_prompt(self, url_content: str,industry:str,location:str) -> List[BaseMessage]:
        prompt = [
            SystemMessage(content="You are a precise data extraction system that returns only valid JSON."),
            HumanMessage(content=f"""
        Extract company information from the following website content in markdown format.

For each company found, extract:
1. Company name
2. Services or products they offer (summarize in under 50 words)
3. Phone number
4. Email address

Instructions to task: 
- Return a JSON object with a key called "companies" containing an array of objects.
    - Each object should have the following keys: "name", "services/products", "phone", "email"
- If a piece of information is not available, use an empty string for that field but do not make up fake information.
- If multiple companies are mentioned, extract information for each of them.
- always select company which is belong to user defined industry type which is {industry} and located in {location}. 
    - do not add details of the company/institution which is not belong the same country or location or the industry type specified by user.
- do not include partial emails and phone numbers (e.g., "+1-303-699-****", [email protected], etc.). if only partial info is found, return an empty string "" instead.
here is a sample Output response:
[
{{
    "name": "TechSolutions Inc.",
    "services/products": "Cloud computing services, IT infrastructure solutions, AI-driven analytics, custom software development, and enterprise IT management.",
    "phone": "(555) 123-4567",
    "email": "info@techsolutions-example.com"
}},
{{
    "name": "GreenGrow Agricultural Services",
    "services/products": "Sustainable farming solutions and organic crop management services.",
    "phone": "",
    "email": ""
}}
]

Here is the content to analyze:

{url_content}""")
        ]

        return prompt

    def _construct_email_prompt(self, content: str, company_name: str) -> List[BaseMessage]:
        prompt = [
            SystemMessage(content="You are a precise data extraction system that returns only valid JSON."),
            HumanMessage(content=f"""
Extract the business contact email and phone number for the company named "{company_name}" using the provided search result snippets or full website content.

Instructions:
- Prioritize extracting from the official company website or links that look like legitimate company sources.
- If only partial info is found (e.g., "+1-303-699-****"), return an empty string "" instead.
- Do not generate or guess any contact details.
- Output only the business-relevant email and phone number for cold outreach.

Output Format:
{{
    "email": "example@company.com",
    "phone": "(555) 123-4567"
}}

Here is the content to analyze:

{content}
""")
        ]

        return prompt

    def extract(self, url_content: str,industry: str,location: str) -> List[Dict[str, str]]:
        messages = self._construct_prompt(url_content=url_content,industry=industry,location=location)
        response = self.llm.invoke(messages)
        print(f"LLM Extracted info: \n{response.content}\n")
        try:
            text = response.content
            start, end = text.find('['), text.rfind(']') + 1
            json_str = text[start:end] if start != -1 and end != 0 else text
            companies = json.loads(json_str)

            for c in companies:
                for k in ["name", "services/products", "phone", "email"]:
                    c.setdefault(k, "")

            return companies
        except Exception as e:
            print(f"Parsing error: {e}")
            return []

    def extract_email(self, content: str, company_name: str) -> Tuple[str, str]:
        messages = self._construct_email_prompt(content, company_name)
        response = self.llm.invoke(messages)
        try:
            text = response.content
            # Extract the JSON part
            start, end = text.find('{'), text.rfind('}') + 1
            json_str = text[start:end] if start != -1 and end != 0 else text
            data = json.loads(json_str)
            print(f"LLM Extracted email info: \n{data}\n")
            return data.get("email", ""), data.get("phone", "")
        except Exception as e:
            print(f"Email extraction error for {company_name}: {e}")
            return "", ""


class WebTools:
    @staticmethod
    def web_search(query: str, start_page: int, end_page: int,exact_term:str="") -> List[Dict[str, str]]:
        """
        Simulated web search function that would be replaced with actual implementation
        Returns a list of dictionaries with title, url, and snippet
        """
        results = web_search.run(query=query, exact_term=exact_term, start_page=start_page, end_page=end_page)
        print(f"web search query: {query}")
        print("web search results:")
        pprint.pprint(results, indent=2, width=100)
        return results

    @staticmethod
    def scrape_url(url: str) -> str:
        """
        Simulated URL scraper that would be replaced with actual implementation
        Returns the content of the page as markdown
        """
        # This is a placeholder - replace with your actual web scraping implementation
        md_text = scrape_page(url)
        print(f"Converted htmlpage to markDown format for URL: {url}")
        # In a real implementation, this would scrape the actual URL
        return f"content for {url}:\n\n{md_text}."


class CompanyScraper:
    def __init__(self, model_name: str, provider: str, api_key: Optional[str] = None):
        self.extractor = CompanyExtractor(model_name, provider, api_key)
        self.web_tools = WebTools()
        self.output_file = None
        self.total_companies_with_email = 0

    def run(self, industry: str, location: str, target_count: int) -> Tuple[str, int]:
        """
        Main orchestration function that runs the entire scraping pipeline
        """
        print(f"Starting scraper for {industry} companies in {location}, targeting {target_count} companies")
        
        # Step 1: Create output CSV file
        output_dir= "extractions"
        os.makedirs(output_dir,exist_ok=True)
        timestamp = self._get_timestamp()
        output_file_name = f"company_data_{industry}_{location}_{timestamp}.csv"
        self.output_file = os.path.join(output_dir, output_file_name)
        self._initialize_csv()
        
        # Step 2: Perform initial search
        end_page = max(1, int(target_count / 10))
        search_query = f"best {industry} in {location}" #------------------> adjust the search query
        search_results = self.web_tools.web_search(query = search_query,exact_term=location, start_page=1, end_page=end_page)
        
        # Step 3 & 4: Scrape URLs and extract company data
        companies_data = []
        for i,result in enumerate(search_results):
            url = result["url"]
            url_content = self.web_tools.scrape_url(url)
            extracted_companies = self.extractor.extract(url_content =url_content,industry=industry,location=location)
            companies_data.extend(extracted_companies)
            
            # Write email containing company data to CSV as we go
            companies_with_email = [company for company in extracted_companies if company["name"] and company["email"]]
            self._write_to_csv(companies_with_email)
            
            # Count companies with email
            self.total_companies_with_email += sum(1 for company in extracted_companies if company["email"])

            # print loop status
            print(f"\r|------stage 1 ---> scraping web URL {i+1}/{len(search_results)}-----|",end="",flush=True)

            # If we have enough companies with email, stop
            if self.total_companies_with_email >= target_count:
                print(f"\r|------stage 1 ---> process stopped early as reached target count : {self.total_companies_with_email}/{target_count} company emails-----|",end="",flush=True)
                break
        
        # Step 5: Filter companies without email
        companies_missing_email = [company for company in companies_data if company["name"] and not company["email"]]
        
        # Step 6: Second search for emails for companies missing them
        remaining_needed = target_count - self.total_companies_with_email
        if remaining_needed > 0:
            print(f"Need {remaining_needed} more companies with email. Initializing stage 2 scrapping...")
            self._find_missing_emails(companies_missing_email, remaining_needed)
        
        print(f"process completed. collected {self.total_companies_with_email} companies with email data collected")

        # Step 7: Return results
        return self.output_file, self.total_companies_with_email

    def _initialize_csv(self):
        """Initialize the CSV file with headers"""
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Services/Products", "Email", "Phone"])

    def _write_to_csv(self, companies: List[Dict[str, str]]):
        """Write companies data to CSV file"""
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for company in companies:
                writer.writerow([
                    company["name"],
                    company["services/products"],
                    company["email"],
                    company["phone"]
                ])

    def _find_missing_emails(self, companies: List[Dict[str, str]], remaining_needed: int):
        """Find emails for companies that are missing them (stage 2 extraction)"""
        for i,company in enumerate(companies):
            if remaining_needed <= 0:
                print(f"\r|------stage 2 ---> process successfully completed----|",end="",flush=True)
                break
                
            company_name = company["name"]
            location = "location"  # You would need to pass location to this function in a real implementation
            
            search_query = f"{company_name} in {location} email phone"
            search_results = self.web_tools.web_search(query=search_query, start_page=1, end_page=1)
            
            # change search result obj to llm processible string obj
            combined_content = json.dumps(search_results,indent=2)
            
            # Extract email
            print(f"\r|------stage 2 ---> processing company : {i+1}/{len(companies)}. parsing web search result for company name: {company_name}-----|",end="",flush=True)
            email, phone = self.extractor.extract_email(combined_content, company_name)
            
            if email:
                company["email"] = email
                if phone and not company["phone"]:
                    company["phone"] = phone
                    
                # Write updated company info to CSV
                self._write_to_csv([company])
                
                # Update counter
                self.total_companies_with_email += 1
                remaining_needed -= 1
                
            # If email still not found, try scraping each URL
            if not email and remaining_needed > 0:
                top_n = 2 # -----------------> adjust top n value. default is 3 to search for top n urls
                capped_search_results = search_results[:top_n]
                for j,result in enumerate(capped_search_results): # ----------------->adjust top k results value. default is 3
                    print(f"\r|------stage 2 ---> processing company : {i+1}/{len(companies)}.Email not found in search results. Executing deep URL search : {j+1}/{len(capped_search_results)} URLs -----|",end="",flush=True)
                    content = self.web_tools.scrape_url(result["url"])
                    email, phone = self.extractor.extract_email(content, company_name)
                    
                    if email:
                        company["email"] = email
                        if phone and not company["phone"]:
                            company["phone"] = phone
                        print(f"\r|------stage 2 ---> processing company : {i+1}/{len(companies)}. Deep URL search successfully completed and identified Email. -----|",end="",flush=True)    
                        # Write updated company info to CSV
                        self._write_to_csv([company])
                        
                        # Update counter
                        self.total_companies_with_email += 1
                        remaining_needed -= 1
                        break

    def _get_timestamp(self):
        """Generate a timestamp for the output file"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# Main entry point
def main():
    from dotenv import load_dotenv
    import os

    # Load environment variables from .env file
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")

    # Set variables directly here
    industry = "construction company"
    location = "colorado"
    count = 5

    # groq
    # provider = "groq"
    # model = "llama-3.2-3b-preview"

    # # openai
    # provider = "openai"
    # model = "gpt-4o-mini"

    # # groq
    # provider = "deepseek"
    # model = "deepseek-chat"

    # google
    provider = "google"
    model = "gemini-2.0-flash-lite"

    # Select the appropriate API key based on provider
    api_key = None
    if provider == "openai":
        api_key = OPENAI_API_KEY
    elif provider == "groq":
        api_key = GROQ_API_KEY
    elif provider == "deepseek":
        api_key = DEEPSEEK_API_KEY
    elif provider == "google":
        api_key = GOOGLE_AI_API_KEY

    # Initialize and run the scraper
    scrapper = CompanyScraper(model, provider, api_key)
    output_file, email_count = scrapper.run(industry, location, count)

    print(f"\nScraping completed!")
    print(f"Results saved to: {output_file}")
    print(f"Total companies with email: {email_count}")


if __name__ == "__main__":
    main()

