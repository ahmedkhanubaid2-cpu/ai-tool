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

from fastapi import FastAPI, UploadFile, File,HTTPException
import shutil
import os
import json
from datetime import datetime
from pathlib import Path


from app.ingest.document_parser import parse_docx
from app.llm.scene_generator import generate_scene
from app.utils import slugify
#for get 
import re
from typing import List, Set

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



app = FastAPI(title="Storybook AI – Milestone 1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://76.13.108.33:3000",
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
    # ---- 1) Save uploaded file temporarily (safe temp name, not user filename) ----
    tmp_dir = Path("data/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_path = tmp_dir / f"upload_{timestamp}.docx"

    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # ---- 2) Extract book title + pages from DOCX ----
    extracted = parse_docx(str(tmp_path))
    book_title = extracted["book_title"]

    # slug can get huge; cap it to reduce Windows path-length issues
    book_slug = slugify(book_title)[:60] or "untitled"

    # unique folder per upload
    book_folder = Path(BASE_DIR) / f"{book_slug}_{timestamp}"

    input_dir = book_folder / "input"
    output_dir = book_folder / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- 3) Store input file permanently (portable filename) ----
    saved_docx_path = input_dir / "original.docx"
    shutil.move(str(tmp_path), str(saved_docx_path))

    # ---- 4) Store extracted pages JSON (output/extracted_pages.json) ----
    extracted_json_path = output_dir / "extracted_pages.json"
    with extracted_json_path.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    # ---- 5) Run LLM to generate scenes page-by-page ----
    scenes = []
    prev_summary = ""

    for page in extracted["pages"]:
        scene = generate_scene(
            book_title=book_title,
            page=page,
            prev_summary=prev_summary
        )
        prev_summary = scene.get("continuity_notes", "")
        scenes.append(scene)

    # ---- 6) Store final book-wise scenes JSON (output/scenes.json) ----
    final_output = {"book_title": book_title, "pages": scenes}

    scenes_json_path = output_dir / "scenes.json"
    with scenes_json_path.open("w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    # ---- 7) Return response ----
    return {
        "book_title": book_title,
        "book_folder": str(book_folder),
        "book_file_id": str(book_folder).split("books/")[-1].split("books\\")[-1],
        "input_file": str(saved_docx_path),
        "extracted_pages_json": str(extracted_json_path),
        "scenes_json": str(scenes_json_path),
        "pages_count": len(scenes),
        "page": scenes
    }



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
    overwrite: bool = False,
    start_page: int = 1,
    end_page: int = 10_000
):
    book_dir = Path("data/books") / book_id
    scenes_path = book_dir / "output" / "scenes.json"

    if not scenes_path.exists():
        raise HTTPException(status_code=404, detail=f"scenes.json not found: {scenes_path}")

    with open(scenes_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    book_title = data["book_title"]
    pages = data["pages"]
    total_pages = len(pages)

    images_dir = book_dir / "images" / slugify(book_title)
    images_dir.mkdir(parents=True, exist_ok=True)

    generated, skipped, failed = [], [], []

    for page in pages:
        page_no = int(page["page_number"])
        if page_no < start_page or page_no > end_page:
            continue

        out_path = images_dir / f"page_{page_no:03d}.png"

        if out_path.exists() and not overwrite:
            skipped.append(str(out_path))
            continue

        try:
            img = generate_image_for_page(
                page=page
                # bailey_ref_path=REF_BAILEY,
                # beau_ref_path=REF_BEAU,
            )
            img.save(out_path)
            generated.append(str(out_path))
        except Exception as e:
            failed.append({"page": page_no, "error": str(e)})

    return {
        "book_id": book_id,
        "book_title": book_title,
        "total_pages": total_pages,
        "images_folder": str(images_dir),
        "generated_count": len(generated),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "failed": failed[:10]
    }


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
        "generated_pages_sample": generated_pages[:15], # just a sample
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
