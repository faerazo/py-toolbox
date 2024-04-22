import os
import logging
from pytube import YouTube
from moviepy.editor import AudioFileClip
from pathlib import Path

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def download_video(url, output_path):
    yt = YouTube(url)
    video = yt.streams.filter(only_audio=True).first()
    return video.download(output_path=output_path)

def convert_video_to_mp3(input_file):
    input_file = str(input_file)
    base = Path(input_file).stem.replace(' ', '')
    new_file = Path(input_file).parent / f'{base}.mp3'
    clip = AudioFileClip(input_file)
    clip.write_audiofile(new_file.as_posix())
    return new_file

def clean_up_file(file_path):
    os.remove(file_path)

def process_video_download(url, save_path):
    out_file = download_video(url, save_path)
    new_file = convert_video_to_mp3(Path(out_file))
    clean_up_file(out_file)
    return new_file.name

def download_multiple_videos_as_mp3(urls_string, save_path, delimiter=';'):
    ensure_directory_exists(save_path)
    urls = urls_string.split(delimiter)
    downloaded_files = [process_video_download(url.strip(), save_path) for url in urls if url.strip()]
    text_file = save_path / 'downloaded_mp3_files.txt'
    with open(text_file, 'w') as f:
        f.write("mp3_files = [\n")
        f.writelines([f"             '{filename}',\n" for filename in downloaded_files[:-1]])
        f.write(f"             '{downloaded_files[-1]}'\n")
        f.write("]\n")
    logging.info("The list of downloaded MP3 files has been generated.")

def main():
    save_path = Path('Downloads')
    urls_string = input("Enter the YouTube video URLs separated by a semicolon (;): ")
    download_multiple_videos_as_mp3(urls_string, save_path)

if __name__ == "__main__":
    setup_logging()
    main()