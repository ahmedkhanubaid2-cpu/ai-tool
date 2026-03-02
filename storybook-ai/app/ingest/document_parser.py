from docx import Document
import re


PAGE_RE = re.compile(r"^Page\s+(\d+)", re.IGNORECASE)


def parse_docx(file_path: str) -> dict:
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        raise ValueError("Empty document")

    book_title = paragraphs[0]

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
        else:
            if current_page is not None:
                buffer.append(p)

    if current_page is not None:
        pages.append({
            "page_number": current_page,
            "page_text": " ".join(buffer).strip()
        })
    print(book_title)
    print(pages)
    return {
        "book_title": book_title,
        "pages": pages
    }
