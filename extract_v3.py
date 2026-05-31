# -*- coding: utf-8 -*-
"""
Iteration v3: re-extract 10 X-ray cases from the PDFs in the user's
"흉부 사진 공부 앱/학생 들 사진 판독" folder, output to images/v3/.

Method: render each chosen PDF page at 220 DPI, find the X-ray content
region (mid-gray pixels), crop to it. This drops patient text overlays
that appear in the white-background slide template.
"""
import sys, io, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pdfplumber
import numpy as np
from PIL import Image

PDF_DIR = r"C:/Users/unive/OneDrive/111 Claude/흉부 사진 공부 앱/학생 들 사진 판독"
OUT_DIR = r"C:/Users/unive/OneDrive/111 Claude/병동 가이드 라인/cxr-grading-app/images/v3"

# Clean output dir
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)
os.makedirs(OUT_DIR)

# Selected 10 cases from the PDFs (case_id, pdf, page_index_0based, which_panel)
# which: "right" = current/abnormal X-ray on comparison page;
#        "biggest" = single dominant X-ray on the page
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

def runs(mask, min_len, gap):
    out, in_run, start, last = [], False, 0, -gap - 1
    for i, v in enumerate(mask):
        if v:
            if not in_run: start, in_run = i, True
            last = i
        else:
            if in_run and i - last > gap:
                if last - start + 1 >= min_len: out.append((start, last))
                in_run = False
    if in_run and last - start + 1 >= min_len: out.append((start, last))
    return out

def crop_xray(page_image, which="right"):
    arr = np.array(page_image.convert("L"))
    h, w = arr.shape
    content = (arr > CONTENT_LO) & (arr < CONTENT_HI)
    col_rich = content.mean(axis=0) > 0.10
    col_runs = runs(col_rich, int(w * 0.10), int(w * 0.02))
    if not col_runs: return None
    if which == "right":   x1, x2 = col_runs[-1]
    elif which == "left":  x1, x2 = col_runs[0]
    else:                  x1, x2 = max(col_runs, key=lambda r: r[1] - r[0])
    strip = content[:, x1:x2 + 1]
    row_runs = runs(strip.mean(axis=1) > 0.10, int(h * 0.10), int(h * 0.02))
    if not row_runs: return None
    y1, y2 = max(row_runs, key=lambda r: r[1] - r[0])
    pad = 6
    return (max(0, x1 + pad), max(0, y1 + pad),
            min(w - 1, x2 - pad), min(h - 1, y2 - pad))

ok = 0
for case_id, pdf_name, page_idx, which in CASES:
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        print(f"[MISS] {case_id}: {pdf_name}"); continue
    with pdfplumber.open(pdf_path) as pdf:
        if page_idx >= len(pdf.pages):
            print(f"[MISS] {case_id}: page {page_idx}"); continue
        page_img = pdf.pages[page_idx].to_image(resolution=220).original
    box = crop_xray(page_img, which=which)
    if box is None:
        print(f"[FAIL] {case_id}: no panel detected"); continue
    cropped = page_img.crop(box)
    out_path = os.path.join(OUT_DIR, f"{case_id}.png")
    cropped.save(out_path, optimize=True)
    print(f"[OK]   {case_id}: {pdf_name} p{page_idx+1} {which} -> {cropped.size[0]}x{cropped.size[1]}")
    ok += 1
print(f"\n{ok}/{len(CASES)} cases written to {OUT_DIR}")
