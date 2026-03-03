# from fastapi import FastAPI, UploadFile, File
# import shutil
# import os
# import json

# from app.ingest.document_parser import parse_docx
# from app.llm.scene_generator import generate_scene

# app = FastAPI(title="Storybook AI – Milestone 1")


# @app.post("/v1/upload-docx")
# async def upload_docx(file: UploadFile = File(...)):
#     os.makedirs("data", exist_ok=True)

#     file_path = f"data/{file.filename}"
#     with open(file_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     extracted = parse_docx(file_path)

#     scenes = []
#     prev_summary = ""

#     for page in extracted["pages"]:
#         scene = generate_scene(
#             book_title=extracted["book_title"],
#             page=page,
#             prev_summary=prev_summary
#         )

#         prev_summary = scene["continuity_notes"]
#         scenes.append(scene)

#     output = {
#         "book_title": extracted["book_title"],
#         "scenes": scenes
#     }

#     with open("data/output/scenes.json", "w") as f:
#         json.dump(output, f, indent=2)

#     return output

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import shutil
import os
import json
from datetime import datetime
from pathlib import Path


from app.ingest.document_parser import parse_docx
from app.llm.scene_generator import generate_scene
from app.utils import slugify
import logging
import re
from typing import List, Set

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("storybook-ai")

# --- USAGE TRACKER (In-Memory for now) ---
class UsageStats:
    def __init__(self):
        self.llm_requests = 0
        self.image_requests = 0
        self.uploads = 0

    def to_dict(self):
        return {
            "llm_requests": self.llm_requests,
            "image_requests": self.image_requests,
            "uploads": self.uploads
        }

stats = UsageStats()

# from app.llm.image_generator import build_page_prompt, generate_page_image_bytes

#from app.llm.gemini_image_generator import generate_image_for_page
from app.llm.image_generator import generate_image_for_page

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import File, UploadFile

from pydantic import BaseModel

class ScenesUpdateRequest(BaseModel):
    book_title: str
    pages: list

class PageGenerateRequest(BaseModel):
    # Optional parameters for regeneration, like custom instructions (future)
    custom_prompt: str = None



app = FastAPI(title="Storybook AI – Milestone 1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://76.13.108.33:3000",
        "http://187.77.129.112:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/media",
    StaticFiles(directory="data"),
    name="media"
)

BASE_DIR = "data/books"

SYSTEM_PROMPT_PATH = "app/prompts/illustration_system.txt"
USER_PROMPT_PATH = "app/prompts/illustration_user.txt"

REF_BAILEY = "data/brand/reference/Bailey.png"
REF_BEAU = "data/brand/reference/Beau.png"


# @app.post("/v1/upload-docx")
# async def upload_docx(file: UploadFile = File(...)):
#     # 1) Save uploaded file temporarily first (needed for parsing)
#     os.makedirs("data/tmp", exist_ok=True)
#     tmp_path = f"data/tmp/{file.filename}"

#     with open(tmp_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     # 2) Extract book title + pages from DOCX
#     extracted = parse_docx(tmp_path)
#     book_title = extracted["book_title"]
#     book_slug = slugify(book_title)

#     # Optional: make each upload unique (same title uploaded twice)
#     # comment this out if you want to overwrite same-title book folder
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     book_folder = os.path.join(BASE_DIR, f"{book_slug}_{timestamp}")

#     input_dir = os.path.join(book_folder, "input")
#     output_dir = os.path.join(book_folder, "output")
#     os.makedirs(input_dir, exist_ok=True)
#     os.makedirs(output_dir, exist_ok=True)

#     # 3) Store input file permanently (input/original.docx)
#     saved_docx_path = os.path.join(input_dir, f'{book_title}.docx')
#     shutil.move(tmp_path, saved_docx_path)

#     # 4) Store extracted pages JSON (output/extracted_pages.json)
#     extracted_json_path = os.path.join(output_dir, "extracted_pages.json")
#     with open(extracted_json_path, "w", encoding="utf-8") as f:
#         json.dump(extracted, f, indent=2, ensure_ascii=False)

#     # 5) Run LLM to generate scenes page-by-page
#     scenes = []
#     prev_summary = ""

