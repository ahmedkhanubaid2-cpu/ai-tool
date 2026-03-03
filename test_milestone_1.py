import requests
import os
import time

# --- CONFIGURATION ---
BASE_URL = "http://187.77.129.112:8001"
TEST_DOC_PATH = "cep log book.z.docx"

def test_milestone_1_flow():
    print("Starting Test Case for Milestone 1 Architecture Refactor...")
    
    # 1. TEST UPLOAD-DOCX
    print("\n[Step 1] Uploading DOCX & Initializing Book...")
    if not os.path.exists(TEST_DOC_PATH):
        print(f"Error: Test document {TEST_DOC_PATH} not found.")
        return

    try:
        with open(TEST_DOC_PATH, "rb") as f:
            files = {"file": f}
            resp = requests.post(f"{BASE_URL}/v1/upload-docx", files=files)
        
        if resp.status_code != 200:
            print(f"Upload Failed: {resp.status_code} - {resp.text}")
            return
        
        data = resp.json()
        book_id = data.get("book_id")
        pages_count = data.get("pages_count")
        print(f"Upload Successful! Book ID: {book_id}")
        print(f"Pages Extracted: {pages_count}")

        # 2. TEST GET-BOOK-STATUS
        print("\n[Step 2] Checking Initial Book Status...")
        status_resp = requests.get(f"{BASE_URL}/v1/books/{book_id}")
        status_data = status_resp.json()
        
        # Check that generated_scenes is empty (Milestone 1 decouples this)
        if len(status_data.get("generated_scenes", [])) == 0:
            print("Correct: Initial scene list is empty (Architecture decoupled).")
        else:
            print("Warning: Initial scene list is NOT empty.")

        # 3. TEST ATOMIC PAGE GENERATION (PAGE 1)
        print("\n[Step 3] Generating Scene for Page 1...")
        gen_resp = requests.post(f"{BASE_URL}/v1/books/{book_id}/pages/1/generate")
        
        if gen_resp.status_code == 200:
            p1_scene = gen_resp.json()
            print(f"Page 1 Generated! Setting: {p1_scene.get('setting')}")
            p1_continuity = p1_scene.get("continuity_notes", "")
            print(f"Continuity Notes Captured: {p1_continuity[:50]}...")
        else:
            print(f"Page 1 Generation Failed: {gen_resp.status_code} - {gen_resp.text}")
            return

        # 4. TEST ATOMIC PAGE GENERATION (PAGE 2) - Continuity flow
        print("\n[Step 4] Generating Scene for Page 2 (Checking Continuity Flow)...")
        gen_resp_p2 = requests.post(f"{BASE_URL}/v1/books/{book_id}/pages/2/generate")
        
        if gen_resp_p2.status_code == 200:
            p2_scene = gen_resp_p2.json()
            print(f"Page 2 Generated! Mood: {p2_scene.get('mood')}")
        else:
            print(f"Page 2 Generation Failed: {gen_resp_p2.status_code} - {gen_resp_p2.text}")
            return

        # 5. TEST PAGE REGENERATION (PAGE 1)
        print("\n[Step 5] Testing Regeneration Flow (Page 1 Isolation)...")
        regen_resp = requests.post(f"{BASE_URL}/v1/books/{book_id}/pages/1/generate")
        
        if regen_resp.status_code == 200:
            print("Page 1 Regenerated Successfully.")
        else:
            print(f"Regeneration Failed: {regen_resp.status_code} - {regen_resp.text}")

        # 6. FINAL STATUS CHECK
        print("\n[Step 6] Final Book Status Architecture Check...")
        final_status = requests.get(f"{BASE_URL}/v1/books/{book_id}").json()
        generated_count = len(final_status.get("generated_scenes", []))
        
        print(f"Total Generated Scenes: {generated_count}")
        if generated_count == 2:
            print("\nTEST CASE PASSED: Milestone 1 Architecture is solid!")
        else:
            print(f"\nTEST CASE FAILED: Expected 2 scenes in list, but found {generated_count}.")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    test_milestone_1_flow()
