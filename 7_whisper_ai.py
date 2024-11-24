import argparse
import logging
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import whisper
import warnings
import torch


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # Filter out CUDA warnings
    warnings.filterwarnings("ignore", 
                          message="Applied workaround for CuDNN issue, install nvrtc.so.*",
                          category=UserWarning)
    warnings.filterwarnings("ignore", category=UserWarning)


def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def check_dependencies():
    try:
        # Check ffmpeg
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        logging.error("ffmpeg is not installed. Please install it first.")
        return False
    except FileNotFoundError:
        logging.error("ffmpeg is not installed. Please install it first.")
        return False
    
    return True


def transcribe_audio(file_path, output_dir, model_name='medium', language='English'):
    try:
        # Load model only if it hasn't been loaded
        if not hasattr(transcribe_audio, 'model'):
            logging.info(f"Loading Whisper model: {model_name}")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            transcribe_audio.model = whisper.load_model(model_name).to(device)
            logging.info(f"Using device: {device}")
            if device == "cuda":
                logging.info(f"GPU: {torch.cuda.get_device_name()}")
        
        logging.info(f"Transcribing: {file_path.name}")
        result = transcribe_audio.model.transcribe(
            str(file_path),
            language=language
        )
        
        # Save the transcription
        output_file = output_dir / f"{file_path.stem}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["text"])
        
        logging.info(f"Transcription saved to: {output_file}")
        return output_file.name
        
    except Exception as e:
        logging.error(f"Error transcribing {file_path.name}: {e}")
        return None


def process_audio_file(file_path, output_dir, model_name, language):
    """Process a single audio file."""
    file_path = Path(file_path)
    ensure_directory_exists(output_dir)
    
    supported_formats = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
    if file_path.suffix.lower() not in supported_formats:
        logging.error(f"Unsupported file format: {file_path.suffix}")
        return None
        
    return transcribe_audio(file_path, output_dir, model_name, language)


def process_multiple_files(file_paths, output_dir, model_name, language, max_workers=3):
    """Process multiple audio files concurrently."""
    ensure_directory_exists(output_dir)
    processed_files = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(
                process_audio_file,
                file_path,
                output_dir,
                model_name,
                language
            ): file_path
            for file_path in file_paths
        }
        
        with tqdm(total=len(future_to_file), desc="Transcribing files") as pbar:
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        processed_files.append(result)
                except Exception as exc:
                    logging.error(f'{file_path} generated an exception: {exc}')
                pbar.update(1)


def process_input_path(input_path, output_dir, model_name, language):
    """Process either a single file or directory of audio files."""
    path = Path(input_path)
    if path.is_dir():
        supported_files = [
            f for f in path.glob("*")
            if f.suffix.lower() in {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
        ]
        if not supported_files:
            logging.error("No supported audio files found in directory")
            return
        
        process_multiple_files(supported_files, output_dir, model_name, language)
    elif path.is_file():
        result_file = process_audio_file(path, output_dir, model_name, language)
        if result_file:
            logging.info(f"Processed {path.name} to {result_file}")
        logging.info("-" * 50)
    else:
        logging.error("Invalid input path: It must be a directory or an audio file.")


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Whisper AI."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the audio file or directory containing audio files."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Directory to save the transcriptions. Default is ~/Downloads/"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="medium",
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help="Whisper model to use. Default is 'medium'"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="English",
        help="Language of the audio. Default is 'English'"
    )
    
    args = parser.parse_args()
    
    if not check_dependencies():
        return
    
    output_dir = Path(args.output_dir)
    ensure_directory_exists(output_dir)
    
    # Set behavior
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    process_input_path(args.input_path, output_dir, args.model, args.language)


if __name__ == "__main__":
    setup_logging()
    main()