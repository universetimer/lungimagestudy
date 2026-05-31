# -*- coding: utf-8 -*-
"""
Finalize 10 X-ray cases from PPT presentations:
- Copy/mask images from _case_xrays/ to images/case_NN.png
- Mask DICOM corner text (top-left & top-right) for images that need it,
  while preserving the radiographic R/L marker
- Extract findings text per case from the corresponding PPT
- Emit a draft cases.json (operator can refine keywords later)
"""
import sys, io, os, json, shutil, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

PPT_DIR = r"C:/Users/unive/OneDrive/111 유튜버/학생 흉부 사진/20260519 학생"
SRC_DIR = r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/_case_xrays"
DST_DIR = r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/images"
META_PATH = r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/_extracted_cases.json"

os.makedirs(DST_DIR, exist_ok=True)
# Clear old PDF-rendered images
for f in os.listdir(DST_DIR):
    if f.startswith("case_") and f.endswith(".png"):
        os.remove(os.path.join(DST_DIR, f))

# (final_case_id, source_image, mask_corners)
# mask_corners: True if image has DICOM header text in corners
FINAL = [
    # source_id        case_n   mask
    ("hong_1",   "case_01", False),
    ("hong_2",   "case_02", False),
    ("hong_3",   "case_03", False),
    ("seo_1",    "case_04", False),
    ("seo_2",    "case_05", False),
    ("seo_3",    "case_06", False),
    ("lee_1",    "case_07", False),
    ("choi_2",   "case_08", False),
    ("choi_3",   "case_09", False),
    ("yu_2",     "case_10", True),   # has visible DICOM header — mask
]

def find_ext(base):
    for ext in (".jpg", ".jpeg", ".png"):
        p = os.path.join(SRC_DIR, base + ext)
        if os.path.exists(p): return p
    return None

def mask_corners(img):
    """Mask all four corner DICOM text regions completely.
    Preserving R/L radiographic markers is nice-to-have but secondary to
    removing every line that could carry identifiers/metadata."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    # Top-left: 0..18% width × 0..12% height (covers Idx/Im/DigitalDiagnost/R)
    draw.rectangle([0, 0, int(w * 0.20), int(h * 0.12)], fill="black")
    # Top-right: 78..100% × 0..12% (covers hospital name, study date, age/sex)
    draw.rectangle([int(w * 0.78), 0, w, int(h * 0.12)], fill="black")
    # Bottom-left: technical info / scale
    draw.rectangle([0, int(h * 0.92), int(w * 0.22), h], fill="black")
    # Bottom-right: window/level info
    draw.rectangle([int(w * 0.78), int(h * 0.92), w, h], fill="black")
    return img

# Load source metadata (has findings_text per case)
with open(META_PATH, encoding="utf-8") as f:
    meta_list = json.load(f)
meta_by_id = {m["case_id"]: m for m in meta_list}

# Copy & process
out_cases = []
for src_id, case_n, do_mask in FINAL:
    src = find_ext(src_id)
    if not src:
        print(f"[MISS] {src_id}")
        continue
    img = Image.open(src).convert("RGB")
    if do_mask:
        img = mask_corners(img)
    out_path = os.path.join(DST_DIR, f"{case_n}.png")
    img.save(out_path, optimize=True)
    m = meta_by_id.get(src_id, {})
    print(f"[OK]   {case_n}: {src_id} ({img.size[0]}x{img.size[1]}) mask={do_mask}")
    out_cases.append({
        "case_n": case_n,
        "source": src_id,
        "age": m.get("age"),
        "sex": m.get("sex"),
        "cc": m.get("cc"),
        "findings_text": m.get("findings_text", "")
    })

# Print findings text for each case so we can craft answer keys
print("\n" + "=" * 70)
print("FINDINGS TEXT PER CASE (for answer-key crafting):")
print("=" * 70)
for c in out_cases:
    print(f"\n--- {c['case_n']} ({c['age']}/{c['sex']}) CC: {c['cc']} ---")
    if c["findings_text"]:
        # Print first 1500 chars
        print(c["findings_text"][:1500])
    else:
        print("  (no findings text found)")

# Dump for downstream use
with open(r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/_final_cases_meta.json", "w", encoding="utf-8") as f:
    json.dump(out_cases, f, ensure_ascii=False, indent=2)
print(f"\nMeta written. {len(out_cases)} cases ready in images/")
