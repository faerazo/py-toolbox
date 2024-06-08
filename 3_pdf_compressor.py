import subprocess
import logging
import argparse
from pathlib import Path

DEFAULT_QUALITY = "-dPDFSETTINGS=/screen"
BYTES_IN_KB = 1024


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def compress_pdf(input_path, output_path):
    quality = DEFAULT_QUALITY
    cmd = ["gs", "-sDEVICE=pdfwrite", quality, "-o", output_path, input_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Error in compressing {input_path}: {result.stderr.decode()}")
        return False
    return True


def process_pdf_compression(file_path, save_path):
    file_path = Path(file_path)  # Ensure file_path is a Path object
    ensure_directory_exists(save_path)
    output_file = Path(save_path) / f"{file_path.stem}_compressed.pdf"

    # Use .stat() method to get the file size in kilobytes
    original_size = file_path.stat().st_size / BYTES_IN_KB
    # Pass file paths as strings to the compression function
    success = compress_pdf(str(file_path), str(output_file))

    if success:
        new_size = output_file.stat().st_size / BYTES_IN_KB  # Size in kilobytes
        logging.info(f"Original size: {original_size:.2f} KB")
        logging.info(f"New size: {new_size:.2f} KB")
        logging.info(f"Compression rate: {((new_size/original_size)-1) * 100:.2f}%")
        return output_file.name
    return None


def process_input_path(input_path, save_path):
    path = Path(input_path)
    if path.is_dir():
        for pdf_file in path.glob("*.pdf"):
            result_file = process_pdf_compression(pdf_file, save_path)
            if result_file:
                logging.info(f"Compressed and saved {pdf_file.name} to {result_file}")
            logging.info("-" * 50)
    elif path.is_file():
        result_file = process_pdf_compression(path, save_path)
        if result_file:
            logging.info(f"Compressed and saved {path.name} to {result_file}")
        logging.info("-" * 50)
    else:
        logging.error("Invalid input path: It must be a directory or a PDF file.")


def main():
    parser = argparse.ArgumentParser(description="Compress PDF files.")
    parser.add_argument(
        "input_path", type=str, help="The directory or PDF file path to compress."
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=str(Path.home() / "Downloads"),
        help="Path to save the compressed PDF files. Default is ~/Downloads",
    )
    args = parser.parse_args()

    input_path = args.input_path
    save_path = Path(args.save_path)
    ensure_directory_exists(save_path)
    process_input_path(input_path, save_path)


if __name__ == "__main__":
    setup_logging()
    main()
