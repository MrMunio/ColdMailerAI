# email_composer.py
from typing import List, Dict, Optional
import csv
import os
from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_deepseek import ChatDeepSeek


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
            return ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


class EmailGenerator:
    def __init__(self, model_name: str, provider: str, api_key: Optional[str] = None):
        """Initialize the cold email generator with the specified LLM."""
        self.llm = self._init_llm(provider, model_name, api_key)
        
    def _init_llm(self, provider: str, model_name: str, api_key: Optional[str]):
        """Initialize the language model based on the provider."""
        if provider == "openai":
            return ChatOpenAI(model=model_name, openai_api_key=api_key)
        elif provider == "ollama":
            return ChatOllama(model=model_name)
        elif provider == "deepseek":
            return ChatDeepSeek(model=model_name, api_key=api_key)
        elif provider == "groq":
            return ChatGroq(model=model_name, api_key=api_key)
        elif provider == "google":
            return ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def read_company_data(self, csv_file_path: str) -> List[Dict]:
        """Read company data from the CSV file."""
        company_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                company_data.append(row)
        return company_data
    
    def _construct_email_prompt(self, 
                               target_company: Dict, 
                               user_company_name: str, 
                               user_company_description: str,
                               additional_instructions: str,
                               delimiter:str="|") -> List[BaseMessage]:
        """Construct the prompt for generating a personalized cold email."""
        target_name = target_company.get('Name', '')
        target_services = target_company.get('Services/Products', '')
        
        prompt = [
            SystemMessage(content=f"""You are a business development expert writing effective, personalized cold outreach emails. Emails must be professional, concise, and value-driven—avoiding generic language or templates.

Each email should:
- Reference the recipient's specific services/products.
- Clearly explain how the sender's company can provide value.
- Include a low-pressure, clear call-to-action.
- Maintain a professional yet conversational tone.
- Avoid placeholders—use real sender and recipient details.

Provide a complete, ready-to-send email with:
- A compelling subject line to boost open rates.
- A body under 200 words, addressed naturally (e.g., “Hi” or use the company name).
- at the end DO NOT give like this place holders :
    Best regards,
    [Your Name]
    usercompany Inc.
    [Your Email]
    [Your Phone]
- at the end, insted of place holder use the info you have of user company and give like this:
    Bestg Regards,
    Team UserCompany Inc
                          
- DO NOT USE "{delimiter}" this symbol in your email subject or body. it is used as a delimiter to store subject and body in a csv file.
"""),
            
            HumanMessage(content=f"""Create a personalized cold email from {user_company_name} to {target_name}.

RECIPIENT COMPANY INFORMATION:
- Company Name: {target_name}
- Services/Products they offer: {target_services}

SENDER COMPANY INFORMATION:
- Company Name: {user_company_name}
- Company Description: {user_company_description}

ADDITIONAL INSTRUCTIONS:
{additional_instructions}

Output format should be a JSON object with these fields:
- subject: A compelling subject line that will increase open rates
- body: The personalized email body (keep it under 200 words)

The email should:
1. Specifically reference the recipient's services/products 
2. Clearly articulate how your company can provide value to them
3. Include a clear, low-pressure call-to-action
4. Be professional but conversational in tone
5. Avoid generic phrases and sales-speak""")
        ]
        return prompt
    
    def generate_email(self, 
                      target_company: Dict, 
                      user_company_name: str, 
                      user_company_description: str,
                      additional_instructions: str) -> Dict:
        """Generate a personalized email for a target company."""
        prompt = self._construct_email_prompt(
            target_company, 
            user_company_name, 
            user_company_description,
            additional_instructions
        )
        
        # Get response from the LLM
        response = self.llm.invoke(prompt)
        content = response.content
        
        # Extract JSON from response if needed
        if "{" in content and "}" in content:
            import json
            import re
            
            # Find JSON pattern in the response
            json_pattern = r'\{.*\}'
            json_match = re.search(json_pattern, content, re.DOTALL)
            
            if json_match:
                try:
                    email_content = json.loads(json_match.group())
                    return email_content
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a structured response
                    lines = content.split('\n')
                    subject_line = ""
                    body_lines = []
                    
                    in_body = False
                    for line in lines:
                        if line.lower().startswith("subject:"):
                            subject_line = line.replace("Subject:", "").strip()
                        elif line.lower().startswith("body:") or in_body:
                            in_body = True
                            if not line.lower().startswith("body:"):
                                body_lines.append(line)
                    
                    return {
                        "subject": subject_line,
                        "body": "\n".join(body_lines).strip()
                    }
        
        # If structured extraction fails, make a best guess
        parts = content.split("\n\n", 1)
        if len(parts) > 1:
            return {
                "subject": parts[0].replace("Subject:", "").strip(),
                "body": parts[1].strip()
            }
        else:
            return {
                "subject": "Partnership Opportunity",
                "body": content.strip()
            }
    
    def process_companies(self, 
                      csv_input_path: str, 
                      csv_file_name: str,
                      user_company_name: str,
                      user_company_description: str,
                      additional_instructions: str = "",
                      delimiter:str="|") -> None:
        """Process all companies and generate personalized emails."""
        # Read company data
        companies = self.read_company_data(csv_input_path)

        # Create output data structure
        output_data = []

        # Process each company
        for company in companies:
            if not company.get('Email'):
                continue
                
            email_content = self.generate_email(
                company,
                user_company_name,
                user_company_description,
                additional_instructions

            )
            
            output_data.append([
                company.get('Name', ''),
                company.get('Email', ''),
                email_content.get('subject', ''),
                email_content.get('body', '')
            ])

        # Write to CSV with custom delimiter
        output_folder_name = "composed_emails"
        os.makedirs(output_folder_name, exist_ok=True)
        csv_output_path = os.path.join(output_folder_name, csv_file_name)
        with open(csv_output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Company', 'Email', 'Subject', 'Body'])
            writer.writerows(output_data)

        print(f"✅ Generated {len(output_data)} emails and saved to {csv_output_path}")



def pretty_print_emails(csv_file_path: str, delimiter='|'):
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        for idx, row in enumerate(reader, start=1):
            print(f"\n📧 Email {idx}")
            print(f"Subject: {row['Subject']}")
            print("Body:")
            print(row['Body'])
            print("-" * 50)

def main():
    """Main function to run the email generator."""
    # # Example usage
    # model_name = "gpt-4o-mini"
    # provider = "openai"
    # api_key = os.getenv("OPENAI_API_KEY")

    # Example usage
    model_name = "gemini-2.0-flash"
    provider = "google"
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    
    # Get input and output file paths
    input_csv = r"extractions\company_data_construction company_colorado_20250407_154412.csv"
    output_csv = r"composed_emails.csv"
    
    # Get user company information
    user_company_name = "infomerica inc"
    print("Enter your company description (what capabilities/products you offer):")
    user_company_description = "Leading IT service  provider with cloud migratons, RPA, AI services, etc.."
    
    print("Enter any additional instructions for email generation (optional):")
    additional_instructions = ""

    # Initialize and run the email generator
    generator = EmailGenerator(model_name, provider, api_key)
    
    generator.process_companies(
        input_csv,
        output_csv,
        user_company_name,
        user_company_description,
        additional_instructions
    )
    # pretty_print_emails(output_csv, delimiter='|')
    import pprint
    pprint.pprint(generator.read_company_data( input_csv))




# Example usage


if __name__ == "__main__":
    main()
    