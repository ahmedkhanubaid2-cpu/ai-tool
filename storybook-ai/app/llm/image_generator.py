import os
from typing import Dict, Optional
from PIL import Image
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")

if not GEMINI_API_KEY:
    raise ValueError("Set GEMINI_API_KEY in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

# Put refs here (same as your pipeline)
# REF_BAILEY = "data/brand/reference/bailey.png"
# REF_BEAU = "data/brand/reference/beau.png"
REFS = {
    "Bailey": [
        "data/brand/reference/bailey.png"         # identity (must be first)
        
    ],
    "Beau": [
        "data/brand/reference/beau.png"    
    ],
}

def _open_ref(path: str) -> Optional[Image.Image]:
    if not path or not os.path.exists(path):
        return None
    img = Image.open(path)
    # Force consistent mode (VERY important)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img
def _open_refs(paths):
    imgs = []
    for p in paths:
        img = _open_ref(p)
        if img:
            imgs.append(img)
    return imgs

def _combine_refs_side_by_side(bailey: Image.Image, beau: Image.Image) -> Image.Image:
    """
    Stronger identity anchoring: one combined reference image (no text labels).
    This often reduces drift vs sending two separate images.
    """
    # Normalize heights
    target_h = 768
    def resize_keep_aspect(im: Image.Image, h: int) -> Image.Image:
        w = int(im.width * (h / im.height))
        return im.resize((w, h))

    b1 = resize_keep_aspect(bailey, target_h)
    b2 = resize_keep_aspect(beau, target_h)

    gap = 48
    canvas = Image.new("RGB", (b1.width + gap + b2.width, target_h), (255, 255, 255))
    canvas.paste(b1, (0, 0))
    canvas.paste(b2, (b1.width + gap, 0))
    return canvas

def build_actions_block(characters: list) -> str:
    """
    Builds a clean, visual-only description of what is happening in the scene.
    One clear moment, no dialogue.
    """
    if not characters:
        return "- No character action (environment-focused scene)."

    action_lines = []

    for ch in characters:
        name = ch.get("name", "").strip()
        actions = ch.get("actions", [])

        if actions:
            # take only the first visual action
            primary_action = actions[0]
            action_lines.append(f"- {name} is {primary_action}.")
        else:
            action_lines.append(f"- {name} is present in the scene.")

    return "\n".join(action_lines)
# -------------------------
# YOUR EXACT PROMPT (unchanged, copy-pasted)
# -------------------------
def build_page_prompt(page: dict) -> str:
    page_no = page.get("page_number")
    page_text = page.get("page_text", "")
    setting = page.get("setting", "")
    time_of_day = page.get("time_of_day", "")
    mood = page.get("mood", "")
    characters = page.get("characters", [])
    props = page.get("props", [])
    composition = page.get("composition_notes", "")
    continuity = page.get("continuity_notes", "")

    char_lines = []
    for ch in characters:
        name = ch.get("name", "")
        actions = ", ".join(ch.get("actions", []))
        emotions = ", ".join(ch.get("emotions", []))
        char_lines.append(f"- {name}: actions({actions}); emotions({emotions})")

    chars_block = "\n".join(char_lines) if char_lines else "- (no characters listed)"
    actions_block = build_actions_block(characters)
    print(actions_block)
    props_block = ", ".join(props) if props else "(none)"

    # prompt = f"""
    prompt = f"""

You are illustrating a children’s storybook page.

ABSOLUTE PRIORITY — IDENTITY LOCK (NON-NEGOTIABLE):
The character descriptions below define the TRUE and FINAL designs.
Bailey and Beau MUST remain visually identical across every page.
Do NOT redesign, reinterpret, stylize, age, or alter proportions.
If any detail is unclear, DEFAULT to the reference description, not creativity.

━━━━━━━━━━━━━━━━━━━━━━
IDENTITY LOCK — BAILEY (FEMALE)
━━━━━━━━━━━━━━━━━━━━━━
• Gender: Girl
• Age appearance: ~9 years (child, not toddler, not teen)
• Height: slightly taller than Beau
• Build: slim child proportions, natural posture

FACE & SKIN
• Face shape: soft, rounded, gentle
• Expression: calm, thoughtful, kind
• Eyes: large, soft, warm, curious
• Skin tone: light with warmth (never pale, never dark)
• Cheeks: soft rosy blush (consistent)

━━━━━━━━━━━━━━━━━━━━━━
HAIR (CRITICAL — MUST NEVER CHANGE)
━━━━━━━━━━━━━━━━━━━━━━
• Color: light brown
• Texture: soft, natural (not styled, not glossy)
• Style: EXACTLY two small buns, one on each side of head

SIGNATURE DETAIL — SINGLE RINGLET LOCK (ABSOLUTE, MUST PASS)

LEFT SIDE (ONLY PLACE WHERE LOOSE HAIR IS ALLOWED):

Bailey MUST ALWAYS have EXACTLY ONE loose curl (ringlet) falling forward on the LEFT side of her face ONLY.

The ringlet MUST be clearly visible and must fall in front of the LEFT cheek (front-facing curl).

RIGHT SIDE (ZERO TOLERANCE CLEAN SIDE):

The RIGHT side of Bailey’s face MUST be 100% clean and fully tied back.

The RIGHT cheek, RIGHT jawline, and RIGHT forehead edge must be fully unobstructed.

On the RIGHT side there must be ABSOLUTELY NO:

curls

strands

ringlets

loose hair

bangs

flyaways

wisps

baby hair

side locks

mirrored curl

symmetric curl

any hair falling forward

ANTI-SYMMETRY RULE (MOST IMPORTANT):

NEVER mirror the curl.

NEVER generate any curl/strand on the RIGHT side.

Bailey MUST NOT have symmetrical hair framing on both sides.

If any loose hair is visible on the RIGHT side → FAIL.

VALIDATION RULE:

If Bailey has ANY loose strand/curl on the RIGHT side OR the curl appears on both sides → the output is INVALID and MUST be regenerated.

━━━━━━━━━━━━━━━━━━━━━━


CLOTHING (UNIFORM — MUST NEVER CHANGE)
━━━━━━━━━━━━━━━━━━━━━━
• Top: purple sweatshirt (brand purple #764F84)
• Graphic: simple panda graphic (same size, same position every page)
• Bottom: yellow leggings (brand yellow #F0C75E)
• Shoes: white sneakers with purple accents
• Clothing feel: simple, comfortable, age-appropriate
• NO fashion changes, NO accessories
━━━━━━━━━━━━━━━━━━━━━━
IDENTITY LOCK — BEAU (MALE)
━━━━━━━━━━━━━━━━━━━━━━
• Gender: Boy
• Age appearance: ~7 years
• Height: clearly shorter than Bailey
• Build: small, active child proportions

FACE & SKIN
• Face: friendly, expressive, animated
• Eyes: bright and lively
• Skin tone: light and warm (match Bailey’s warmth)

HAIR (CRITICAL — MUST NEVER CHANGE)
• Color: brown
• Length: short
• Style: slightly tousled, natural
• NEVER spiky, NEVER styled, NEVER messy

CLOTHING (UNIFORM — MUST NEVER CHANGE)
• Top: dark blue shirt (#3D3B62)
• Bottom: khaki shorts
• Shoes: brown and white sneakers or booties
• Clothing feel: practical, playful, child-appropriate

━━━━━━━━━━━━━━━━━━━━━━
SIBLING RELATIONSHIP (IMPORTANT)
━━━━━━━━━━━━━━━━━━━━━━
• Bailey: calmer, thoughtful, observant
• Beau: energetic, curious, hands-on
• Their outfits coordinate in color but do NOT match
• They must always look like the SAME siblings on every page

━━━━━━━━━━━━━━━━━━━━━━
STRICT NO-TEXT POLICY (ZERO TOLERANCE)
━━━━━━━━━━━━━━━━━━━━━━
• NO text of any kind anywhere in the image
• NO letters, words, numbers, symbols
• NO speech bubbles, captions, signs, labels
• NO book titles, notes, maps, posters with writing
• NO watermarks, logos, UI, page numbers
• All books, papers, signs must be BLANK surfaces
• Avoid gibberish or fake writing entirely

━━━━━━━━━━━━━━━━━━━━━━
STYLE LOCK (CONSISTENT)
━━━━━━━━━━━━━━━━━━━━━━
• Soft watercolor storybook illustration
• Gentle outlines, clean shapes
• Warm lighting
• Pastel colors (avoid neon)
• Flat-to-soft shading (no 3D, no realism, no anime)
• Child-friendly proportions
• Clear focal subject, uncluttered composition

━━━━━━━━━━━━━━━━━━━━━━
SCENE DETAILS (USE VISUALS ONLY)
━━━━━━━━━━━━━━━━━━━━━━
Setting:
{setting}

Time of day:
{time_of_day}

Mood:
{mood}

Characters present:
{chars_block}

Actions (visual only, no dialogue):
{actions_block}

Props (visual objects only — all blank, no text):
{props_block}

Composition:
{composition}

Continuity:
{continuity}

━━━━━━━━━━━━━━━━━━━━━━
FINAL OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━
• One single illustration
• Bailey and Beau must match the identity lock EXACTLY
• Bailey’s LEFT-SIDE ringlet curl MUST be clearly visible (mandatory identity feature)
• No text anywhere in the image
• If forced to choose: character accuracy > scene creativity



""".strip()


    return prompt


# def generate_image_for_page(page: Dict) -> Image.Image:
#     prompt = build_page_prompt(page)

#     bailey_img = _open_ref(REF_BAILEY)
#     beau_img = _open_ref(REF_BEAU)

#     contents = [prompt]

#     # Best: one combined anchor (stronger identity lock)
#     if bailey_img and beau_img:
#         anchor = _combine_refs_side_by_side(bailey_img, beau_img)
#         contents.append(anchor)
#     else:
#         # fallback: whatever exists
#         if bailey_img:
#             contents.append(bailey_img)
#         if beau_img:
#             contents.append(beau_img)

#     response = client.models.generate_content(
#         model=GEMINI_IMAGE_MODEL,
#         contents=contents,
#     )

#     for part in getattr(response, "parts", []) or []:
#         if getattr(part, "inline_data", None):
#             return part.as_image()

#     raise RuntimeError("No image returned (Gemini responded text-only).")
# def generate_image_for_page(page: Dict) -> Image.Image:
#     prompt = build_page_prompt(page)

#     bailey_img = _open_ref(REF_BAILEY)
#     beau_img = _open_ref(REF_BEAU)

#     contents = [prompt]

#     # Best: one combined anchor (stronger identity lock)
#         # if bailey_img and beau_img:
#         #     anchor = _combine_refs_side_by_side(bailey_img, beau_img)
#         #     contents.append(anchor)

#     if bailey_img and beau_img:
#         anchor = _combine_refs_side_by_side(bailey_img, beau_img)
#         contents.append(anchor)
#     # ✅ ADD THESE LINES (easy fix)
#     for p in REF_BAILEY:
#         img = _open_ref(p)
#         if img:
#             contents.append(img)

#     for p in REF_BEAU:
#         img = _open_ref(p)
#         if img:
#             contents.append(img)

#     else:
#         # fallback: whatever exists
#         if bailey_img:
#             contents.append(bailey_img)
#         if beau_img:
#             contents.append(beau_img)

#     response = client.models.generate_content(
#         model=GEMINI_IMAGE_MODEL,
#         contents=contents,
#     )

#     for part in getattr(response, "parts", []) or []:
#         if getattr(part, "inline_data", None):
#             return part.as_image()

#     raise RuntimeError("No image returned (Gemini responded text-only).")

def generate_image_for_page(page: Dict) -> Image.Image:
    prompt = build_page_prompt(page)

    contents = [prompt]

    # Bailey refs
    bailey_imgs = _open_refs(REFS["Bailey"])
    if bailey_imgs:
        contents.append("Reference images: Bailey (female child). Use these to match face, hair buns, outfit colors exactly.")
        contents.extend(bailey_imgs)

    # Beau refs
    beau_imgs = _open_refs(REFS["Beau"])
    if beau_imgs:
        contents.append("Reference images: Beau (male child). Use these to match face, hair, outfit colors exactly.")
        contents.extend(beau_imgs)

    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=contents,
    )

    for part in getattr(response, "parts", []) or []:
        if getattr(part, "inline_data", None):
            return part.as_image()

    raise RuntimeError("No image returned (Gemini responded text-only).")