from pytube import YouTube
from moviepy.editor import *
import os

save_path = 'Downloads/' # Path to save the downloaded MP3 files

def download_video_as_mp3(url):
    """
    Download a YouTube video and save it as an MP3 file, removing spaces from the file name.
    """
    try:
        # Ensure save_path exists
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # Download video
        yt = YouTube(url)
        video = yt.streams.filter(only_audio=True).first()
        out_file = video.download(output_path=save_path)

        # Convert to MP3 with no spaces in the filename
        base, ext = os.path.splitext(out_file)
        base = base.replace(' ', '')  # Remove spaces from the base filename
        new_file = base + '.mp3'
        clip = AudioFileClip(out_file)
        clip.write_audiofile(new_file)

        # Remove the original download
        os.remove(out_file)

        # Final MP3 filename
        final_file = os.path.basename(new_file)

        print(f"Downloaded and converted to MP3: {final_file}")
        return final_file
    except Exception as e:
        print(f"An error occurred with {url}: {e}")
        return None

def download_multiple_videos_as_mp3(urls_string, delimiter=';'):
    """
    Download multiple YouTube videos and save them as MP3 files. Generate a text file 
    listing all downloaded MP3 files.
    """
    urls = urls_string.split(delimiter)
    downloaded_files = []

    for url in urls:
        url = url.strip()  # Remove any leading/trailing whitespace
        filename = download_video_as_mp3(url)
        if filename:
            downloaded_files.append(filename)

    # Generate text file with MP3 filenames
    text_file = os.path.join(save_path, 'downloaded_mp3_files.txt')
    with open(text_file, 'w') as f:
        f.write("mp3_files = [\n")
        # Handle the comma placement for the last item
        for i, filename in enumerate(downloaded_files):
            if i < len(downloaded_files) - 1:
                f.write(f"             '{filename}',\n")
            else:
                f.write(f"             '{filename}'\n")
        f.write("]\n")

    print("The list of downloaded MP3 files has been generated.")

if __name__ == "__main__":
    urls_string = input("Enter the YouTube video URLs separated by a semicolon (;): ")
    download_multiple_videos_as_mp3(urls_string)
