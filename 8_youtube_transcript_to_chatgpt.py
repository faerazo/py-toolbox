import logging
import argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import subprocess
import pyperclip

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def get_video_id_from_url(youtube_url: str) -> str:
    parsed_url = urlparse(youtube_url)
    if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif parsed_url.hostname == "youtu.be":
        return parsed_url.path.lstrip("/")
    else:
        return None

def fetch_transcript(video_id: str):
    if not video_id:
        raise ValueError("Invalid YouTube URL or video ID.")

    transcripts_list = YouTubeTranscriptApi.list_transcripts(video_id)
    try:
        # Try to find a manually created English transcript first
        transcript = transcripts_list.find_manually_created_transcript(['en'])
    except NoTranscriptFound:
        # If not found, try auto-generated English transcript
        transcript = transcripts_list.find_generated_transcript(['en'])

    return transcript.fetch()

def save_transcript_to_file(video_id, transcript_data, save_path):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        video_title = transcript_list.video_title
        safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in video_title)
        safe_title = safe_title.replace(" ", "_")
        transcript_file = Path(save_path) / f"{safe_title}_transcript.txt"
    except Exception:
        transcript_file = Path(save_path) / f"{video_id}_transcript.txt"
    
    # Save transcript to file
    full_transcript = ""
    with open(transcript_file, "w", encoding="utf-8") as f:
        for segment in transcript_data:
            line = f"{segment['text']}\n"
            f.write(line)
            full_transcript += line

    # Prepare the prompt and copy to clipboard
    prompt = "Summarize the following video, provide me the key points and relevant details.\n\n" + full_transcript
    try:
        pyperclip.copy(prompt)
        logging.info("Prompt copied to clipboard! You can now paste it into ChatGPT.")
    except Exception as e:
        logging.error(f"Failed to copy to clipboard: {e}")
    
    # Open ChatGPT using the appropriate command based on the platform
    try:
        import platform
        system = platform.system().lower()
        
        if system == 'darwin':  # macOS
            subprocess.run(['open', 'https://chat.openai.com/'], check=True)
        elif system == 'linux':  # Linux/WSL
            try:
                subprocess.run(['wslview', 'https://chat.openai.com/'], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to xdg-open if wslview is not available
                subprocess.run(['xdg-open', 'https://chat.openai.com/'], check=True)
        elif system == 'windows':  # Windows
            subprocess.run(['start', 'https://chat.openai.com/'], shell=True, check=True)
    except Exception as e:
        logging.error(f"Failed to open browser: {e}")
    
    return transcript_file.name

def process_video_transcript(youtube_url, save_path):
    video_id = get_video_id_from_url(youtube_url)
    if not video_id:
        logging.error(f"Could not extract video ID from URL: {youtube_url}")
        return None

    try:
        transcript_data = fetch_transcript(video_id)
        filename = save_transcript_to_file(video_id, transcript_data, save_path)
        logging.info(f"Saved transcript: {filename}")
        return filename
    except TranscriptsDisabled:
        logging.error(f"Transcripts are disabled for video: {youtube_url}")
    except NoTranscriptFound:
        logging.error(f"No transcript found for video: {youtube_url}")
    except Exception as e:
        logging.error(f"Error fetching transcript for {youtube_url}: {e}")

    return None

def download_multiple_transcripts(urls, save_path):
    ensure_directory_exists(save_path)
    downloaded_files = []
    total = len(urls)

    logging.info(f"Processing {total} video(s)...")

    for url in urls:
        url = url.strip()
        if not url:
            continue
        filename = process_video_transcript(url, save_path)
        if filename:
            downloaded_files.append(filename)

    logging.info(f"Successfully downloaded {len(downloaded_files)} transcript(s).")

def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube video transcripts."
    )
    parser.add_argument(
        "urls",
        type=str,
        nargs="+",
        help="YouTube video URLs separated by spaces or semicolons.",
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Path to save the downloaded transcript files.",
    )
    args = parser.parse_args()

    # Split URLs by semicolon if multiple are given in a single argument
    all_urls = []
    for url in args.urls:
        all_urls.extend(url.split(";"))

    save_path = Path(args.save_path)
    download_multiple_transcripts(all_urls, save_path)

if __name__ == "__main__":
    setup_logging()
    main()
