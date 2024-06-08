import os
import logging
import argparse
from pytube import YouTube
from moviepy.editor import AudioFileClip
from pathlib import Path


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def download_video(url, output_path):
    try:
        yt = YouTube(url)
        video = yt.streams.filter(only_audio=True).first()
        return video.download(output_path=output_path)
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None


def convert_video_to_mp3(input_file):
    try:
        input_file = str(input_file)
        base = Path(input_file).stem.replace(" ", "")
        new_file = Path(input_file).parent / f"{base}.mp3"
        clip = AudioFileClip(input_file)
        clip.write_audiofile(new_file.as_posix())
        clip.close()
        return new_file
    except Exception as e:
        logging.error(f"Error converting video to mp3: {e}")
        return None


def clean_up_file(file_path):
    try:
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Error deleting file: {e}")


def process_video_download(url, save_path):
    out_file = download_video(url, save_path)
    if out_file:
        new_file = convert_video_to_mp3(Path(out_file))
        if new_file:
            clean_up_file(out_file)
            return new_file.name
    return None


def download_multiple_videos_as_mp3(urls, save_path):
    ensure_directory_exists(save_path)
    downloaded_files = [
        process_video_download(url.strip(), save_path) for url in urls if url.strip()
    ]
    downloaded_files = [file for file in downloaded_files if file]
    text_file = save_path / "downloaded_mp3_files.txt"
    with open(text_file, "w") as f:
        f.write("mp3_files = [\n")
        f.writelines(
            [f"    '{filename}',\n" for filename in downloaded_files[:-1]]
        )
        if downloaded_files:
            f.write(f"    '{downloaded_files[-1]}'\n")
        f.write("]\n")
    logging.info("The list of downloaded MP3 files has been generated.")


def main():
    parser = argparse.ArgumentParser(description="Download YouTube videos as MP3 files.")
    parser.add_argument(
        'urls',
        type=str,
        nargs='+',
        help='YouTube video URLs separated by spaces or semicolons.'
    )
    parser.add_argument(
        '--save_path',
        type=str,
        default='Downloads',
        help='Path to save the downloaded MP3 files.'
    )
    args = parser.parse_args()

    # Split the URLs by semicolons
    all_urls = []
    for url in args.urls:
        all_urls.extend(url.split(';'))
    
    save_path = Path(args.save_path)
    download_multiple_videos_as_mp3(all_urls, save_path)


if __name__ == "__main__":
    setup_logging()
    main()
