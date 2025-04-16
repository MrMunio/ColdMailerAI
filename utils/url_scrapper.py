# utils/url_scrapper.py
from bs4 import BeautifulSoup
import html2text
import requests
def clean_content( soup):
    """
    Clean HTML content by removing unwanted elements
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        BeautifulSoup: Cleaned HTML
    """
    # Remove script and style elements
    for element in soup(['script', 'style', 'iframe', 'nav', 'footer']):
        element.decompose()
    return soup

def html_to_markdown(html_content):
    """
    Convert HTML content to markdown
    
    Args:
        html_content (str): HTML content
        
    Returns:
        str: Markdown content
    """
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title
    title = soup.title.string if soup.title else "No Title"
    
    # Clean content
    cleaned_soup = clean_content(soup)
    
    # Convert to markdown
    markdown = html2text.HTML2Text().handle(str(cleaned_soup))
    
    # Add title as heading
    markdown = f"# {title}\n\n{markdown}"
    
    return markdown

def scrape_page(url):
    """
    Scrape a single page and convert to markdown
    
    Args:
        url (str): URL to scrape
        
    Returns:
        tuple: (markdown_content, links) - the markdown content and extracted links
    """
    
    try:
        # Fetch page content
        print(f"Scraping: {url}")
        response = requests.Session().get(url, timeout=10)
        
        # Check status code
        if response.status_code != 200:
            print(f"Error scraping {url}: HTTP status code {response.status_code}")
            return None, []
            
        # Some sites may not properly set content-type header
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Try to detect if content is HTML, even if content-type isn't set correctly
        if 'text/html' not in content_type and '<html' not in response.text.lower()[:1000]:
            print(f"Skipping {url} - content doesn't appear to be HTML (Content-Type: {content_type})")
            return None, []
            
        # Convert to markdown
        markdown_content = html_to_markdown(response.text)
        
        # Extract links for further crawling
        soup = BeautifulSoup(response.text, 'html.parser')
        # links = extract_links(soup, url)
        
        return markdown_content
        
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        return None, []
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None, []