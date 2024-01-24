import os
import git
import requests
from urllib.parse import urlparse
import markdown
from markdown.extensions.toc import TocExtension
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Headers for the requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Function to initialize headless Chrome browser
# This function is used to start a Chrome browser in headless mode (without GUI)
def init_headless_chrome():
    # Create an instance of Options class
    chrome_options = Options()
    # Add the "--headless" argument to the options
    chrome_options.add_argument("--headless")
    # Add the "--no-sandbox" argument to the options
    chrome_options.add_argument("--no-sandbox")
    # Add the "--disable-dev-shm-usage" argument to the options
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Create an instance of Service class
    service = Service(ChromeDriverManager().install())
    # Return a new instance of the Chrome driver with the specified options and service
    return webdriver.Chrome(service=service, options=chrome_options)

# Function to check if a link is broken using requests
# This function sends a GET request to the specified URL and checks if the status code is in the 4xx range
def is_broken_link_requests(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url, allow_redirects=True, timeout=10, headers=headers)
        # Check if the status code is in the 4xx range
        return 400 <= response.status_code < 500
    except requests.RequestException:
        # If an exception is raised, return True (the link is broken)
        return True

# Function to check if a link is broken using Selenium
# This function navigates to the specified URL using a Selenium browser and checks if the current URL is "about:blank"
def is_broken_link_selenium(url, browser):
    try:
        # Navigate to the URL
        browser.get(url)
        # Check if the current URL is "about:blank"
        if browser.current_url == "about:blank":
            return True
        return False
    except WebDriverException:
        # If an exception is raised, return True (the link is broken)
        return True

# Function to extract and check links in a markdown file
# This function reads the content of a markdown file, converts it to HTML, extracts all the links, and checks if they are broken
def check_links_in_file(file_path, browser):
    broken_links = []
    # Open the file in read mode with UTF-8 encoding
    with open(file_path, 'r', encoding='utf-8') as file:
        # Read the content of the file
        text = file.read()
        # Convert the markdown text to HTML
        html = markdown.markdown(text, extensions=[TocExtension(baselevel=1)])
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        # Find all the <a> tags (links) in the HTML
        for link in soup.find_all('a'):
            # Get the href attribute of the <a> tag
            url = link.get('href')
            # Check if the URL is not empty and its scheme is either "http" or "https"
            if url and urlparse(url).scheme in ['http', 'https']:
                # Check if the link is broken using requests
                if is_broken_link_requests(url):
                    # If requests indicate a broken link, double-check with Selenium
                    if is_broken_link_selenium(url, browser):
                        # If Selenium also indicates a broken link, add the URL to the list of broken links
                        broken_links.append(url)
    # Return the list of broken links
    return broken_links

# Function to clone the repository
# This function clones the specified GitHub repository to a local directory
def clone_repo(repo_url, target_path='repo'):
    # Check if the target directory does not exist
    if not os.path.exists(target_path):
        # Clone the repository to the target directory
        git.Repo.clone_from(repo_url, target_path)
    # Return the path of the target directory
    return target_path

# Function to scan a directory and check all markdown files
# This function scans a directory for markdown files, checks all the links in each file, and returns a dictionary of broken links per file
def scan_directory(directory_path):
    # Initialize a headless Chrome browser
    browser = init_headless_chrome()
    # Create an empty dictionary to store the broken links per file
    broken_links_per_file = {}
    # Walk through the directory
    for root, dirs, files in os.walk(directory_path):
        # Iterate over the files in the current directory
        for file in files:
            # Check if the file is a markdown file
            if file.endswith('.md'):
                # Get the full path of the file
                file_path = os.path.join(root, file)
                # Check the links in the file
                broken_links = check_links_in_file(file_path, browser)
                # If there are broken links, add them to the dictionary
                if broken_links:
                    broken_links_per_file[file_path] = broken_links
    # Quit the browser when done
    browser.quit()
    # Return the dictionary of broken links per file
    return broken_links_per_file

