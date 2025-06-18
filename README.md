# Glean Prompt Library Scraper

A Python tool for scraping and collecting prompt data from the [Glean Prompt Library](https://www.glean.com/prompt-library).

## Features

- Extracts all prompt URLs from the main Glean prompt library page
- Visits each prompt page to collect detailed information
- Collects the following data for each prompt:
  - Heading
  - "Suited for" tags
  - Category
  - Connectors
  - Prompt text
- Saves data to CSV files
- Handles errors gracefully with retries
- Provides periodic backup saves
- Deduplicates results

## Requirements

- Python 3.8+
- Chrome browser

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/jypal6/glean-prompt-library.git
   cd glean-prompt-library
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Simply run the script:

```
python scraper.py
```

The script will:
1. Open the Glean prompt library website
2. Extract all prompt URLs
3. Visit each URL to collect data
4. Save the data to CSV files

Output files:
- `prompt_urls.txt` - List of all prompt URLs
- `glean_prompts_partial_*.csv` - Periodic backups during scraping
- `glean_prompts.csv` - Final complete dataset
- `glean_prompts_deduped.csv` - Final dataset with duplicates removed

## License

MIT

## Disclaimer

This tool is for educational purposes only. Please respect Glean's terms of service and robots.txt file when using this scraper.
