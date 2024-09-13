import fitz
import logging
import os
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class Slide:
    def __init__(self, page_number, title, content):
        self.page_number = page_number
        self.title = title
        self.content = content
        self.content_length = len(content)

    def __str__(self):
        return (
            f"Page Number: {self.page_number}\n"
            f"Title: {self.title}\n"
            f"Content Length: {self.content_length} characters\n"
            f"Content: {self.content}\n"
        )


def extract_slide_information(pdf_path):
    try:
        document = fitz.open(pdf_path)
        slides = []

        for page_number in range(len(document)):
            page = document.load_page(page_number)
            text = page.get_text()
            lines = text.split("\n")
            if lines:
                title = lines[0] if lines[0] else "No Title"
                content = "\n".join(lines[1:]) if len(lines) > 1 else "No Content"
                slide = Slide(page_number + 1, title, content)
                slides.append(slide)

        return slides
    except Exception as e:
        logging.error(f"Failed to extract slide information from {pdf_path}: {e}")
        return []


def process_input_path(input_path, output_dir):
    if os.path.isfile(input_path):
        process_file(input_path, output_dir)
    elif os.path.isdir(input_path):
        process_directory(input_path, output_dir)
    else:
        logging.error(f"The input path {input_path} is neither a file nor a directory.")


def process_file(file_path, output_dir):
    try:
        slides = extract_slide_information(file_path)
        slide_dict = create_slide_dict(slides)
        filtered_dict = filter_slide_dict(slide_dict)
        filter_pdf_pages(file_path, filtered_dict, output_dir)
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")


def process_directory(directory_path, output_dir):
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith(".pdf")]
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_file, os.path.join(directory_path, f), output_dir) for f in pdf_files]
        for _ in tqdm(as_completed(futures), total=len(pdf_files), desc="Processing PDFs"):
            pass


def create_slide_dict(slides):
    slide_dict = {}
    for slide in slides:
        if slide.title not in slide_dict:
            slide_dict[slide.title] = {}
        slide_dict[slide.title][slide.page_number] = slide.content_length
    return slide_dict


def filter_slide_dict(slide_dict):
    filtered_dict = {}
    for title, pages in slide_dict.items():
        if len(pages) > 1:
            keep_pages = find_pages_to_keep(pages)
            filtered_dict[title] = keep_pages
        else:
            filtered_dict[title] = list(pages.keys())
    return filtered_dict


def find_pages_to_keep(pages):
    keep_pages = []
    page_numbers = sorted(pages.keys())
    max_length = pages[page_numbers[0]]
    for i in range(1, len(page_numbers)):
        if pages[page_numbers[i]] < pages[page_numbers[i - 1]]:
            keep_pages.append(page_numbers[i - 1])
        max_length = max(max_length, pages[page_numbers[i]])
    keep_pages.append(page_numbers[-1])
    return keep_pages


def filter_pdf_pages(pdf_path, filtered_dict, output_dir):
    try:
        document = fitz.open(pdf_path)
        output_filename = os.path.basename(pdf_path).replace(".pdf", "_filtered.pdf")
        output_path = os.path.join(output_dir, output_filename)
        output_document = fitz.open()

        pages_to_keep = set()
        for pages in filtered_dict.values():
            pages_to_keep.update(pages)

        for page_number in sorted(pages_to_keep):
            output_document.insert_pdf(document, from_page=page_number-1, to_page=page_number-1)

        output_document.save(output_path)
        output_document.close()
        document.close()

        removed_pages_count = len(document) - len(pages_to_keep)
        logging.info(f"Filtered PDF saved as {output_path}")
        logging.info(f"Number of slides removed: {removed_pages_count}")
    except Exception as e:
        logging.error(f"Failed to filter PDF pages for {pdf_path}: {e}")


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Extract slide information from PDF files."
    )
    parser.add_argument(
        "input_path", type=str, help="Path to the PDF file or directory of PDFs."
    )
    parser.add_argument("-o", "--output_dir", type=str, default=".", help="Output directory for filtered PDFs.")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    process_input_path(args.input_path, output_dir)


if __name__ == "__main__":
    main()
