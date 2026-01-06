"""
Google Scholar to BibTeX Generator
Searches for publications by a specific author and generates a BibTeX file.

Supports two modes:
1. SerpAPI (reliable, free tier: 100 searches/month) - https://serpapi.com
2. Direct scraping (may be rate-limited by Google Scholar)
"""

import requests
import re
import os
import time
from typing import Optional
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURATION
# ============================================================
# Get a free API key at: https://serpapi.com/ (100 free searches/month)
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")


def sanitize_bibtex_key(title: str, year: str, author_last: str) -> str:
    """Generate a clean BibTeX key from title, year, and author."""
    words = re.sub(r'[^\w\s]', '', title).split()
    first_word = words[0].lower() if words else 'unknown'
    author_clean = re.sub(r'[^\w]', '', author_last).lower()
    return f"{author_clean}{year}{first_word}"


def extract_year(text: str) -> str:
    """Extract year from publication info text."""
    match = re.search(r'\b(19|20)\d{2}\b', str(text))
    return match.group(0) if match else 'n.d.'


def publication_to_bibtex(pub: dict, index: int) -> str:
    """Convert a publication dict to BibTeX format."""
    title = pub.get('title', 'Unknown Title')
    authors = pub.get('authors', 'Unknown Author')
    year = str(pub.get('year', 'n.d.'))
    venue = pub.get('venue', pub.get('publication', ''))
    snippet = pub.get('snippet', '')
    citations = pub.get('citations', 0)
    link = pub.get('link', '')
    
    # Clean up data
    title = title.replace('{', '').replace('}', '')
    authors = authors.replace('{', '').replace('}', '')
    
    # Determine entry type
    if venue:
        venue_lower = venue.lower()
        if any(x in venue_lower for x in ['conference', 'proceedings', 'symposium', 'workshop']):
            entry_type = 'inproceedings'
        elif any(x in venue_lower for x in ['journal', 'transactions', 'letters']):
            entry_type = 'article'
        else:
            entry_type = 'article'
    else:
        entry_type = 'misc'
    
    # Generate unique key
    author_parts = authors.split(',')[0].split() if authors else ['unknown']
    author_last = author_parts[-1] if author_parts else 'unknown'
    bibtex_key = f"{sanitize_bibtex_key(title, year, author_last)}_{index}"
    
    # Build BibTeX entry
    lines = [f"@{entry_type}{{{bibtex_key},"]
    lines.append(f'  title = {{{title}}},')
    lines.append(f'  author = {{{authors}}},')
    lines.append(f'  year = {{{year}}},')
    
    if venue:
        if entry_type == 'inproceedings':
            lines.append(f'  booktitle = {{{venue}}},')
        else:
            lines.append(f'  journal = {{{venue}}},')
    
    if snippet:
        snippet_clean = snippet.replace('{', '').replace('}', '')
        lines.append(f'  abstract = {{{snippet_clean}}},')
    
    if citations:
        lines.append(f'  note = {{Cited by {citations}}},')
    
    if link:
        lines.append(f'  url = {{{link}}},')
    
    lines.append("}")
    return '\n'.join(lines)


# ============================================================
# SerpAPI Method (Most Reliable)
# ============================================================

def search_scholar_serpapi(author_name: str, api_key: str, max_results: int = 100) -> list:
    """Search Google Scholar using SerpAPI (most reliable method)."""
    print(f"Searching Google Scholar via SerpAPI for: {author_name}")
    
    all_publications = []
    start = 0
    
    while len(all_publications) < max_results:
        params = {
            "engine": "google_scholar",
            "q": f'author:"{author_name}"',
            "api_key": api_key,
            "start": start,
            "num": 20
        }
        
        try:
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            
            if response.status_code == 401:
                print("Invalid API key. Please check your SerpAPI key.")
                break
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                break
                
            data = response.json()
            
            if "error" in data:
                print(f"Error: {data['error']}")
                break
            
            results = data.get("organic_results", [])
            if not results:
                print("No more results found.")
                break
                
            for result in results:
                pub_info = result.get('publication_info', {})
                authors_list = pub_info.get('authors', [])
                
                # Convert authors list to string
                if isinstance(authors_list, list):
                    authors = ', '.join([a.get('name', '') for a in authors_list])
                else:
                    authors = str(authors_list)
                
                pub = {
                    'title': result.get('title', ''),
                    'authors': authors if authors else pub_info.get('summary', '').split(' - ')[0],
                    'venue': pub_info.get('summary', ''),
                    'year': extract_year(pub_info.get('summary', '')),
                    'snippet': result.get('snippet', ''),
                    'citations': result.get('inline_links', {}).get('cited_by', {}).get('total', 0),
                    'link': result.get('link', '')
                }
                
                all_publications.append(pub)
                print(f"  [{len(all_publications)}] {pub['title'][:55]}...")
            
            start += 20
            
            total_results = data.get('search_information', {}).get('total_results', 0)
            if start >= total_results or start >= max_results:
                break
                
        except requests.exceptions.Timeout:
            print("Request timed out. Retrying...")
            continue
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return all_publications[:max_results]


# ============================================================
# Direct Scraping Method (Fallback)
# ============================================================

