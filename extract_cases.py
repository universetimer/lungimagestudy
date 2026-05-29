# -*- coding: utf-8 -*-
"""
Extract 10 clean X-ray images from student PDF presentations.

Strategy v2:
- Identify "X-ray content pixels" by intensity: 50 < value < 200
  (excludes pure black slide background AND white text labels)
- Find connected horizontal bands rich in X-ray content
- If multiple panels exist (Normal | Current comparison), separate by
  finding the empty gap column between them and pick the requested side.
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pdfplumber
import numpy as np
from PIL import Image

PDF_DIR = r"C:/Users/unive/OneDrive/111 유튜버/학생 흉부 사진"
OUT_DIR = r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/images"
os.makedirs(OUT_DIR, exist_ok=True)

# (case_id, pdf_filename, page_index_0based, which_panel)
CASES = [
    ("case_01", "3조 배강렬.pdf",   2, "right"),
    ("case_02", "3조 배강렬.pdf",   7, "right"),
    ("case_03", "3조 배강렬.pdf",  11, "right"),
    ("case_04", "김단아.pdf",       2, "right"),
    ("case_05", "김단아.pdf",       7, "right"),
    ("case_06", "김단아.pdf",      12, "right"),
    ("case_07", "김민재.pdf",       3, "biggest"),
    ("case_08", "김민재.pdf",       9, "biggest"),
    ("case_09", "신건우.pdf",       2, "right"),
    ("case_10", "CXR 발표_A반 4조 11번 202200077 이서현.pdf", 2, "right"),
]

CONTENT_LO = 50
CONTENT_HI = 200

def find_runs(mask, min_len, gap_tolerance):
    """Find runs of True in 1D mask, allowing small gaps."""
    runs = []
    in_run = False
    start = 0
    last_true = -gap_tolerance - 1
    for i, v in enumerate(mask):
        if v:
            if not in_run:
                start = i; in_run = True
            last_true = i
        else:
            if in_run and i - last_true > gap_tolerance:
                if last_true - start + 1 >= min_len:
                    runs.append((start, last_true))
                in_run = False
    if in_run and last_true - start + 1 >= min_len:
        runs.append((start, last_true))
    return runs

def find_xray_panel(page_image, which="right"):
    arr = np.array(page_image.convert("L"))
    h, w = arr.shape

    # Mask of "X-ray content" pixels: medium grayscale only
    content = (arr > CONTENT_LO) & (arr < CONTENT_HI)

    # Column profile: fraction of column that is X-ray content
    col_pct = content.mean(axis=0)
    col_rich = col_pct > 0.10  # at least 10% of column is X-ray gray

    col_runs = find_runs(col_rich,
                         min_len=int(w * 0.10),
                         gap_tolerance=int(w * 0.02))
    if not col_runs:
        return None

    if which == "right":
        x1, x2 = col_runs[-1]
    elif which == "left":
        x1, x2 = col_runs[0]
    else:  # biggest / only
        x1, x2 = max(col_runs, key=lambda r: r[1] - r[0])

    # Row profile within selected columns
    strip = content[:, x1:x2 + 1]
    row_pct = strip.mean(axis=1)
    row_rich = row_pct > 0.10
    row_runs = find_runs(row_rich,
                         min_len=int(h * 0.10),
                         gap_tolerance=int(h * 0.02))
    if not row_runs:
        y1, y2 = 0, h - 1
    else:
        y1, y2 = max(row_runs, key=lambda r: r[1] - r[0])

    # Shrink slightly to ensure no text bleed at edges
    pad = 6
    return (max(0, x1 + pad), max(0, y1 + pad),
            min(w - 1, x2 - pad), min(h - 1, y2 - pad))

def extract_one(case_id, pdf_name, page_idx, which):
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        print(f"[MISS] {case_id}: {pdf_name} not found"); return False
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx >= len(pdf.pages):
            print(f"[MISS] {case_id}: page {page_idx} out of range"); return False
        page_img = pdf.pages[page_idx].to_image(resolution=220).original

    box = find_xray_panel(page_img, which=which)
    if box is None:
        print(f"[FAIL] {case_id}: no panel detected")
        return False

    cropped = page_img.crop(box)
    out_path = os.path.join(OUT_DIR, f"{case_id}.png")
    cropped.save(out_path, optimize=True)
    print(f"[OK]   {case_id}: p{page_idx+1} {which} → {cropped.size[0]}x{cropped.size[1]}")
    return True

ok = 0
for case_id, pdf_name, page_idx, which in CASES:
    if extract_one(case_id, pdf_name, page_idx, which):
        ok += 1
print(f"\nDone: {ok}/{len(CASES)}")