#     for page in extracted["pages"]:
#         scene = generate_scene(
#             book_title=book_title,
#             page=page,
#             prev_summary=prev_summary
#         )

#         # continuity strategy: use continuity_notes as "memory"
#         prev_summary = scene.get("continuity_notes", "")
#         scenes.append(scene)

#     # 6) Store final book-wise scenes JSON (output/scenes.json)
#     final_output = {
#         "book_title": book_title,
#         "pages": scenes
#     }

#     scenes_json_path = os.path.join(output_dir, "scenes.json")
#     with open(scenes_json_path, "w", encoding="utf-8") as f:
#         json.dump(final_output, f, indent=2, ensure_ascii=False)

#     # 7) Return response + paths (useful for Milestone 2 & 3)
#     return {
#         "book_title": book_title,
#         "book_folder": book_folder,
#         "input_file": saved_docx_path,
#         "book_file_id":book_folder.replace("\\", "/").split("books/")[-1],
#         "extracted_pages_json": extracted_json_path,
#         "scenes_json": scenes_json_path,
#         "pages_count": len(scenes),
#         "page":scenes
#     }


@app.post("/v1/upload-docx")
async def upload_docx(file: UploadFile = File(...)):
    # ---- 1) Save uploaded file temporarily ----
    logger.info(f"Received upload request for file: {file.filename}")
    stats.uploads += 1
    
    tmp_dir = Path("data/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_path = tmp_dir / f"upload_{timestamp}.docx"

    try:
        with tmp_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Saved temporary file to {tmp_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # ---- 2) Extract book title + pages from DOCX ----
    try:
        logger.info(f"Parsing DOCX: {tmp_path}")
        extracted = parse_docx(str(tmp_path))
        if not extracted or not extracted.get("pages"):
            logger.warning("DOCX parsing returned no pages.")
            raise ValueError("No pages extracted from document. Please check the file structure.")
        logger.info(f"Extracted {len(extracted['pages'])} pages from '{extracted['book_title']}'")
    except Exception as e:
        logger.error(f"Error parsing DOCX: {str(e)}")
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=400, detail=str(e))
        
    book_title = extracted["book_title"]
    book_slug = slugify(book_title)[:60] or "untitled"
    book_id = f"{book_slug}_{timestamp}"
    book_folder = Path(BASE_DIR) / book_id

    input_dir = book_folder / "input"
    output_dir = book_folder / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- 3) Store input file permanently ----
    saved_docx_path = input_dir / "original.docx"
    shutil.move(str(tmp_path), str(saved_docx_path))
    logger.info(f"Moved original to permanent storage: {saved_docx_path}")

    # ---- 4) Store extracted pages JSON ----
    extracted_json_path = output_dir / "extracted_pages.json"
    with extracted_json_path.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    # ---- 5) Initialize empty scenes.json ----
    scenes_skeleton = {
        "book_title": book_title,
        "pages": [] 
    }
    scenes_json_path = output_dir / "scenes.json"
    with scenes_json_path.open("w", encoding="utf-8") as f:
        json.dump(scenes_skeleton, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Book initialization complete for {book_id}")

    return {
        "book_title": book_title,
        "book_id": book_id,
        "book_folder": str(book_folder),
        "pages_count": len(extracted["pages"]),
        "extracted_pages": extracted["pages"]
    }

@app.get("/v1/system/usage")
def get_system_usage():
    return stats.to_dict()

@app.get("/v1/books/{book_id}")
def get_book_status(book_id: str):
    book_dir = Path(BASE_DIR) / book_id
    output_dir = book_dir / "output"
    
    extracted_path = output_dir / "extracted_pages.json"
    scenes_path = output_dir / "scenes.json"
    
    if not extracted_path.exists():
        raise HTTPException(status_code=404, detail="Book not found")
        
    with extracted_path.open("r", encoding="utf-8") as f:
        extracted_data = json.load(f)
        
    scenes_data = {"pages": []}
    if scenes_path.exists():
        with scenes_path.open("r", encoding="utf-8") as f:
            scenes_data = json.load(f)
            
    return {
        "book_title": extracted_data["book_title"],
        "book_id": book_id,
        "extracted_pages": extracted_data["pages"],
        "generated_scenes": scenes_data.get("pages", [])
    }

@app.post("/v1/books/{book_id}/pages/{page_number}/generate")
async def generate_page_scene(book_id: str, page_number: int, request: PageGenerateRequest = None):
    book_dir = Path(BASE_DIR) / book_id
    output_dir = book_dir / "output"
    
    extracted_path = output_dir / "extracted_pages.json"
    scenes_path = output_dir / "scenes.json"
    
    if not extracted_path.exists():
        raise HTTPException(status_code=404, detail="Book not found")
        
    with extracted_path.open("r", encoding="utf-8") as f:
        extracted_data = json.load(f)
        
    # Find the specific page text
    page_data = next((p for p in extracted_data["pages"] if p["page_number"] == page_number), None)
    if not page_data:
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found in document")
        
    # Get continuity notes from previous page if it exists in scenes.json
    prev_summary = ""
    scenes_list = []
    if scenes_path.exists():
        with scenes_path.open("r", encoding="utf-8") as f:
            scenes_full_data = json.load(f)
            scenes_list = scenes_full_data.get("pages", [])
            
        if page_number > 1:
            prev_page = next((p for p in scenes_list if p["page_number"] == page_number - 1), None)
            if prev_page:
                prev_summary = prev_page.get("continuity_notes", "")

    # Generate the scene
    try:
        logger.info(f"Generating scene for book {book_id}, page {page_number}")
        stats.llm_requests += 1
        new_scene = generate_scene(
            book_title=extracted_data["book_title"],
            page=page_data,
            prev_summary=prev_summary
        )
        logger.info(f"Successfully generated scene for page {page_number}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation failed: {str(e)}")

    # Update scenes.json (Page Isolation / Regeneration)
    existing_page_idx = next((i for i, p in enumerate(scenes_list) if p["page_number"] == page_number), -1)
    
    if existing_page_idx != -1:
        scenes_list[existing_page_idx] = new_scene
    else:
        scenes_list.append(new_scene)
        # Sort by page number to keep it tidy
        scenes_list.sort(key=lambda x: x["page_number"])
        
    final_output = {
        "book_title": extracted_data["book_title"],
        "pages": scenes_list
    }
    
    with scenes_path.open("w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    return new_scene



def _load_scenes_json(scenes_path: Path) -> dict:
    if not scenes_path.exists():
        raise FileNotFoundError(f"scenes.json not found at {scenes_path}")
    with open(scenes_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Regular expression to match page image filenames like "page_001.png"
PAGE_FILE_RE = re.compile(r"^page_(\d+)\.(png|jpg|jpeg|webp)$", re.IGNORECASE)

def _list_generated_page_numbers(images_dir: Path) -> List[int]:
    if not images_dir.exists():
        return []
    nums: List[int] = []
    for fn in os.listdir(images_dir):
        m = PAGE_FILE_RE.match(fn)
        if m:
            nums.append(int(m.group(1)))
    return sorted(set(nums))

def _expected_page_numbers_from_scenes(pages: list) -> List[int]:
    exp: Set[int] = set()
    for p in pages:
        pn = p.get("page_number")
        if pn is None:
            continue
        exp.add(int(pn))
    return sorted(exp)





REF_BAILEY = "data/brand/reference/bailey.png"
REF_BEAU = "data/brand/reference/beau.png"


@app.post("/v1/books/{book_id}/generate-images-gemini")
def generate_images_for_book_gemini(
    book_id: str,
    background_tasks: BackgroundTasks,
    overwrite: bool = False,
    start_page: int = 1,
    end_page: int = 10_000
):
    background_tasks.add_task(
        generate_images_task,
        book_id=book_id,
        overwrite=overwrite,
        start_page=start_page,
        end_page=end_page
    )
    return {
        "status": "started", 
        "message": "Image generation started in background."
    }

def generate_images_task(
    book_id: str,
    overwrite: bool = False,
    start_page: int = 1,
    end_page: int = 10_000
):
    try:
        book_dir = Path("data/books") / book_id
        scenes_path = book_dir / "output" / "scenes.json"

        if not scenes_path.exists():
            logger.error(f"scenes.json not found: {scenes_path}")
            return

        with open(scenes_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        book_title = data["book_title"]
        pages = data["pages"]
        total_pages = len(pages)

        images_dir = book_dir / "images" / slugify(book_title)
        images_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting background image generation for {book_id}, total {total_pages} pages.")

        for page in pages:
            page_no = int(page["page_number"])
            if page_no < start_page or page_no > end_page:
                continue

            out_path = images_dir / f"page_{page_no:03d}.png"

            if out_path.exists() and not overwrite:
                continue

            try:
                stats.image_requests += 1
                img = generate_image_for_page(
                    page=page
                )
                img.save(out_path)
                logger.info(f"Generated image for page {page_no}")
            except Exception as e:
                logger.error(f"Failed generating image for page {page_no}: {str(e)}")
    except Exception as e:
        logger.error(f"Background image generation failed: {str(e)}")


@app.get("/v1/books/{book_id}/images/status")
def get_images_status(book_id: str):
    book_dir = Path("data/books") / book_id
    scenes_path = book_dir / "output" / "scenes.json"

    if not scenes_path.exists():
        raise HTTPException(status_code=404, detail=f"scenes.json not found: {scenes_path}")

    data = _load_scenes_json(scenes_path)
    book_title = data["book_title"]
    pages = data.get("pages", [])

    expected_pages = _expected_page_numbers_from_scenes(pages)
    total_pages = len(expected_pages)

    images_dir = book_dir / "images" / slugify(book_title)
    generated_pages = _list_generated_page_numbers(images_dir)

    expected_set = set(expected_pages)
    generated_set = set(generated_pages)

    missing_pages = sorted(expected_set - generated_set)
    generated_count = len(generated_set)
    skipped_count = max(0, total_pages - generated_count)

    return {
        "book_id": book_id,
        "book_title": book_title,
        "scenes_json": str(scenes_path),
        "images_folder": str(images_dir),
        "total_pages": total_pages,
        "generated_count": generated_count,
        "skipped_count": skipped_count,
        "missing_pages": missing_pages,                 # IMPORTANT
        "generated_pages": generated_pages, # all generated pages thus far
    }


@app.get("/v1/books/{book_id}/images/skipped")
def get_skipped_images(book_id: str):
    book_dir = Path("data/books") / book_id
    scenes_path = book_dir / "output" / "scenes.json"

    if not scenes_path.exists():
        raise HTTPException(status_code=404, detail=f"scenes.json not found: {scenes_path}")

    data = _load_scenes_json(scenes_path)
    book_title = data["book_title"]
    pages = data.get("pages", [])

    expected_pages = _expected_page_numbers_from_scenes(pages)
    images_dir = book_dir / "images" / slugify(book_title)

    generated_pages = _list_generated_page_numbers(images_dir)

    missing_pages = sorted(set(expected_pages) - set(generated_pages))

    missing_files = [
        {
            "page_number": pn,
            "expected_file": str(images_dir / f"page_{pn:03d}.png")
        }
        for pn in missing_pages
    ]

    return {
        "book_id": book_id,
        "book_title": book_title,
        "images_folder": str(images_dir),
        "skipped_count": len(missing_pages),
        "missing_files": missing_files
    }


@app.post("/v1/books/{book_id}/scenes")
def update_scenes_json(book_id: str, payload: ScenesUpdateRequest):
    book_dir = Path("data/books") / book_id
    scenes_path = book_dir / "output" / "scenes.json"

    if not scenes_path.exists():
        raise HTTPException(
            status_code=404,
            detail="scenes.json not found for this book"
        )

    # Optional: basic validation
    if not isinstance(payload.pages, list) or len(payload.pages) == 0:
        raise HTTPException(
            status_code=400,
            detail="Pages array is invalid or empty"
        )
    
    # Clear existing images directory
    images_dir = book_dir / "images"
    if images_dir.exists() and images_dir.is_dir():
        shutil.rmtree(images_dir)



    # Overwrite scenes.json
    with scenes_path.open("w", encoding="utf-8") as f:
        json.dump(payload.dict(), f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "message": "scenes.json updated successfully",
        "scenes_json": str(scenes_path)
    }
