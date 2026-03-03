from docx import Document
import re


PAGE_RE = re.compile(r"^Page\s+(\d+)", re.IGNORECASE)


def parse_docx(file_path: str) -> dict:
    import logging
    logger = logging.getLogger("storybook-ai.parser")
    
    logger.info(f"Parsing document at {file_path}")
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        logger.error("Document is empty (no text found in paragraphs)")
        raise ValueError("Empty document")

    book_title = paragraphs[0]
    logger.info(f"Inferred Book Title: {book_title}")

    pages = []
    current_page = None
    buffer = []

    for p in paragraphs[1:]:
        match = PAGE_RE.match(p)
        if match:
            if current_page is not None:
                pages.append({
                    "page_number": current_page,
                    "page_text": " ".join(buffer).strip()
                })
            current_page = int(match.group(1))
            buffer = []
            logger.info(f"Found marker for Page {current_page}")
        else:
            if current_page is not None:
                buffer.append(p)
            else:
                # If content exists before any 'Page X' marker, save it for fallback
                buffer.append(p)

    if current_page is not None:
        pages.append({
            "page_number": current_page,
            "page_text": " ".join(buffer).strip()
        })
    elif buffer:
        # FALLBACK: If no 'Page X' markers were found at all, treat the entire document as Page 1
        logger.warning("No 'Page X' markers found. Falling back to single-page mode.")
        pages.append({
            "page_number": 1,
            "page_text": " ".join(buffer).strip()
        })

    logger.info(f"Final Page Count: {len(pages)}")
    return {
        "book_title": book_title,
        "pages": pages
    }
