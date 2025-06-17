"""
Glean Prompt Library Scraper

This script scrapes prompt data from the Glean Prompt Library website.
It extracts all URLs first, then visits each one to collect data.
"""

import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    StaleElementReferenceException, 
    TimeoutException, 
    NoSuchElementException,
    WebDriverException
)


def setup_driver():
    """Setup and return a configured Chrome WebDriver."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    
    # Add user-agent to appear more like a regular browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        raise


def extract_prompt_data(driver):
    """Extract data from a prompt detail page."""
    # Check if we're on an empty page
    if driver.current_url == "data:," or "about:blank" in driver.current_url:
        print("Error: Empty page detected. Cannot extract data.")
        return {
            "Heading": "ERROR - Empty page",
            "Suited for": "N/A",
            "Category": "N/A",
            "Connectors": "N/A",
            "Prompt": "N/A"
        }
    
    # Wait for the page to load
    try:
        # First check if the page has loaded at all
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Now wait for specific elements
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".heading-xlarge-new.text-color-grey-333"))
        )
    except TimeoutException:
        print("Warning: Page load timeout. Attempting to extract available data.")
        # Take a screenshot for debugging
        try:
            screenshot_path = f"error_screenshot_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
        except:
            print("Could not save error screenshot")
    
    # Add a small delay to ensure page is fully rendered
    time.sleep(random.uniform(1, 2))
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Initialize data dictionary with default values
    data = {
        "Heading": "N/A",
        "Suited for": "N/A",
        "Category": "N/A",
        "Connectors": "N/A",
        "Prompt": "N/A"
    }
    
    # Extract heading
    try:
        heading_elem = soup.find('h1', class_="heading-xlarge-new text-color-grey-333")
        if heading_elem:
            data["Heading"] = heading_elem.text.strip()
    except Exception as e:
        print(f"Error extracting heading: {e}")
      
    # Extract "Suited for" tags
    try:
        suited_for_tags = soup.find_all(class_="pl_tag_item")
        if suited_for_tags and len(suited_for_tags) > 0:
            # Take only the first occurrence
            data["Suited for"] = suited_for_tags[0].text.strip()
    except Exception as e:
        print(f"Error extracting suited for tags: {e}")
    
    # Extract Category tags
    try:
        category_tags = soup.find_all(class_="category_tag_item w-dyn-item")
        if category_tags:
            data["Category"] = ', '.join(tag.text.strip() for tag in category_tags)
    except Exception as e:
        print(f"Error extracting category tags: {e}")
      
    # Extract Connectors
    try:
        connectors_wrapper = soup.find(class_="pl-template_connectors_wrapper w-dyn-items")
        if connectors_wrapper:
            connectors_items = connectors_wrapper.find_all('div', recursive=False)
            if connectors_items:
                # Clean up the connector text by removing "Click to go to integration page"
                cleaned_connectors = []
                for item in connectors_items:
                    connector_text = item.text.strip()
                    # Remove the unwanted text
                    connector_text = connector_text.replace("Click to go to integration page", "").strip()
                    if connector_text:  # Only add non-empty connectors
                        cleaned_connectors.append(connector_text)
                
                data["Connectors"] = ', '.join(cleaned_connectors)
    except Exception as e:
        print(f"Error extracting connectors: {e}")
    
    # Extract Prompt
    try:
        prompt_div = soup.find(class_="pl-template-2col_prompt-richtext w-richtext")
        if prompt_div:
            data["Prompt"] = prompt_div.get_text(strip=True)
    except Exception as e:
        print(f"Error extracting prompt: {e}")
    
    return data


def save_progress(data_list, is_final=False):
    """Save the collected data to a CSV file."""
    if not data_list:
        print("No data to save.")
        return False
    
    try:
        df = pd.DataFrame(data_list)
        
        if is_final:
            filename = "glean_prompts.csv"
        else:
            filename = f"glean_prompts_partial_{len(data_list)}_{int(time.time())}.csv"
        
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}: {len(data_list)} records")
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def extract_all_urls(driver):
    """Extract all prompt URLs from the main page."""
    print("Extracting all prompt URLs from the main page...")
    
    # Wait for the cards to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pl_card_outer-wrapper.w-dyn-item"))
    )
    
    # Get all cards
    cards = driver.find_elements(By.CSS_SELECTOR, ".pl_card_outer-wrapper.w-dyn-item")
    print(f"Found {len(cards)} cards on the page")
    
    # Extract URLs from all cards
    urls = []
    failed_cards = []
    
    for i, card in enumerate(cards):
        try:
            # Get card HTML
            card_html = card.get_attribute('outerHTML')
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(card_html, 'html.parser')
            link_tag = soup.find('a')
            
            if link_tag and link_tag.has_attr('href'):
                # Get the relative URL
                relative_url = link_tag['href']
                
                # Create absolute URL
                absolute_url = f"https://www.glean.com{relative_url}"
                urls.append(absolute_url)
                
                # Print progress every 10 cards
                if (i + 1) % 10 == 0:
                    print(f"Extracted {i + 1} URLs so far...")
            else:
                print(f"Warning: Could not find href in card {i + 1}")
                failed_cards.append(i)
                
                # Try alternate method with Selenium
                try:
                    a_tag = card.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")
                    
                    if href and href != "data:," and "about:blank" not in href:
                        urls.append(href)
                    else:
                        pathname = a_tag.get_attribute("pathname")
                        if pathname:
                            absolute_url = f"https://www.glean.com{pathname}"
                            urls.append(absolute_url)
                except Exception:
                    # If all else fails, just skip this card
                    print(f"Failed to extract URL from card {i + 1}")
        
        except Exception as e:
            print(f"Error extracting URL from card {i + 1}: {e}")
            failed_cards.append(i)
    
    print(f"Successfully extracted {len(urls)} URLs")
    
    if failed_cards:
        print(f"Failed to extract URLs from {len(failed_cards)} cards")
    
    return urls


def remove_duplicates_max_info(data):
    """Remove duplicates from data and retain rows with maximum information."""
    if not data:
        return data
    
    df = pd.DataFrame(data)
    
    # Count non-empty fields for each row (excluding URL)
    info_cols = [col for col in df.columns if col != "URL"]
    df["info_count"] = df[info_cols].apply(lambda row: sum(bool(str(x).strip()) and x != "N/A" for x in row), axis=1)
    
    # Keep row with max info_count for each URL
    df = df.sort_values("info_count", ascending=False).drop_duplicates(subset=["URL"], keep="first")
    df = df.drop(columns=["info_count"])
    
    return df.to_dict(orient="records")


def scrape_glean_prompts():
    """Main function to scrape the Glean prompt library."""
    # Initialize the browser
    driver = None
    all_prompts_data = []
    
    try:
        # Setup the browser
        driver = setup_driver()
        
        # Navigate to the prompt library
        print("Opening the Glean prompt library...")
        driver.get("https://www.glean.com/prompt-library")
        
        # Extract all URLs first
        all_urls = extract_all_urls(driver)
        
        # Save the URLs to a file for backup
        with open("prompt_urls.txt", "w") as f:
            for url in all_urls:
                f.write(f"{url}\n")
        print(f"Saved {len(all_urls)} URLs to prompt_urls.txt")
        
        # Process each URL
        for i, url in enumerate(all_urls):
            print(f"\nProcessing URL {i+1}/{len(all_urls)}: {url}")
            
            max_retries = 3
            success = False
            retries = 0
            
            while not success and retries < max_retries:
                try:
                    # Navigate to the URL
                    driver.get(url)
                    
                    # Check if page loaded successfully
                    if driver.current_url == "data:," or "about:blank" in driver.current_url:
                        print(f"Error: Empty page detected. Retrying ({retries+1}/{max_retries})...")
                        retries += 1
                        time.sleep(2)
                        continue
                    
                    # Extract data from the page
                    prompt_data = extract_prompt_data(driver)
                    
                    # Add URL to the data
                    prompt_data["URL"] = url
                    
                    # Add to our collection
                    all_prompts_data.append(prompt_data)
                    
                    # Mark as successful
                    success = True
                    
                    # Save progress periodically
                    if len(all_prompts_data) % 5 == 0:
                        save_progress(all_prompts_data)
                
                except Exception as e:
                    print(f"Error processing URL: {e}")
                    retries += 1
                    print(f"Retrying ({retries}/{max_retries})...")
                    time.sleep(2)
            
            if not success:
                print(f"Failed to process URL after {max_retries} attempts. Skipping.")
        
        # Final save
        print("\nScraping completed. Saving final results...")
        save_progress(all_prompts_data, is_final=True)
        
    except Exception as e:
        print(f"Critical error: {e}")
        
        # Emergency save if we have any data
        if all_prompts_data:
            print("Attempting emergency data save...")
            save_progress(all_prompts_data)
    
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
                print("Browser closed successfully")
            except:
                print("Error closing browser")
        
        return all_prompts_data


if __name__ == "__main__":
    print("Starting Glean Prompt Library scraper...")
    start_time = time.time()
    
    results = scrape_glean_prompts()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"\nScraping completed in {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"Total prompts collected: {len(results)}")

    # If running as script, deduplicate and save again
    if results:
        deduped = remove_duplicates_max_info(results)
        print(f"After deduplication: {len(deduped)} prompts remain")
        pd.DataFrame(deduped).to_csv("glean_prompts_deduped.csv", index=False)
        print("Deduplicated results saved to glean_prompts_deduped.csv")
