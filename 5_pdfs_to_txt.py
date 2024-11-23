import logging
import argparse
from pathlib import Path
import fitz
import concurrent.futures
from tqdm import tqdm
import textwrap

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

def ensure_directory_exists(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text_content = []
        
        # Extract text from each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            # Add page number reference
            text_content.append(f"\n--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        return "\n".join(text_content)
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return None

def format_for_claude(text, pdf_name):
    """Format the extracted text for Claude"""
    formatted_text = f"""<document>
<name>{pdf_name}</name>
<text>
{text}
</text>
</document>"""
    return formatted_text

def format_for_chatgpt(text, pdf_name):
    """Format the extracted text for ChatGPT"""
    header = f"Content extracted from: {pdf_name}\n{'='*60}\n"
    
    # Wrap the text to improve readability in ChatGPT interface
    wrapped_text = textwrap.fill(text, width=80, replace_whitespace=False)
    
    formatted_text = f"""{header}
{wrapped_text}

Note: This text was automatically extracted from a PDF document. Page breaks are indicated by "--- Page X ---".
{'='*60}"""
    return formatted_text

def save_formatted_text(text, output_path):
    """Save formatted text to file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        logging.error(f"Error saving to {output_path}: {e}")
        return False

def process_pdf(pdf_path, output_dir):
    """Process a single PDF file and create both format versions."""
    try:
        pdf_name = pdf_path.name
        logging.info(f"Processing: {pdf_name}")
        
        # Extract text content
        text_content = extract_text_from_pdf(pdf_path)
        if not text_content:
            return False
        
        success = True
        # Create and save Claude format
        claude_path = output_dir / f"{pdf_path.stem}.claude.txt"
        claude_content = format_for_claude(text_content, pdf_name)
        if not save_formatted_text(claude_content, claude_path):
            success = False
        
        # Create and save ChatGPT format
        chatgpt_path = output_dir / f"{pdf_path.stem}.chatgpt.txt"
        chatgpt_content = format_for_chatgpt(text_content, pdf_name)
        if not save_formatted_text(chatgpt_content, chatgpt_path):
            success = False
        
        if success:
            logging.info(f"Created both formats for: {pdf_name}")
        return success
    except Exception as e:
        logging.error(f"Failed to process {pdf_name}: {e}")
        return False

def process_directory(input_path, output_dir):
    """Process all PDFs in a directory."""
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logging.error(f"No PDF files found in {input_path}")
        return
    
    successful = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a progress bar
        futures = {executor.submit(process_pdf, pdf, output_dir): pdf 
                  for pdf in pdf_files}
        
        for future in tqdm(concurrent.futures.as_completed(futures), 
                          total=len(pdf_files),
                          desc="Processing PDFs"):
            if future.result():
                successful += 1
    
    logging.info(f"\nSuccessfully processed {successful} out of {len(pdf_files)} PDF files")
    logging.info(f"Created both .claude.txt and .chatgpt.txt files for each PDF")

def main():
    parser = argparse.ArgumentParser(
        description="Convert PDFs to text files formatted for both Claude.ai and ChatGPT"
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to PDF file or directory containing PDFs"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(Path.home() / "Downloads" / "ai_texts"),
        help="Directory to save the output text files"
    )
    
    args = parser.parse_args()
    input_path = Path(args.input_path)
    output_dir = Path(args.output_dir)
    
    # Ensure output directory exists
    ensure_directory_exists(output_dir)
    
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        process_pdf(input_path, output_dir)
    elif input_path.is_dir():
        process_directory(input_path, output_dir)
    else:
        logging.error("Input must be a PDF file or directory containing PDFs")

if __name__ == "__main__":
    setup_logging()
    main()