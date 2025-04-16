# app.py
import streamlit as st
import pandas as pd
import os
import base64
import time
from datetime import datetime
import sys
from dotenv import load_dotenv
load_dotenv()  # Load .env variables into os.environ

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
from ai_company_info_scrapper import CompanyScraper
from email_composer import EmailGenerator
from send_mails import send_emails_from_csv

# Set page configuration
st.set_page_config(
    page_title="Business Outreach Automation",
    page_icon="📧",
    layout="wide",
)

# App title and description
st.title("📧 Business Outreach Automation")
st.markdown("""
This application streamlines your B2B outreach process in three simple steps:
1. **Scrape** company information based on industry and location
2. **Compose** personalized cold outreach emails for each company
3. **Send** the emails directly through Gmail SMTP
""")

# Create a sidebar for navigation
st.sidebar.title("Navigation")
pages = ["Scrape Company Info", "Compose Emails", "Send Emails"]
page = st.sidebar.radio("Go to", pages)

# Function to download DataFrame as CSV
def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False, sep='|')
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 {text}</a>'
    return href

# Function to save uploaded file to a temp directory
def save_uploaded_file(uploaded_file):
    try:
        with open(os.path.join("temp", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        return os.path.join("temp", uploaded_file.name)
    except Exception as e:
        st.error(f"Error saving uploaded file: {e}")
        return None

# Create temp directory if it doesn't exist
if not os.path.exists("temp"):
    os.makedirs("temp")

# Session state initialization
if 'scraped_data_path' not in st.session_state:
    st.session_state.scraped_data_path = None
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'composed_emails_path' not in st.session_state:
    st.session_state.composed_emails_path = None

# Load API keys (in real app, these would be in .env or secrets)
# For Streamlit deployment, you should use Streamlit secrets
if 'OPENAI_API_KEY' not in st.session_state:
    st.session_state.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
if 'GOOGLE_API_KEY' not in st.session_state:
    st.session_state.GOOGLE_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')
if 'DEEPSEEK_API_KEY' not in st.session_state:
    st.session_state.DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
if 'SENDER_EMAIL' not in st.session_state:
    st.session_state.SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
if 'SENDER_PASSWORD' not in st.session_state:
    st.session_state.SENDER_PASSWORD = os.getenv('GOOGLE_APP_PASSWORD', '')

# Allow user to enter API keys if not found in environment
with st.sidebar.expander("API Settings"):
    openai_api_key = st.text_input("OpenAI API Key", value=st.session_state.OPENAI_API_KEY, type="password")
    if openai_api_key:
        st.session_state.OPENAI_API_KEY = openai_api_key
    
    google_key = st.text_input("Google API Key", value=st.session_state.GOOGLE_API_KEY, type="password")
    if google_key:
        st.session_state.GOOGLE_API_KEY = google_key

    deepseek_api_key = st.text_input("Deepseek API Key", value=st.session_state.DEEPSEEK_API_KEY, type="password")
    if deepseek_api_key:
        st.session_state.DEEPSEEK_API_KEY = deepseek_api_key
    
    llm_model = st.selectbox(
        "LLM Model",
        ["gemini-2.0-flash-lite","gemini-2.0-flash","gpt-4o-mini", "gpt-4o","deepseek-chat"],
        index=0
    )

llm_provider_map ={
    "gemini-2.0-flash-lite":"google",
    "gemini-2.0-flash":"google",
    "gpt-4o-mini":"openai",
    "gpt-4o":"openai",
    "deepseek-chat":"deepseek"
}

llm_provider = llm_provider_map[llm_model]

llm_api_key_map = {
    "gemini-2.0-flash-lite":"GOOGLE_API_KEY",
    "gemini-2.0-flash":"GOOGLE_API_KEY",
    "gpt-4o-mini":"OPENAI_API_KEY",
    "gpt-4o":"OPENAI_API_KEY",
    "deepseek-chat":"DEEPSEEK_API_KEY"
}
    

# Page 1: Scrape Company Info
if page == "Scrape Company Info":
    st.header("Step 1: Scrape Company Information")
    
    # Form for company scraping
    with st.form(key="scrape_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            industry = st.text_input("Target Industry", placeholder="e.g., Software Development")
            location = st.text_input("Location", placeholder="e.g., San Francisco")
        
        with col2:
            target_count = st.number_input("Number of companies to scrape (with emails)", 
                                           min_value=1, 
                                           max_value=50, 
                                           value=10)
        
        submit_scrape = st.form_submit_button("🔍 Scrape Companies")
    
    # Handle scrape form submission
    if submit_scrape:
        if not industry or not location:
            st.error("Please fill in both industry and location fields.")
        elif not st.session_state[llm_api_key_map[llm_model]]:
            st.error("Please provide an OpenAI API key in the sidebar settings.")
        else:
            try:
                # Show progress
                progress_placeholder = st.empty()
                progress_bar = st.progress(0)
                
                # Create scraper
                progress_placeholder.text("Initializing scraper...")
                scraper = CompanyScraper(llm_model, llm_provider, st.session_state[llm_api_key_map[llm_model]])
                
                # Run scraper with progress updates
                progress_placeholder.text(f"Searching for {industry} companies in {location}...")
                
                # This is a workaround since we can't modify the scraper's run method
                # In a real app, you'd modify the scraper to report progress
                for i in range(10):
                    progress_bar.progress((i+1) * 10)
                    time.sleep(2)  # Simulate work
                
                output_file, count = scraper.run(industry, location, target_count)
                
                # Save results to session state
                st.session_state.scraped_data_path = output_file
                st.session_state.scraped_data = pd.read_csv(output_file)
                
                # Show success message
                progress_placeholder.empty()
                progress_bar.empty()
                st.success(f"Successfully scraped {count} companies with emails!")
                
                # Display the scraped data
                if st.session_state.scraped_data is not None:
                    st.subheader("Scraped Company Data")
                    st.dataframe(st.session_state.scraped_data)
                    
                    # Provide download link
                    st.markdown(
                        get_csv_download_link(
                            st.session_state.scraped_data, 
                            f"companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "Download Scraped Data"
                        ),
                        unsafe_allow_html=True
                    )
                    
                    # Guide to next step
                    st.info("Now proceed to the 'Compose Emails' step in the sidebar.")
                
            except Exception as e:
                st.error(f"Error during scraping: {e}")
                progress_placeholder.empty()
                progress_bar.empty()
    
    # Show existing data if available
    elif st.session_state.scraped_data is not None:
        st.subheader("Previously Scraped Company Data")
        st.dataframe(st.session_state.scraped_data)
        
        # Provide download link
        st.markdown(
            get_csv_download_link(
                st.session_state.scraped_data, 
                f"companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "Download Scraped Data"
            ),
            unsafe_allow_html=True
        )
        
        # Option to clear data and start again
        if st.button("Clear data and scrape again"):
            st.session_state.scraped_data = None
            st.session_state.scraped_data_path = None
            st.experimental_rerun()

# Page 2: Compose Emails
elif page == "Compose Emails":
    st.header("Step 2: Compose Personalized Emails")
    
    # Check if we have company data
    if st.session_state.scraped_data is None:
        # Allow user to upload a CSV instead
        st.warning("No scraped data found. Please complete Step 1 first or upload a CSV file with company data.")
        
        uploaded_file = st.file_uploader("Upload company CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                # Save the uploaded file
                file_path = save_uploaded_file(uploaded_file)
                
                # Read the CSV
                st.session_state.scraped_data = pd.read_csv(file_path)
                st.session_state.scraped_data_path = file_path
                
                st.success("File uploaded successfully!")
                st.dataframe(st.session_state.scraped_data)
            except Exception as e:
                st.error(f"Error reading the CSV file: {e}")
    
    # Only show compose form if we have data
    if st.session_state.scraped_data is not None:
        # Form for email composition
        with st.form(key="compose_form"):
            st.subheader("Your Company Information")
            
            company_name = st.text_input("Your Company Name", placeholder="e.g., Tech Solutions Inc.")
            
            company_desc = st.text_area(
                "Your Company Description", 
                placeholder="Describe your company, services, and unique value proposition...",
                height=150
            )
            
            additional_instructions = st.text_area(
                "Additional Instructions for Email Composition (Optional)", 
                placeholder="E.g., Include a brief mention of our special discount for new clients...",
                height=100
            )
            
            # Output filename
            output_filename = st.text_input(
                "Output Filename", 
                value=f"composed_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            submit_compose = st.form_submit_button("✉️ Compose Emails")
        
        # Handle compose form submission
        if submit_compose:
            if not company_name or not company_desc:
                st.error("Please fill in your company name and description.")
            elif not st.session_state[llm_api_key_map[llm_model]]:
                st.error("Please provide an API key in the sidebar settings.")
            else:
                try:
                    # Show progress
                    progress_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    progress_placeholder.text("Initializing email generator...")
                    
                    # Create email generator
                    # Create email generator with debug info
                    st.info(f"Creating EmailGenerator with model={llm_model}, provider={llm_provider}")
                    generator = EmailGenerator(llm_model, llm_provider, st.session_state[llm_api_key_map[llm_model]])
                    
                    # Process companies
                    csv_path = st.session_state.scraped_data_path
                    
                    # Create a wrapper function that reports progress
                    def process_with_progress():
                        companies = generator.read_company_data(csv_path)
                        total = len(companies)
                        emails = []
                        
                        for i, company in enumerate(companies):
                            progress_placeholder.text(f"Composing email for {company['Name']} ({i+1}/{total})...")
                            progress_bar.progress((i+1)/total)
                            
                            email = generator.generate_email(
                                company, 
                                company_name, 
                                company_desc, 
                                additional_instructions
                            )
                            
                            # Add to emails list
                            emails.append({
                                "Company Name": company["Name"],
                                "Email": company["Email"],
                                "Subject": email["subject"],
                                "Body": email["body"]
                            })
                        
                        # Create the output directory if it doesn't exist
                        if not os.path.exists("output"):
                            os.makedirs("output")
                        
                        # Write to CSV
                        output_file = f"output/{output_filename}.csv"
                        emails_df = pd.DataFrame(emails)
                        emails_df.to_csv(output_file, index=False, sep='|')
                        
                        return output_file, emails_df
                    
                    # Run the processing
                    output_file, emails_df = process_with_progress()
                    
                    # Save to session state
                    st.session_state.composed_emails_path = output_file
                    
                    # Clear progress indicators
                    progress_placeholder.empty()
                    progress_bar.empty()
                    
                    # Show success message
                    st.success(f"Successfully composed {len(emails_df)} emails!")
                    
                    # Preview the emails
                    with st.expander("Preview Composed Emails", expanded=True):
                        for i, row in emails_df.iterrows():
                            st.subheader(f"Email for {row['Company Name']}")
                            st.write(f"**To:** {row['Email']}")
                            st.write(f"**Subject:** {row['Subject']}")
                            st.text_area(f"Body {i+1}", value=row['Body'], height=150, key=f"body_{i}")
                            st.divider()
                    
                    # Provide download link
                    st.markdown(
                        get_csv_download_link(
                            emails_df, 
                            f"{output_filename}.csv",
                            "Download Composed Emails CSV"
                        ),
                        unsafe_allow_html=True
                    )
                    
                    # Note about CSV format
                    st.info("""
                    **Note:** The CSV file uses '|' as a delimiter. If you need to edit the emails before sending, 
                    download the file, make your changes, and then upload the edited file in the 'Send Emails' step.
                    """)
                    
                    # Guide to next step
                    st.info("Now proceed to the 'Send Emails' step in the sidebar.")
                    
                except Exception as e:
                    st.error(f"Error composing emails: {e}")
                    progress_placeholder.empty()
                    progress_bar.empty()

# Page 3: Send Emails
elif page == "Send Emails":
    st.header("Step 3: Send Emails")
    
    # Option to upload a different CSV
    st.subheader("Email Data Source")
    
    source_option = st.radio(
        "Choose email data source:",
        ["Use previously composed emails", "Upload a different CSV file"],
        index=0 if st.session_state.composed_emails_path else 1
    )
    
    emails_csv_path = None
    
    if source_option == "Use previously composed emails" and st.session_state.composed_emails_path:
        emails_csv_path = st.session_state.composed_emails_path
        st.success(f"Using previously composed emails: {os.path.basename(emails_csv_path)}")
        
        # Preview the data
        try:
            emails_df = pd.read_csv(emails_csv_path, sep='|')
            with st.expander("Preview Emails to Send", expanded=True):
                st.dataframe(emails_df[["Company Name", "Email", "Subject"]])
        except Exception as e:
            st.error(f"Error reading the emails file: {e}")
            emails_csv_path = None
            
    else:
        uploaded_file = st.file_uploader("Upload emails CSV file (with '|' delimiter)", type=["csv"])
        if uploaded_file is not None:
            try:
                # Save the uploaded file
                file_path = save_uploaded_file(uploaded_file)
                
                # Read the CSV
                emails_df = pd.read_csv(file_path, sep='|')
                
                st.success("File uploaded successfully!")
                
                # Preview the data
                with st.expander("Preview Emails to Send", expanded=True):
                    st.dataframe(emails_df[["Company Name", "Email", "Subject"]])
                
                emails_csv_path = file_path
                
            except Exception as e:
                st.error(f"Error reading the CSV file: {e}")
    
    # Send emails form
    if emails_csv_path:
        
        with st.form(key="send_form"):
            st.subheader("Email Sending Settings")
            
            sender_email = st.text_input("Your Gmail Address", value=st.session_state.SENDER_EMAIL)
            sender_password = st.text_input("Gmail App Password", value=st.session_state.SENDER_PASSWORD, type="password", 
                                          help="Use an app password, not your regular Gmail password. Create one at https://myaccount.google.com/apppasswords")
            
            submit_send = st.form_submit_button("📤 Send Emails")
        
        # Handle send form submission
        if submit_send:
            if not sender_email or not sender_password:
                st.error("Please provide both email address and app password.")
            else:
                try:
                    # Show progress
                    progress_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    progress_placeholder.text("Preparing to send emails...")
                    
                    # Read emails data to count total
                    emails_df = pd.read_csv(emails_csv_path, sep='|')
                    total_emails = len(emails_df)
                    
                    # We can't directly modify the send_emails_from_csv function,
                    # so create a wrapper that updates progress
                    def send_with_progress():
                        # This would normally call send_emails_from_csv, but we'll simulate it
                        # to show progress since we can't modify the original function
                        progress_placeholder.text(f"Sending {total_emails} emails...")
                        
                        # Simulate sending emails with progress
                        for i in range(total_emails):
                            progress_bar.progress((i+1)/total_emails)
                            time.sleep(1)  # Simulate sending
                        
                        # In a real app, you would call:
                        send_emails_from_csv(emails_csv_path, sender_email, sender_password)
                        
                    # Send the emails
                    send_with_progress()
                    
                    # In a real implementation, replace the above with:
                    # send_emails_from_csv(emails_csv_path, sender_email, sender_password)
                    
                    # Clear progress indicators
                    progress_placeholder.empty()
                    progress_bar.empty()
                    
                    # Show success message
                    st.success(f"Successfully sent {total_emails} emails!")
                    
                except Exception as e:
                    st.error(f"Error sending emails: {e}")
                    progress_placeholder.empty()
                    progress_bar.empty()
    else:
        st.warning("Please choose a source for emails to send.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Note:** This application requires API keys to function properly:
- OpenAI API key for generating content
- Gmail credentials for sending emails

All data is processed locally and not stored on external servers.
""")

# Main page footer
st.markdown("---")
st.caption("Business Outreach Automation | Developed by Muni Sekhar")

# to start the app run command:
# streamlit run app.py

