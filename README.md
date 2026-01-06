# Google Scholar to BibTeX Generator

A Python script that searches Google Scholar for publications by a specific author and generates a BibTeX file for use in LaTeX documents, reference managers, or other academic tools.

## Features

- 🔍 Search Google Scholar by author name
- 📄 Generate properly formatted BibTeX entries
- 📊 Includes citation counts, abstracts, and URLs
- 🔄 Supports two search methods:
  - **SerpAPI** (recommended): Reliable, free tier available
  - **Direct scraping**: Fallback option (may be rate-limited)

## Prerequisites

- Python 3.8+
- SerpAPI account (free tier: 100 searches/month)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Get a SerpAPI key** (free):
   - Sign up at [https://serpapi.com/](https://serpapi.com/)
   - Get your API key from the dashboard

5. **Set your API key**:
   ```powershell
   $env:SERPAPI_KEY = "your_api_key_here"
   ```
   
   Or on Linux/Mac:
   ```bash
   export SERPAPI_KEY="your_api_key_here"
   ```

## Usage

### Basic Usage

Edit the configuration in `scholar_to_bibtex.py`:

```python
AUTHOR_NAME = "Andrew Le Gear"  # Author to search for
OUTPUT_FILE = "publications.bib"  # Output filename
MAX_RESULTS = 100  # Maximum publications to retrieve
```

Then run:

```powershell
python scholar_to_bibtex.py
```

### Programmatic Usage

```python
from scholar_to_bibtex import generate_bibtex_file

generate_bibtex_file(
    author_name="John Smith",
    output_file="john_smith_publications.bib",
    max_results=50,
    api_key="your_serpapi_key"  # or None to use env variable
)
```

## Output Format

The script generates standard BibTeX entries:

```bibtex
@article{smith2023machine_0,
  title = {Machine Learning Applications in Healthcare},
  author = {J Smith, A Jones, B Williams},
  year = {2023},
  journal = {Journal of Medical Informatics},
  abstract = {This paper explores...},
  note = {Cited by 45},
  url = {https://example.com/paper},
}
```

## Entry Types

The script automatically determines the appropriate BibTeX entry type:

| Venue Keywords | Entry Type |
|----------------|------------|
| conference, proceedings, symposium, workshop | `@inproceedings` |
| journal, transactions, letters | `@article` |
| Other/unknown | `@misc` |

## Troubleshooting

### "No publications found"

1. **Try different name formats**: `"A. Le Gear"`, `"A Le Gear"`, `"Andrew Le Gear"`
2. **Check your API key**: Ensure `SERPAPI_KEY` is set correctly
3. **Verify the author exists** on [Google Scholar](https://scholar.google.com)

### Rate Limiting

If using direct scraping without SerpAPI, Google Scholar may block requests. Solutions:
- Wait and try again later
- Use SerpAPI (recommended)

### Invalid API Key

Verify your key at [SerpAPI Dashboard](https://serpapi.com/manage-api-key)

## Project Structure

```
myresearchscraper/
├── scholar_to_bibtex.py    # Main script
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── *.bib                  # Generated BibTeX files
```

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing (fallback scraping)
- `scholarly` - Google Scholar library (optional)

## Limitations

- Google Scholar does not provide a public API
- SerpAPI free tier limited to 100 searches/month
- Some publication metadata may be incomplete
- Duplicate entries possible if papers appear in multiple venues

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! Feel free to submit issues or pull requests.