def search_scholar_direct(author_name: str, max_results: int = 100) -> list:
    """
    Search Google Scholar directly using requests with browser-like headers.
    This may be blocked by Google Scholar - use SerpAPI for reliable results.
    """
    print(f"Searching Google Scholar directly for: {author_name}")
    print("⚠️  Note: Direct scraping may be blocked. Consider using SerpAPI.")
    print()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    session = requests.Session()
    all_publications = []
    start = 0
    
    while len(all_publications) < max_results:
        # URL encode the author name
        query = f'author:"{author_name}"'
        url = f'https://scholar.google.com/scholar?q={requests.utils.quote(query)}&start={start}&hl=en'
        
        try:
            # Add some randomization to appear more human-like
            time.sleep(2 + (start / 10))  # Longer delays as we go
            
            response = session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 429:
                print("\n❌ Rate limited by Google Scholar.")
                print("   Please try again later or use SerpAPI for reliable access.")
                break
            
            if response.status_code != 200:
                print(f"\n❌ HTTP Error: {response.status_code}")
                break
            
            # Check for CAPTCHA or blocking
            if 'captcha' in response.text.lower() or 'unusual traffic' in response.text.lower():
                print("\n❌ Google Scholar is showing CAPTCHA.")
                print("   Use SerpAPI for reliable access (free tier available).")
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all search results
            results = soup.select('.gs_r.gs_or.gs_scl')
            
            if not results:
                # Check if we've reached the end or if there's an issue
                if 'did not match any articles' in response.text:
                    print("\nNo results found for this author.")
                break
            
            for result in results:
                # Extract title
                title_elem = result.select_one('.gs_rt a')
                if not title_elem:
                    title_elem = result.select_one('.gs_rt')
                title = title_elem.get_text() if title_elem else ''
                title = re.sub(r'^\[.*?\]\s*', '', title).strip()  # Remove [PDF] etc.
                
                # Extract link
                link = ''
                if title_elem and title_elem.name == 'a':
                    link = title_elem.get('href', '')
                
                # Extract authors and venue
                authors_elem = result.select_one('.gs_a')
                authors_text = authors_elem.get_text() if authors_elem else ''
                
                # Parse the author line (format: "Authors - Venue, Year - Publisher")
                parts = authors_text.split(' - ')
                authors = parts[0].strip() if parts else ''
                venue = parts[1].strip() if len(parts) > 1 else ''
                
                # Extract snippet/abstract
                snippet_elem = result.select_one('.gs_rs')
                snippet = snippet_elem.get_text() if snippet_elem else ''
                
                # Extract citation count
                cited_elem = result.select_one('a[href*="cites"]')
                citations = 0
                if cited_elem:
                    match = re.search(r'Cited by (\d+)', cited_elem.get_text())
                    if match:
                        citations = int(match.group(1))
                
                if title:
                    pub = {
                        'title': title,
                        'authors': authors,
                        'venue': venue,
                        'year': extract_year(authors_text),
                        'snippet': snippet.strip(),
                        'citations': citations,
                        'link': link
                    }
                    all_publications.append(pub)
                    print(f"  [{len(all_publications)}] {title[:55]}...")
            
            start += 10
            
        except requests.exceptions.Timeout:
            print("Request timed out. Continuing...")
            start += 10
            continue
        except Exception as e:
            print(f"Error during search: {e}")
            break
    
    return all_publications[:max_results]


# ============================================================
# Main Function
# ============================================================

def generate_bibtex_file(author_name: str, output_file: str = "publications.bib", 
                         max_results: int = 100, api_key: Optional[str] = None):
    """Main function to generate BibTeX file for an author."""
    
    print("=" * 60)
    print("  Google Scholar to BibTeX Generator")
    print("=" * 60)
    print()
    
    # Choose search method based on API key availability
    if api_key:
        publications = search_scholar_serpapi(author_name, api_key, max_results)
    else:
        print("ℹ️  No SerpAPI key provided.")
        print("   For reliable results, get a FREE API key at: https://serpapi.com/")
        print("   (100 free searches/month)")
        print()
        publications = search_scholar_direct(author_name, max_results)
    
    if not publications:
        print("\n" + "=" * 60)
        print("❌ No publications found!")
        print("=" * 60)
        print("\n📋 Troubleshooting tips:")
        print("   1. Try a different name format (e.g., 'A Le Gear' or 'A. Le Gear')")
        print("   2. Google Scholar may be blocking requests - try later")
        print("   3. Use SerpAPI for guaranteed results:")
        print("      - Sign up free at: https://serpapi.com/")
        print("      - Set environment variable: SERPAPI_KEY=your_key")
        print("      - Or edit this script to add your key directly")
        return
    
    print(f"\n✅ Found {len(publications)} publications")
    print("Generating BibTeX entries...")
    
    bibtex_entries = []
    for i, pub in enumerate(publications):
        try:
            entry = publication_to_bibtex(pub, i)
            bibtex_entries.append(entry)
        except Exception as e:
            print(f"  ⚠️  Could not convert publication {i+1}: {e}")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"% BibTeX file generated from Google Scholar\n")
        f.write(f"% Author: {author_name}\n")
        f.write(f"% Total entries: {len(bibtex_entries)}\n")
        f.write(f"% Generated by: scholar_to_bibtex.py\n\n")
        f.write('\n\n'.join(bibtex_entries))
    
    print(f"\n{'=' * 60}")
    print(f"✅ Successfully generated {len(bibtex_entries)} BibTeX entries")
    print(f"📄 Output file: {output_file}")
    print("=" * 60)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    # Configuration
    AUTHOR_NAME = "Andrew Le Gear"
    OUTPUT_FILE = "andrew_le_gear_publications.bib"
    MAX_RESULTS = 100
    
    # API Key - set via environment variable or paste directly here
    # Get a free key at: https://serpapi.com/
    API_KEY = SERPAPI_KEY  # or: "paste_your_key_here"
    
    generate_bibtex_file(
        author_name=AUTHOR_NAME,
        output_file=OUTPUT_FILE,
        max_results=MAX_RESULTS,
        api_key=API_KEY if API_KEY else None
    )
