import streamlit as st
from script import clone_repo, scan_directory, check_links_in_file, init_headless_chrome
import os

st.title('Markdown Link Checker')

# Function to list directories only
def list_directories(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

# User input for repository URL
repo_url = st.text_input('Enter the GitHub repository URL:', '')

if repo_url:
    # Clone the repository and get the path
    repo_path = clone_repo(repo_url)
    directories = list_directories(repo_path)

    # User input to select a directory
    directory_to_scan = st.selectbox('Select a directory to scan:', directories)

    # Scan the selected directory
    if st.button('Scan for broken links'):
        with st.spinner('Scanning...'):
            full_path = os.path.join(repo_path, directory_to_scan)
            markdown_files = [f for f in os.listdir(full_path) if f.endswith('.md')]

            if not markdown_files:
                st.warning('No Markdown files found in the selected directory.')
            else:
                st.write(f"Found {len(markdown_files)} Markdown files: {', '.join(markdown_files)}")
                
                # Initialize the headless browser
                browser = init_headless_chrome()

                progress_bar = st.progress(0)
                broken_links_data = {}
                for i, file in enumerate(markdown_files):
                    file_path = os.path.join(full_path, file)
                    broken_links = check_links_in_file(file_path, browser)  # Pass the browser instance
                    if broken_links:
                        broken_links_data[file_path] = broken_links
                    progress_bar.progress((i + 1) / len(markdown_files))

                # Quit the browser when done
                browser.quit()

                if not broken_links_data:
                    st.success('No broken links found in any of the Markdown files.')
                else:
                    for file_path, broken_links in broken_links_data.items():
                        with st.expander(f'{file_path}'):
                            for link in broken_links:
                                st.write(link)
