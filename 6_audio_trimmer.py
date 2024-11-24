import argparse
import logging
from pathlib import Path
from pydub import AudioSegment
import re


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def time_to_milliseconds(time_str):
    try:
        # Split the time string and reverse for easier processing
        parts = time_str.split(':')[::-1]
        
        if len(parts) == 2:  # MM:SS format
            seconds, minutes = parts
            hours = 0
        elif len(parts) == 3:  # HH:MM:SS format
            seconds, minutes, hours = parts
        else:
            raise ValueError("Invalid time format")

        # Convert to milliseconds
        total_ms = (int(hours) * 3600000 +  # hours to ms
                   int(minutes) * 60000 +    # minutes to ms
                   float(seconds) * 1000)    # seconds to ms
        
        return int(total_ms)
    except Exception as e:
        raise ValueError(f"Invalid time format: {time_str}. Use MM:SS or HH:MM:SS format.")


def load_audio_file(file_path):
    try:
        # Try to load the audio file directly
        audio = AudioSegment.from_file(str(file_path))
        return audio
    except Exception as e:
        logging.error(f"Error loading audio file: {e}")
        return None


def trim_audio(input_file, start_time, end_time, output_path):
    try:
        # Load the audio file
        audio = load_audio_file(str(input_file))
        if audio is None:
            return None
        
        # Convert time strings to milliseconds
        start_ms = time_to_milliseconds(start_time)
        end_ms = time_to_milliseconds(end_time)
        
        # Validate time range
        if start_ms >= end_ms:
            raise ValueError("End time must be after start time")
        if end_ms > len(audio):
            raise ValueError("End time exceeds audio duration")
        
        # Extract the specified portion
        trimmed_audio = audio[start_ms:end_ms]
        
        # Generate output filename (always .mp3)
        output_filename = f"{input_file.stem}_trimmed_{start_time.replace(':', '')}_to_{end_time.replace(':', '')}.mp3"
        output_file = output_path / output_filename
        
        # Export the trimmed audio as MP3
        logging.info(f"Exporting trimmed audio to MP3...")
        trimmed_audio.export(
            str(output_file),
            format='mp3',
            bitrate='192k',
            parameters=["-q:a", "0", "-map", "a"]
        )
        
        logging.info(f"Successfully trimmed audio: {output_file}")
        logging.info(f"Duration: {(end_ms - start_ms) / 1000:.2f} seconds")
        return output_file.name
        
    except Exception as e:
        logging.error(f"Error trimming audio file: {e}")
        return None


def process_audio_file(file_path, start_time, end_time, save_path):
    file_path = Path(file_path)
    ensure_directory_exists(save_path)
    
    # Try to process any file that might be an audio file
    try:
        return trim_audio(file_path, start_time, end_time, save_path)
    except Exception as e:
        logging.error(f"Could not process {file_path}: {e}")
        return None


def process_input_path(input_path, start_time, end_time, save_path):
    path = Path(input_path)
    if path.is_dir():
        # Process all files in directory - if they're not audio files, they'll be skipped
        for audio_file in path.glob("*"):
            result_file = process_audio_file(audio_file, start_time, end_time, save_path)
            if result_file:
                logging.info(f"Processed {audio_file.name} to {result_file}")
            logging.info("-" * 50)
    elif path.is_file():
        result_file = process_audio_file(path, start_time, end_time, save_path)
        if result_file:
            logging.info(f"Processed {path.name} to {result_file}")
        logging.info("-" * 50)
    else:
        logging.error("Invalid input path: It must be a directory or an audio file.")


def validate_time_format(time_str):
    pattern = r'^(?:(?:\d{1,2}:)?[0-5]?\d:[0-5]\d)$'
    if not re.match(pattern, time_str):
        raise argparse.ArgumentTypeError(
            "Time must be in MM:SS or HH:MM:SS format"
        )
    return time_str


def main():
    parser = argparse.ArgumentParser(
        description="Trim audio files at specific timestamps and export as MP3."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the audio file or directory containing audio files."
    )
    parser.add_argument(
        "--start_time",
        type=validate_time_format,
        required=True,
        help="Start time in format MM:SS or HH:MM:SS (e.g., 09:29)"
    )
    parser.add_argument(
        "--end_time",
        type=validate_time_format,
        required=True,
        help="End time in format MM:SS or HH:MM:SS (e.g., 12:30)"
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Path to save the trimmed MP3 files. Default is ~/Downloads"
    )
    
    args = parser.parse_args()
    
    save_path = Path(args.save_path)
    ensure_directory_exists(save_path)
    
    process_input_path(args.input_path, args.start_time, args.end_time, save_path)


if __name__ == "__main__":
    setup_logging()
    main()