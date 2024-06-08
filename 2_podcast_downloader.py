""" 
Works with:
    - https://podcast.emerj.com/rss
    - https://feeds.megaphone.fm/MLN2155636147
    - https://changelog.com/practicalai/feed
"""

import logging
import argparse
from pathlib import Path
import requests
from xml.etree import ElementTree


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def fetch_rss_feed(url):
    response = requests.get(url)
    return ElementTree.fromstring(response.content)


def download_episode(episode_url, episode_title, download_dir):
    safe_title = (
        "".join(
            c
            for c in episode_title.replace(" ", "_").replace(":", "")
            if c.isalnum() or c in ["_", "."]
        )
        + ".mp3"
    )
    full_path = download_dir / safe_title
    response = requests.get(episode_url)
    with open(full_path, "wb") as file:
        file.write(response.content)
    logging.info(f"Downloaded: {safe_title}")
    return safe_title


def generate_downloads_list(filenames, download_dir):
    output_file = download_dir / "downloaded_podcasts.txt"
    with open(output_file, "w") as file:
        file.write("mp3_files = [\n")
        file.writelines(f"             '{filename}',\n" for filename in filenames)
        file.write("]\n")
    logging.info("Download list generated.")


def display_episodes(episodes):
    logging.info("Available episodes:")
    for i, episode in enumerate(episodes[::-1], start=1):
        title = episode.find("title").text
        logging.info(f"Episode {i}: {title}")


def get_selected_episodes(episodes):
    selected_episode_numbers = input(
        "\nEnter the episode numbers you want to download, separated by a semicolon(;):\n"
    )
    selected_numbers = [int(num.strip()) for num in selected_episode_numbers.split(";")]

    return [
        episodes[len(episodes) - num]
        for num in selected_numbers
        if len(episodes) - num in range(len(episodes))
    ]


def download_selected_episodes(episodes, download_dir):
    downloaded_filenames = [
        download_episode(
            ep.find("enclosure").attrib["url"], ep.find("title").text, download_dir
        )
        for ep in episodes
    ]
    generate_downloads_list(downloaded_filenames, download_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Download podcast episodes from an RSS feed."
    )
    parser.add_argument(
        "rss_feed_url", type=str, help="The RSS feed URL of the podcast."
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Path to save the downloaded podcast files.",
    )
    args = parser.parse_args()

    download_dir = Path(args.save_path)
    ensure_directory_exists(download_dir)

    rss_feed_url = args.rss_feed_url
    rss_root = fetch_rss_feed(rss_feed_url)

    episodes = rss_root.findall("./channel/item")
    display_episodes(episodes)

    selected_episodes = get_selected_episodes(episodes)
    download_selected_episodes(selected_episodes, download_dir)


if __name__ == "__main__":
    setup_logging()
    main()
