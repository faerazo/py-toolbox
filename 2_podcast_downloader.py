import requests
from xml.etree import ElementTree
import os

download_dir = os.path.expanduser("~/Downloads")

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# Download an episode and return the filename
def download_episode(episode_url, episode_title):
    safe_title = episode_title.replace(' ', '_').replace(':', '')
    filename = "".join([c for c in safe_title if c.isalpha() or c.isdigit() or c in ['_', '.']]).rstrip() + '.mp3'
    full_path = os.path.join(download_dir, filename)
    response = requests.get(episode_url)
    with open(full_path, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded: {filename}")
    return filename

# Generate a txt file with all downloaded MP3 filenames
def generate_downloads_list(filenames):
    with open(os.path.join(download_dir, 'downloaded_podcasts.txt'), 'w') as file:
        file.write('mp3_files = [\n')
        for filename in filenames:
            file.write(f"             '{filename}',\n")
        file.write(']\n')

# Main script
def main():
    rss_feed_url = input("Please enter the RSS feed URL: ")
    response = requests.get(rss_feed_url)
    rss_root = ElementTree.fromstring(response.content)

    episodes = rss_root.findall('./channel/item')
    print("Available episodes:")
    for i, episode in enumerate(episodes[::-1], start=1):
        title = episode.find('title').text
        print(f"Episode {i}: {title}")

    selected_titles_input = input("\nEnter the titles of the episodes you want to download, separated by commas:\n")
    selected_titles = [title.strip() for title in selected_titles_input.split(',')]
    
    downloaded_filenames = []
    for episode in episodes:
        title = episode.find('title').text
        if title in selected_titles:
            mp3_url = episode.find('enclosure').attrib['url']
            downloaded_filenames.append(download_episode(mp3_url, title))
    
    generate_downloads_list(downloaded_filenames)

if __name__ == "__main__":
    main()
