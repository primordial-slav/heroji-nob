import pdfplumber
import json
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of strings, one per page
    """
    pages_text = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")

        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            pages_text.append(text)
            print(f"Processed page {i + 1}/{len(pdf.pages)}")

    return pages_text


def save_extracted_text(pages_text, output_path):
    """
    Save extracted text to a file.

    Args:
        pages_text: List of text strings
        output_path: Path to save the output
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, page_text in enumerate(pages_text):
            f.write(f"\n{'='*50}\n")
            f.write(f"PAGE {i + 1}\n")
            f.write(f"{'='*50}\n\n")
            f.write(page_text)
            f.write("\n\n")

    print(f"Text saved to: {output_path}")


if __name__ == "__main__":
    # Paths
    pdf_path = Path("../01-data/raw/prva-licka-proleterska.pdf")
    output_path = Path("../01-data/processed/extracted_text.txt")

    # Extract text
    print(f"Extracting text from: {pdf_path}")
    pages_text = extract_text_from_pdf(pdf_path)

    # Save to file
    save_extracted_text(pages_text, output_path)

    print("Done!")
