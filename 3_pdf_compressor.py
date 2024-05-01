import subprocess
import os
import logging
from pathlib import Path

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def compress_pdf(input_path, output_path):
    quality = "-dPDFSETTINGS=/screen"  # Lower quality and smaller size
    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        quality,
        "-o", output_path,
        input_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def process_pdf_compression(file_path, save_path):
    ensure_directory_exists(save_path)
    output_file = Path(save_path) / f"{Path(file_path).stem}_compressed{Path(file_path).suffix}"
    original_size = os.path.getsize(file_path) / 1024  # Size in kilobytes
    compress_pdf(file_path, output_file)
    new_size = os.path.getsize(output_file) / 1024  # Size in kilobytes
    logging.info(f'Original size of {file_path.name}: {original_size:.2f} KB')
    logging.info(f'New size of {output_file.name}: {new_size:.2f} KB')
    logging.info(f'Compression ratio: {new_size / original_size *100:.2f}%')
    return output_file.name

def process_input_path(input_path, save_path):
    path = Path(input_path)
    if path.is_dir():
        for pdf_file in path.glob('*.pdf'):
            result_file = process_pdf_compression(pdf_file, save_path)
            logging.info(f'Compressed and saved {pdf_file.name} to {result_file}')
            logging.info('-' * 50)
    elif path.is_file():
        result_file = process_pdf_compression(path, save_path)
        logging.info(f'Compressed and saved {path.name} to {result_file}')
        logging.info('-' * 50)
    else:
        logging.error("Invalid input path: It must be a directory or a PDF file.")

def main():
    input_path = input("Enter the directory or PDF file path: ")
    save_path = Path.home() / 'Downloads'
    ensure_directory_exists(save_path)
    process_input_path(input_path, save_path)

if __name__ == "__main__":
    setup_logging()
    main()
